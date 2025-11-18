from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone

from service_accounts.models import ServiceAccount


class Command(BaseCommand):
    help = "Send alerts for service accounts with expired or expiring passwords."

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Window (in days) to flag upcoming expirations.'
        )
        parser.add_argument(
            '--recipient',
            action='append',
            dest='recipients',
            default=[],
            help='Email recipient; repeat for multiples. Defaults to settings.ADMINS.'
        )

    def handle(self, *args, **options):
        days = options['days']
        now = timezone.now()
        window = now + timedelta(days=days)

        expired = ServiceAccount.objects.filter(
            is_active=True,
            password_expires_on__isnull=False,
            password_expires_on__lt=now,
        ).order_by('system__name', 'account_name')

        expiring = ServiceAccount.objects.filter(
            is_active=True,
            password_expires_on__gte=now,
            password_expires_on__lte=window,
        ).order_by('system__name', 'account_name')

        if not expired.exists() and not expiring.exists():
            self.stdout.write(self.style.SUCCESS("No expired or expiring service accounts."))
            return

        body_lines = [
            f"Service Account Password Alerts (window: next {days} days)",
            "",
        ]

        if expired.exists():
            body_lines.append("EXPIRED PASSWORDS:")
            for account in expired:
                body_lines.append(
                    f"- {account.account_name} ({account.system.name}) "
                    f"owner: {account.owner or 'Unassigned'} "
                    f"expired {account.password_expires_on:%Y-%m-%d}"
                )
            body_lines.append("")

        if expiring.exists():
            body_lines.append("EXPIRING SOON:")
            for account in expiring:
                body_lines.append(
                    f"- {account.account_name} ({account.system.name}) "
                    f"owner: {account.owner or 'Unassigned'} "
                    f"expires {account.password_expires_on:%Y-%m-%d}"
                )

        message = "\n".join(body_lines)

        recipients = options['recipients']
        if not recipients:
            recipients = [email for _, email in getattr(settings, 'ADMINS', [])]

        if recipients:
            send_mail(
                subject="[UAM] Service Account Password Alerts",
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@user-access-management.local'),
                recipient_list=recipients,
            )
            self.stdout.write(self.style.SUCCESS(f"Alert sent to: {', '.join(recipients)}"))
        else:
            self.stdout.write(self.style.WARNING("No recipients configured; printing message instead."))
            self.stdout.write(message)


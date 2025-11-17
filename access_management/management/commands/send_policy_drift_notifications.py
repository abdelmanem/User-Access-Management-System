import csv
from io import StringIO

from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.utils import timezone

from access_management.reporting import build_policy_drift_snapshot, generate_policy_drift_rows


class Command(BaseCommand):
    help = "Send Policy Drift Monitoring summary emails (supports scheduling via cron/task scheduler)."

    def add_arguments(self, parser):
        parser.add_argument('--system', type=int, help='Filter to a specific system ID')
        parser.add_argument('--department', type=int, help='Filter to a specific department ID')
        parser.add_argument(
            '--status-scope',
            choices=['active', 'all'],
            default='active',
            help='Limit to active/approved/suspended records or all records'
        )
        parser.add_argument('--stale-threshold', type=int, default=90, help='Review window in days (default 90)')
        parser.add_argument(
            '--recipient',
            action='append',
            dest='recipients',
            help='Override notification recipients (can be provided multiple times)'
        )
        parser.add_argument('--dry-run', action='store_true', help='Print the summary instead of sending email')

    def handle(self, *args, **options):
        snapshot = build_policy_drift_snapshot(
            system_id=options.get('system'),
            department_id=options.get('department'),
            status_scope=options['status_scope'],
            stale_threshold_days=options['stale_threshold'],
        )
        rows = list(generate_policy_drift_rows(snapshot))
        summary = snapshot['issue_summary']

        summary_text = (
            f"Policy Drift Snapshot ({timezone.localtime(snapshot['now']).strftime('%Y-%m-%d %H:%M')})\n"
            f"- Missing external usernames: {summary['missing_usernames']}\n"
            f"- Stale reviews: {summary['stale_reviews']}\n"
            f"- Overlapping usernames: {summary['overlapping_usernames']}\n"
            f"- Assignments scanned: {summary['total_assignments']}\n"
            f"- Review threshold: {snapshot['stale_threshold_days']} days\n"
        )

        if options['dry_run']:
            self.stdout.write(self.style.NOTICE(summary_text))
            self.stdout.write(self.style.NOTICE("Top findings:"))
            for row in rows[:10]:
                self.stdout.write(
                    f"* {row['issue_type']} | {row['user_name']} ({row['user_username']}) "
                    f"-> {row['system_name']} ({row['system_code']}) | {row['detail']}"
                )
            return

        recipients = options.get('recipients') or getattr(settings, 'POLICY_DRIFT_NOTIFICATION_RECIPIENTS', [])
        if not recipients:
            self.stdout.write(self.style.WARNING('No recipients configured; set POLICY_DRIFT_NOTIFICATION_RECIPIENTS or pass --recipient.'))
            return

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        subject = f"Policy Drift Monitoring Snapshot ({timezone.localtime(snapshot['now']).date()})"
        email = EmailMessage(
            subject=subject,
            body=summary_text,
            from_email=from_email,
            to=recipients,
        )
        csv_attachment = self._build_csv_attachment(rows)
        email.attach('policy_drift_snapshot.csv', csv_attachment, 'text/csv')
        email.send(fail_silently=False)

        self.stdout.write(self.style.SUCCESS(f"Policy drift summary sent to {', '.join(recipients)}"))

    @staticmethod
    def _build_csv_attachment(rows):
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Issue Type",
            "User",
            "User Login",
            "Department",
            "System",
            "System Code",
            "External Username",
            "Status",
            "Last Review",
            "Next Review",
            "Detail",
            "Assignment ID",
        ])
        for row in rows:
            writer.writerow([
                row["issue_type"],
                row["user_name"],
                row["user_username"],
                row["department"],
                row["system_name"],
                row["system_code"],
                row["external_username"],
                row["status"],
                row["last_review"],
                row["next_review"],
                row["detail"],
                row["assignment_id"],
            ])
        return output.getvalue().encode('utf-8-sig')


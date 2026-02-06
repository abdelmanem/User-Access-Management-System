"""
Management command to process pending change requests automatically.

Usage:
    python manage.py process_changes [--auto-complete] [--days N]
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from change_management.models import AccountChangeRequest
from systems.models import System
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending change requests - approve, reject, or complete'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list-pending',
            action='store_true',
            help='List pending change requests',
        )
        
        parser.add_argument(
            '--approve-all',
            action='store_true',
            help='Approve all pending requests (use with caution)',
        )
        
        parser.add_argument(
            '--complete-old',
            type=int,
            metavar='DAYS',
            help='Mark approved changes as completed if older than N days',
        )
        
        parser.add_argument(
            '--system',
            type=str,
            metavar='SYSTEM_CODE',
            help='Filter by system code',
        )
        
        parser.add_argument(
            '--status',
            type=str,
            metavar='STATUS',
            help='Filter by status (Pending, Approved, Completed, Rejected)',
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        try:
            if options['list_pending']:
                self.list_pending_changes(options)
            
            elif options['approve_all']:
                self.approve_all_pending(options)
            
            elif options['complete_old']:
                self.complete_old_approved(options['complete_old'], options)
            
            else:
                self.print_statistics()
        
        except Exception as e:
            logger.error(f"Error in process_changes command: {str(e)}")
            raise CommandError(str(e))

    def list_pending_changes(self, options):
        """List all pending change requests."""
        queryset = AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_PENDING
        ).select_related('user', 'system', 'requested_by')
        
        if options.get('system'):
            queryset = queryset.filter(system__code=options['system'])
        
        if not queryset.exists():
            self.stdout.write(self.style.SUCCESS('No pending changes'))
            return
        
        self.stdout.write(self.style.WARNING(f'\nPending Change Requests ({queryset.count()}):'))
        self.stdout.write('-' * 100)
        
        for change in queryset:
            user_str = f"{change.user.get_full_name()} ({change.user.employee_id})" if change.user else "—"
            self.stdout.write(
                f'ID: {change.id:5d} | Type: {change.change_type:8s} | User: {user_str:40s} | '
                f'System: {change.system.name:25s} | Created: {change.created_at.strftime("%Y-%m-%d %H:%M")}'
            )

    def approve_all_pending(self, options):
        """Approve all pending change requests."""
        queryset = AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_PENDING,
            system_owner_approved=False
        )
        
        if options.get('system'):
            queryset = queryset.filter(system__code=options['system'])
        
        count = queryset.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No pending changes to approve'))
            return
        
        if options.get('dry_run'):
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would approve {count} changes'))
            for change in queryset[:5]:
                user_str = f"{change.user.get_full_name()}" if change.user else "—"
                self.stdout.write(f'  - {change.system.name} for {user_str}')
            if count > 5:
                self.stdout.write(f'  ... and {count - 5} more')
            return
        
        # Ask for confirmation
        confirm = input(f'\n⚠️  Approve ALL {count} pending changes? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR('Cancelled'))
            return
        
        updated = 0
        for change in queryset:
            change.status = AccountChangeRequest.STATUS_APPROVED
            change.system_owner_approved = True
            change.system_owner_approval_date = timezone.now()
            change.system_owner_approval_notes = "Approved via management command"
            change.save()
            updated += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Approved {updated} changes'))
        logger.info(f"Approved {updated} changes via management command")

    def complete_old_approved(self, days, options):
        """Mark old approved changes as completed."""
        cutoff_date = timezone.now() - timedelta(days=days)
        
        queryset = AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_APPROVED,
            system_owner_approval_date__lt=cutoff_date,
            completed_in_external_system=False
        )
        
        if options.get('system'):
            queryset = queryset.filter(system__code=options['system'])
        
        count = queryset.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'No approved changes older than {days} days'
                )
            )
            return
        
        if options.get('dry_run'):
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would mark {count} changes as completed'
                )
            )
            for change in queryset[:5]:
                user_str = f"{change.user.get_full_name()}" if change.user else "—"
                days_old = (timezone.now() - change.system_owner_approval_date).days
                self.stdout.write(
                    f'  - {change.system.name} for {user_str} (approved {days_old} days ago)'
                )
            if count > 5:
                self.stdout.write(f'  ... and {count - 5} more')
            return
        
        confirm = input(f'\n⚠️  Mark ALL {count} changes as completed? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.ERROR('Cancelled'))
            return
        
        updated = 0
        for change in queryset:
            change.status = AccountChangeRequest.STATUS_COMPLETED
            change.completed_in_external_system = True
            change.completed_date = timezone.now()
            change.save()
            updated += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Completed {updated} changes'))
        logger.info(f"Completed {updated} changes via management command")

    def print_statistics(self):
        """Print change management statistics."""
        total = AccountChangeRequest.objects.count()
        pending = AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_PENDING
        ).count()
        approved = AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_APPROVED
        ).count()
        completed = AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_COMPLETED
        ).count()
        rejected = AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_REJECTED
        ).count()
        
        self.stdout.write(self.style.SUCCESS('\n📊 Change Management Statistics:\n'))
        self.stdout.write(f'  Total Requests:     {total}')
        self.stdout.write(self.style.WARNING(f'  Pending:            {pending}'))
        self.stdout.write(self.style.SUCCESS(f'  Approved:           {approved}'))
        self.stdout.write(self.style.SUCCESS(f'  Completed:          {completed}'))
        self.stdout.write(self.style.ERROR(f'  Rejected:           {rejected}'))
        self.stdout.write('')

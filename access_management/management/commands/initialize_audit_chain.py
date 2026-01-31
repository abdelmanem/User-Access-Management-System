"""
Management command to initialize the audit event log chain anchor.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from access_management.models import AuditEventLog


class Command(BaseCommand):
    help = 'Initialize audit chain with anchor event (call once at deployment)'

    def handle(self, *args, **options):
        # Check if chain already initialized
        existing = AuditEventLog.objects.filter(event_type='AuditChainInitialized').exists()
        if existing:
            self.stdout.write(self.style.WARNING('Audit chain already initialized.'))
            return
        
        # Create anchor event with no previous_event_hash
        anchor = AuditEventLog.objects.create(
            event_type='AuditChainInitialized',
            event_data={'init_time': timezone.now().isoformat()},
            previous_event_hash=None,
            is_finalized=True
        )
        
        self.stdout.write(self.style.SUCCESS(f'✓ Audit chain initialized with anchor event {anchor.pk}'))
        self.stdout.write(f"  Hash: {anchor.event_hash}")
        self.stdout.write(f"  Signature: {anchor.signature or 'N/A'}")

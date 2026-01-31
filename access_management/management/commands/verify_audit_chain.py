"""
Management command to verify the audit event log chain integrity.
"""

from django.core.management.base import BaseCommand
from access_management.models import AuditEventLog


class Command(BaseCommand):
    help = 'Verify audit chain integrity; detect tampering'

    def add_arguments(self, parser):
        parser.add_argument(
            '--repair',
            action='store_true',
            help='Attempt to repair chain (recompute hashes)',
        )

    def handle(self, *args, **options):
        events = AuditEventLog.objects.all().order_by('created_at')
        
        if not events.exists():
            self.stdout.write(self.style.WARNING('No audit events found.'))
            return
        
        tampered = []
        repaired = []
        
        for event in events:
            if not event.verify_integrity():
                tampered.append(event.pk)
                self.stdout.write(self.style.ERROR(f'✗ Event {event.pk} integrity FAILED'))
                
                if options.get('repair'):
                    try:
                        event.save()  # Recompute hash
                        repaired.append(event.pk)
                        self.stdout.write(self.style.SUCCESS(f'  → Repaired event {event.pk}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'  → Repair failed: {e}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Event {event.pk} OK'))
        
        self.stdout.write('\n' + '='*60)
        if tampered:
            self.stdout.write(self.style.ERROR(f'TAMPERING DETECTED: {len(tampered)} events failed integrity check'))
            self.stdout.write(f'Failed events: {tampered}')
        else:
            self.stdout.write(self.style.SUCCESS('✓ All events verified successfully'))
        
        if repaired:
            self.stdout.write(self.style.SUCCESS(f'✓ Repaired {len(repaired)} events'))

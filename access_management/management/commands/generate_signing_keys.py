"""
Management command to generate signing keys for audit logs and attestations.
"""

import os
import secrets
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Generate 256-bit signing keys for audit logs and attestations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--env-file',
            type=str,
            default='.env.production',
            help='Environment file to write keys to (default: .env.production)',
        )

    def handle(self, *args, **options):
        env_file = options['env_file']
        
        # Generate keys
        audit_key = secrets.token_hex(32)  # 64 chars = 256 bits
        attestation_key = secrets.token_hex(32)
        
        self.stdout.write(self.style.SUCCESS('Generated signing keys:'))
        self.stdout.write(f"AUDIT_LOG_SIGNING_KEY={audit_key}")
        self.stdout.write(f"ATTESTATION_SIGNING_KEY={attestation_key}")
        
        # Optionally write to .env file
        if os.path.exists(env_file):
            self.stdout.write(self.style.WARNING(f'\nFile {env_file} already exists.'))
            response = input(f'Append keys to {env_file}? (y/n): ')
            if response.lower() == 'y':
                with open(env_file, 'a') as f:
                    f.write(f'\nAUDIT_LOG_SIGNING_KEY={audit_key}\n')
                    f.write(f'ATTESTATION_SIGNING_KEY={attestation_key}\n')
                self.stdout.write(self.style.SUCCESS(f'Keys appended to {env_file}'))
        else:
            with open(env_file, 'w') as f:
                f.write(f'AUDIT_LOG_SIGNING_KEY={audit_key}\n')
                f.write(f'ATTESTATION_SIGNING_KEY={attestation_key}\n')
            self.stdout.write(self.style.SUCCESS(f'Keys written to {env_file}'))
        
        self.stdout.write(self.style.WARNING('\n⚠️  IMPORTANT: Protect these keys! Store in secure location.'))

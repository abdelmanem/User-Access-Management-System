#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from accounts.models import CustomUser
from systems.models import System
from change_management.models import AccountChangeRequest

# Get or create test data
user = CustomUser.objects.first()
system = System.objects.first()
requester = CustomUser.objects.last()

if user and system and requester:
    cr = AccountChangeRequest.objects.create(
        change_type='Create',
        user=user,
        system=system,
        requested_by=requester,
        business_justification='Test change request for system access',
        status='Pending',
    )
    print(f"✓ Created change request: ID={cr.pk}, Status={cr.status}")
else:
    print("✗ Not enough users or systems in database")
    if not user:
        print("  - No users found")
    if not system:
        print("  - No systems found")

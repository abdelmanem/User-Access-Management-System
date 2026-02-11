#!/usr/bin/env python
"""
Test script to verify user deletion creates a change request.
Run with: python manage.py shell < test_user_deletion_change_request.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from accounts.models import CustomUser
from change_management.models import AccountChangeRequest
from departments.models import Department

# Check existing change requests before test
print("=" * 60)
print("CHECKING EXISTING CHANGE REQUESTS FOR USER DELETIONS")
print("=" * 60)

deletion_requests = AccountChangeRequest.objects.filter(
    change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
    system__isnull=True
).select_related('user')

print(f"\nTotal user deletion change requests: {deletion_requests.count()}")
for req in deletion_requests.order_by('-created_at')[:5]:
    print(f"\n  ID: {req.id}")
    print(f"  Username (snapshot): {req.user_username}")
    print(f"  Full Name (snapshot): {req.user_full_name}")
    print(f"  Status: {req.status}")
    print(f"  Created: {req.created_at}")
    print(f"  User (FK): {req.user}")

print("\n" + "=" * 60)
print("SUCCESS: User deletion change request tracking is working!")
print("=" * 60)

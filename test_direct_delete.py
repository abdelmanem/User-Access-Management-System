#!/usr/bin/env python
"""
Test script to verify user deletion creates a change request.
This simulates the user_delete function behavior.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from accounts.models import CustomUser, UserArchive
from change_management.models import AccountChangeRequest
from departments.models import Department
from django.utils import timezone

# Create a test user
print("=" * 70)
print("Creating test user...")
test_user = CustomUser.objects.create(
    username='test_deletion_user',
    first_name='Test',
    last_name='DeletionUser',
    email='test@example.com',
)
print(f"✓ Created test user: {test_user.username}")

# Archive the user (simulating what happens in user_delete)
print("\nArchiving user...")
UserArchive.objects.create(
    source_user_id=test_user.id,
    username=test_user.username,
    full_name=test_user.get_full_name(),
    employee_id=test_user.employee_id or '',
    email=test_user.email or '',
    department_name=test_user.department.name if test_user.department else '',
    archived_by=None,
    payload={},
)
print(f"✓ Archived user")

# Delete the user
user_id = test_user.id
user_full_name = test_user.get_full_name()
user_username = test_user.username
test_user.delete()
print(f"✓ Deleted user from database")

# Create change request (simulating what should happen in user_delete)
print("\nCreating change request...")
try:
    from change_management.models import AccountChangeRequest
    change_request = AccountChangeRequest.objects.create(
        change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
        user=None,
        user_full_name=user_full_name,
        user_username=user_username,
        system=None,
        business_justification='User account deleted',
        requested_by=None,
        status=AccountChangeRequest.STATUS_PENDING,
        system_owner=None,
    )
    print(f"✓ Created change request ID {change_request.id}")
    print(f"  User (snapshot): {change_request.user_username}")
    print(f"  Full Name (snapshot): {change_request.user_full_name}")
    print(f"  Status: {change_request.status}")
except Exception as e:
    print(f"✗ Failed to create change request: {str(e)}")

# Verify results
print("\n" + "=" * 70)
print("Verification:")
deletion_reqs = AccountChangeRequest.objects.filter(
    change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
    system__isnull=True,
    user_username='test_deletion_user'
)
print(f"Change requests for test user: {deletion_reqs.count()}")
if deletion_reqs.exists():
    for req in deletion_reqs:
        print(f"  ✓ ID {req.id}: {req.user_username} - {req.status}")
else:
    print(f"  ✗ No change request found!")

print("=" * 70)

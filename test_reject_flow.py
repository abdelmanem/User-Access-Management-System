#!/usr/bin/env python
"""
Test script to simulate rejecting a change request via the quick-reject endpoint.
Run with: python test_reject_flow.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from change_management.models import AccountChangeRequest
from django.utils import timezone

User = get_user_model()

# Ensure superuser exists
username = 'automation_admin'
password = 'TestPass123!'
admin, created = User.objects.get_or_create(username=username)
if created:
    admin.is_staff = True
    admin.is_superuser = True
    admin.set_password(password)
    admin.first_name = 'Automation'
    admin.last_name = 'Admin'
    admin.save()
    print(f'Created superuser: {username}')
else:
    # ensure it's a superuser and set password
    changed = False
    if not admin.is_superuser:
        admin.is_superuser = True
        changed = True
    if not admin.is_staff:
        admin.is_staff = True
        changed = True
    admin.set_password(password)
    if changed:
        admin.save()
    print(f'Using existing superuser: {username}')

# Find or create a deletion change request
req = AccountChangeRequest.objects.filter(change_type=AccountChangeRequest.CHANGE_TYPE_DELETE, system__isnull=True).first()
if not req:
    req = AccountChangeRequest.objects.create(
        change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
        user=None,
        user_full_name='Automation Test',
        user_username='automation_test_user',
        system=None,
        business_justification='Test deletion for reject flow',
        requested_by=admin,
        status=AccountChangeRequest.STATUS_PENDING,
    )
    print(f'Created test change request: {req.pk}')
else:
    print(f'Found existing change request: {req.pk}')

# Use test client to login and post rejection
c = Client()
logged_in = c.login(username=username, password=password)
print('Logged in:', logged_in)

reject_url = f'/change-management/requests/{req.pk}/quick-reject/'
print('POSTing to', reject_url)
res = c.post(reject_url, {'rejection_type': 'owner', 'rejection_reason': 'Automated test rejection'}, follow=True)
print('Response status code:', res.status_code)

# Refresh from DB and print status
req.refresh_from_db()
print('Change request status:', req.status)
print('Owner approved flag:', req.system_owner_approved)
print('Owner approval notes:', req.system_owner_approval_notes)
print('Owner:', req.system_owner)
print('It approval date:', req.it_approval_date)

print('\nDone')

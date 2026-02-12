#!/usr/bin/env python
"""
Second, cleaner test for quick-reject using explicit HTTP_HOST to avoid DisallowedHost.
"""
import os, django, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from change_management.models import AccountChangeRequest

User = get_user_model()
username = 'automation_admin'
password = 'TestPass123!'
admin = User.objects.filter(username=username).first()
if not admin:
    admin = User.objects.create(username=username, is_staff=True, is_superuser=True)
    admin.set_password(password)
    admin.save()

# Create a fresh change request
uniq = str(int(time.time()))[-6:]
req = AccountChangeRequest.objects.create(
    change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
    user=None,
    user_full_name=f'Auto Test {uniq}',
    user_username=f'auto_test_{uniq}',
    system=None,
    business_justification='Test deletion for reject flow 2',
    requested_by=admin,
    status=AccountChangeRequest.STATUS_PENDING,
)
print('Created change request', req.pk)

c = Client()
assert c.login(username=username, password=password), 'Login failed'
url = f'/change-management/requests/{req.pk}/quick-reject/'
res = c.post(url, {'rejection_type': 'owner', 'rejection_reason': 'Automated reject 2'}, HTTP_HOST='localhost')
print('Status code:', res.status_code)
req.refresh_from_db()
print('Post-run status:', req.status)
print('Owner notes:', req.system_owner_approval_notes)
print('Owner:', req.system_owner)

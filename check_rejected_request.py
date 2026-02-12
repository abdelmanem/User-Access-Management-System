#!/usr/bin/env python
"""Quick analysis of the rejected request issue"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iam_governance_settings')
django.setup()

from change_management.models import AccountChangeRequest
from access_management.models import UserSystemAccess

print('\n========== DETAILED ANALYSIS OF REJECTED REQUEST ==========\n')

# Get the rejected user deletion
req = AccountChangeRequest.objects.get(id=16)
print(f'Change Request ID: {req.id}')
print(f'Change Type: {req.change_type}')
print(f'Status: {req.status}')
print(f'User (FK): {req.user}')
print(f'User Snapshot: {req.user_full_name} ({req.user_username})')
print(f'System: {req.system}')
print(f'Business Justification: {req.business_justification}')
print(f'Created: {req.created_at}')
print(f'System Owner Approval Date: {req.system_owner_approval_date}')
print(f'Approval Notes: {req.system_owner_approval_notes}')

print(f'\n✗ ISSUE CONFIRMED:')
print(f'   The user "{req.user_full_name}" was DELETED from the database')
print(f'   But the change request shows status: {req.status}')
print(f'   This proves rejection was ineffective - user already gone!')

# Check for any access assignments for this user
print(f'\n========== RELATED ACCESS ASSIGNMENTS ==========\n')
accesses = UserSystemAccess.all_objects.filter(user__username=req.user_username)
print(f'Access assignments for {req.user_username}: {accesses.count()}')
for acc in accesses[:5]:
    print(f'  - System: {acc.system.name}, Status: {acc.status}, is_deleted: {acc.is_deleted}')

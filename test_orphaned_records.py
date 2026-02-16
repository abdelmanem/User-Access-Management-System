#!/usr/bin/env python
"""
Test script to check for orphaned access assignment records
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from access_management.models import UserSystemAccess

# Test 1: Count all access assignments
total_count = UserSystemAccess.objects.count()
print(f"✓ Total access assignments: {total_count}")

# Test 2: Count where user is NULL
orphaned_count = UserSystemAccess.objects.filter(user__isnull=True).count()
print(f"✓ Orphaned assignments (user__isnull=True): {orphaned_count}")

# Test 3: Count distinct users
distinct_users = UserSystemAccess.objects.values('user_id').distinct().count()
print(f"✓ Distinct users with assignments: {distinct_users}")

# Test 4: Get details of orphaned records if any
if orphaned_count > 0:
    print("\n📌 Orphaned Records Details:")
    orphaned = UserSystemAccess.objects.filter(user__isnull=True)
    for i, record in enumerate(orphaned[:10], 1):
        print(f"  {i}. ID: {record.id}, System: {record.system.name if record.system else 'NULL'}, Status: {record.status}, Request Date: {record.request_date}")
else:
    print("\n✓ No orphaned records found.")

# Test 5: Show variance explanation
active_exclude = UserSystemAccess.objects.exclude(user__isnull=True).count()
print(f"\n📊 Variance Analysis:")
print(f"  Total assignments: {total_count}")
print(f"  Assignments with valid user: {active_exclude}")
print(f"  Orphaned (user deleted): {orphaned_count}")
print(f"  Variance: {total_count - distinct_users} (from multiple assignments per user + orphaned)")

# Test 6: Check for assignments where user exists but is marked as deleted
from accounts.models import CustomUser
deleted_user_assignments = UserSystemAccess.objects.filter(user__isnull=False).filter(
    user__is_active=False
).values('user_id').distinct().count()
print(f"\n📌 Inactive/Archived Users with assignments: {deleted_user_assignments}")

# Test 7: Detailed breakdown
print(f"\n📊 Complete Breakdown:")
print(f"  Total assignments: {total_count}")
print(f"  Unique users (active + inactive): {distinct_users}")
print(f"  Orphaned (no user): {orphaned_count}")
print(f"  Expected variance: {distinct_users - 1 + orphaned_count} (some users have multiple assignments)")

#!/usr/bin/env python
"""Test script to check user archive and change request 9"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from change_management.models import AccountChangeRequest
from accounts.models import UserArchive

# Check change request 9
cr9 = AccountChangeRequest.objects.get(pk=9)
print("\n" + "=" * 80)
print("CHANGE REQUEST 9 DETAILS")
print("=" * 80)
print(f"ID: {cr9.pk}")
print(f"Change Type: {cr9.change_type}")
print(f"User ID: {cr9.user_id}")
print(f"User Full Name: '{cr9.user_full_name}'")
print(f"User Username: '{cr9.user_username}'")
print(f"System: {cr9.system.name}")
print(f"Created At: {cr9.created_at}")

# Check if there's archived user data
print("\n" + "=" * 80)
print("CHECKING USER ARCHIVES")
print("=" * 80)

archives = UserArchive.objects.filter(source_user_id=cr9.user_id) if cr9.user_id else UserArchive.objects.all()
print(f"\nTotal archives: {archives.count()}")
for archive in archives[:5]:
    print(f"  - {archive.username} ({archive.full_name}) - ID: {archive.source_user_id}")

print("\n" + "=" * 80)

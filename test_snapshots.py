#!/usr/bin/env python
"""Test script to check populated snapshots"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from change_management.models import AccountChangeRequest

# Check the first few change requests
requests = AccountChangeRequest.objects.all()[:10]
print("\n" + "=" * 80)
print("CHANGE REQUEST SNAPSHOTS")
print("=" * 80)
for req in requests:
    print(f"\nID: {req.pk}")
    print(f"  Change Type: {req.change_type}")
    print(f"  User ID: {req.user_id}")
    print(f"  User Full Name: '{req.user_full_name}'")
    print(f"  User Username: '{req.user_username}'")
    print(f"  User Object exists: {req.user is not None}")
    print(f"  System: {req.system.name if req.system else 'N/A'}")
print("\n" + "=" * 80)

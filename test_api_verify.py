#!/usr/bin/env python
"""Test the Change Management REST API"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from accounts.models import CustomUser
from change_management.models import AccountChangeRequest
from rest_framework.test import APIClient

# Create a test user if needed
user, created = CustomUser.objects.get_or_create(
    username='testuser',
    defaults={'email': 'test@example.com', 'is_staff': False}
)

print(f"Test user: {user.username} (created: {created})")

# Test the API with authenticated client
client = APIClient()
client.force_authenticate(user=user)

# Test 1: List change requests
print("\n=== Test 1: List Change Requests ===")
response = client.get('/api/change-requests/')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Response keys: {list(data.keys())}")
    if 'results' in data:
        print(f"Change requests found: {len(data['results'])}")
else:
    print(f"Error: {response.text[:200]}")

# Test 2: Get API root
print("\n=== Test 2: API Root ===")
response = client.get('/api/')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Available endpoints: {list(response.json().keys())}")

# Test 3: Check pending approvals
print("\n=== Test 3: Pending Approvals ===")
response = client.get('/api/change-requests/pending-approvals/')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")
else:
    print(f"Error: {response.text[:200]}")

# Test 4: Check statistics
print("\n=== Test 4: Statistics ===")
response = client.get('/api/change-requests/statistics/')
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print(f"Response: {response.json()}")
else:
    print(f"Error: {response.text[:200]}")

print("\n✅ API Tests Complete!")
print(f"Total change requests in database: {AccountChangeRequest.objects.count()}")

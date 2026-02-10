#!/usr/bin/env python
"""
Test script to verify the delete URL routing is working correctly
Run with: python manage.py shell < test_delete_url.py
"""
from django.urls import reverse, resolve
from django.test import Client
from access_management.models import UserSystemAccess

# Test 1: Check URL reversal
print("=" * 60)
print("TEST 1: URL Reversal")
print("=" * 60)
try:
    url = reverse('access_management:access_assignment_delete', kwargs={'pk': 245})
    print(f"✓ Reversed URL: {url}")
    print(f"  Expected: /access-management/assignments/245/delete/")
except Exception as e:
    print(f"✗ Error reversing URL: {e}")

# Test 2: Check URL resolution
print("\n" + "=" * 60)
print("TEST 2: URL Resolution")
print("=" * 60)
try:
    match = resolve('/access-management/assignments/245/delete/')
    print(f"✓ Resolved view: {match.func.__name__}")
    print(f"  View function: {match.func}")
    print(f"  Expected: access_assignment_delete")
    if match.func.__name__ == 'access_assignment_delete':
        print("  ✓ CORRECT VIEW MATCHED")
    else:
        print("  ✗ WRONG VIEW MATCHED - This is the problem!")
except Exception as e:
    print(f"✗ Error resolving URL: {e}")

# Test 3: Check view returns correct template
print("\n" + "=" * 60)
print("TEST 3: Check GET Request (simulated)")
print("=" * 60)
try:
    client = Client()
    # Try to get the delete page (will require authentication)
    response = client.get('/access-management/assignments/245/delete/', follow=True)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✓ GET request returned 200 OK")
        # Check if custom template was used
        if 'access_assignment_confirm_delete.html' in [t.name for t in response.templates]:
            print("✓ Custom template 'access_assignment_confirm_delete.html' was used")
        else:
            templates_used = [t.name for t in response.templates]
            print(f"✗ Wrong template used: {templates_used}")
            print("  The view might be redirecting to Django admin delete page")
    elif response.status_code == 302:
        print(f"Status 302 Redirect to: {response.url}")
        print("  (This might be a login redirect or other redirect)")
    elif response.status_code == 404:
        print("✗ 404 NOT FOUND - The URL pattern might not be registered")
    else:
        print(f"Status {response.status_code}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Check if template file exists
print("\n" + "=" * 60)
print("TEST 4: Template File Existence")
print("=" * 60)
from pathlib import Path
from django.conf import settings

template_path = settings.BASE_DIR / 'access_management/templates/access_management/access_assignment_confirm_delete.html'
if template_path.exists():
    print(f"✓ Template file exists: {template_path}")
    print(f"  File size: {template_path.stat().st_size} bytes")
else:
    print(f"✗ Template file NOT FOUND: {template_path}")
    # List what files are in the directory
    template_dir = settings.BASE_DIR / 'access_management/templates/access_management/'
    if template_dir.exists():
        files = list(template_dir.glob('*.html'))
        print(f"  Files in directory: {[f.name for f in files]}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("""
If all tests pass (✓), then the custom delete page should work.
If TEST 3 shows the wrong template or TEST 4 shows file not found,
that's why you're seeing the Django default page.

The most likely issue is browser cache. Try:
1. Clear browser cache (Ctrl+Shift+Delete in most browsers)
2. Or use Private/Incognito browsing
3. Or restart the Django development server
""")

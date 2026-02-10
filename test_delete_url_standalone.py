#!/usr/bin/env python
"""
Standalone test script to verify the delete URL routing
Run with: python test_delete_url_standalone.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import reverse, resolve
from pathlib import Path
from django.conf import settings

print("\n" + "=" * 70)
print("DELETE URL ROUTING TEST")
print("=" * 70)

# Test 1: URL Reversal
print("\n[TEST 1] URL Reversal")
print("-" * 70)
try:
    url = reverse('access_management:access_assignment_delete', kwargs={'pk': 245})
    print(f"✓ Reversed URL: {url}")
    if url == '/access-management/assignments/245/delete/':
        print("✓ URL format is CORRECT")
    else:
        print(f"✗ URL format is WRONG (expected /access-management/assignments/245/delete/)")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: URL Resolution
print("\n[TEST 2] URL Resolution")
print("-" * 70)
try:
    match = resolve('/access-management/assignments/245/delete/')
    view_name = match.func.__name__
    print(f"✓ Resolved view: {view_name}")
    if view_name == 'access_assignment_delete':
        print("✓ CORRECT VIEW is being called")
    else:
        print(f"✗ WRONG VIEW - {view_name} is being called instead of access_assignment_delete")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Template file exists
print("\n[TEST 3] Template File Existence")
print("-" * 70)
template_path = settings.BASE_DIR / 'access_management' / 'templates' / 'access_management' / 'access_assignment_confirm_delete.html'
if template_path.exists():
    print(f"✓ Template file EXISTS: {template_path}")
    file_size = template_path.stat().st_size
    print(f"  File size: {file_size} bytes")
else:
    print(f"✗ Template file NOT FOUND: {template_path}")
    # List what's in the directory
    template_dir = template_path.parent
    if template_dir.exists():
        files = [f.name for f in template_dir.glob('*.html')]
        print(f"  Available HTML files in {template_dir}:")
        for f in sorted(files):
            print(f"    - {f}")

# Test 4: Check if view function exists and has correct decorator
print("\n[TEST 4] View Function Analysis")
print("-" * 70)
try:
    from access_management import views
    if hasattr(views, 'access_assignment_delete'):
        func = views.access_assignment_delete
        print(f"✓ View function exists: {func}")
        
        # Check if it's decorated with login_required
        if hasattr(func, '__wrapped__'):
            print("✓ View appears to have a decorator (likely @login_required)")
        
        # Check the function's module
        print(f"  Module: {func.__module__}")
        print(f"  Name: {func.__name__}")
    else:
        print("✗ View function 'access_assignment_delete' not found in views module")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 5: Check URL patterns
print("\n[TEST 5] URL Pattern Registration")
print("-" * 70)
try:
    from access_management import urls as am_urls
    pattern_found = False
    for pattern in am_urls.urlpatterns:
        if 'delete' in str(pattern.pattern):
            print(f"✓ Delete pattern found: {pattern.pattern}")
            print(f"  Name: {pattern.name}")
            pattern_found = True
    if not pattern_found:
        print("✗ No delete pattern found in access_management URLs")
except Exception as e:
    print(f"✗ Error: {e}")

# Summary
print("\n" + "=" * 70)
print("ANALYSIS SUMMARY")
print("=" * 70)
print("""
If all tests show ✓ (green checks), then:
1. The URL routing is correct
2. The custom view is being called
3. The template file exists

The custom delete confirmation page should display.

If something shows ✗ (red), that's the issue.

SOLUTION IF STILL NOT WORKING:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Restart Django server (python manage.py runserver)
3. Try in Incognito/Private browsing mode
4. Check browser console (F12) for any errors
""")
print("=" * 70 + "\n")

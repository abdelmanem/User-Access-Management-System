#!/usr/bin/env python
"""Test script to verify password history form pre-fill and save logic"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from service_accounts.models import ServiceAccount, ServiceAccountPasswordHistory
from service_accounts.forms import ServiceAccountPasswordHistoryForm
from django.utils import timezone

# Get a service account with an expiration date for testing
sa = ServiceAccount.objects.filter(is_active=True).first()

if sa:
    print(f"✓ Found service account: {sa.account_name}")
    print(f"  Current password_expires_on: {sa.password_expires_on}")
    
    # Test pre-fill
    initial_data = {
        'service_account': sa,
        'password_changed_date': timezone.now(),
    }
    if sa.password_expires_on:
        initial_data['expires_on'] = sa.password_expires_on
    
    form = ServiceAccountPasswordHistoryForm(initial=initial_data)
    
    # Check if the form field has the initial value
    expires_field = form['expires_on']
    print(f"\n✓ Form expires_on field:")
    print(f"  Initial: {initial_data.get('expires_on')}")
    print(f"  Form rendered HTML: {str(expires_field)[:100]}...")
    
    # Test form validation with the same data
    form_data = {
        'service_account': sa.id,
        'password_changed_date': timezone.now().isoformat(),
        'expires_on': sa.password_expires_on.isoformat() if sa.password_expires_on else '',
        'complies_with_policy': True,
        'notes': 'Test password change'
    }
    
    form_submit = ServiceAccountPasswordHistoryForm(form_data)
    if form_submit.is_valid():
        print(f"\n✓ Form validation passed")
        print(f"  Cleaned expires_on: {form_submit.cleaned_data.get('expires_on')}")
    else:
        print(f"\n✗ Form validation failed:")
        print(f"  Errors: {form_submit.errors}")
else:
    print("✗ No active service accounts found")

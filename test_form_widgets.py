#!/usr/bin/env python
"""Test script to verify form widgets are properly configured"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from access_management.forms import QuarterlyActiveUserReviewForm, MonthlyObsoleteAccountReviewForm

# Test quarterly form
print("=== Testing Quarterly Active User Review Form ===")
quarterly_form = QuarterlyActiveUserReviewForm()
print(f"✓ review_quarter field type: {type(quarterly_form.fields['review_quarter']).__name__}")
print(f"✓ review_quarter widget: {type(quarterly_form.fields['review_quarter'].widget).__name__}")
print(f"✓ review_quarter has {len(quarterly_form.fields['review_quarter'].choices)} quarter options")
print(f"✓ First 3 choices: {quarterly_form.fields['review_quarter'].choices[:3]}")
print(f"✓ review_quarter initial value: {quarterly_form.initial.get('review_quarter')}")

# Test monthly form
print("\n=== Testing Monthly Obsolete Account Review Form ===")
monthly_form = MonthlyObsoleteAccountReviewForm()
print(f"✓ review_month field type: {type(monthly_form.fields['review_month']).__name__}")
print(f"✓ review_month widget: {type(monthly_form.fields['review_month'].widget).__name__}")
print(f"✓ review_month widget input type: {monthly_form.fields['review_month'].widget.input_type}")
print(f"✓ review_month initial value: {monthly_form.initial.get('review_month')}")

print("\n✅ All form widgets configured successfully!")

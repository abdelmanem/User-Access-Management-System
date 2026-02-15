#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from django.template import Template, Context

# Test if the add_class filter is registered
test_template = """
{% load form_extras %}
{{ field|add_class:"form-select" }}
"""

try:
    t = Template(test_template)
    print('✓ Template with add_class filter compiles successfully')
except Exception as e:
    print(f'✗ Filter Error: {type(e).__name__}: {e}')

#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from systems.forms import SystemForm
from systems.models import System

s = System.objects.first()
if s:
    form = SystemForm(instance=s)
    hw_count = form.fields['hardware_assets'].queryset.count()
    print(f'Form hardware_assets queryset count: {hw_count}')
    hw_list = list(s.hardware_assets.values_list('name', flat=True)[:5])
    print(f'System {s.name} current hardware: {hw_list}')
    print(f'Initial values set: {list(form.fields["hardware_assets"].initial)[:3] if form.fields["hardware_assets"].initial else "None"}')
else:
    print('No systems found')

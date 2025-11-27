#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from accounts.models import LDAPConfiguration

c = LDAPConfiguration.objects.first()
if c:
    c.ldap_filter = '(&(objectClass=user)(objectCategory=person))'
    c.save()
    print("✅ LDAP Filter updated to: (&(objectClass=user)(objectCategory=person))")
else:
    print("❌ No LDAP configuration found")


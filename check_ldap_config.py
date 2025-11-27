#!/usr/bin/env python
"""
Quick diagnostic script to check LDAP configuration
Run this to see what's configured
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from accounts.models import LDAPConfiguration

config = LDAPConfiguration.objects.first()

if not config:
    print("❌ No LDAP configuration found!")
    print("\nPlease create one at: /accounts/ldap/configuration/")
else:
    print("✅ LDAP Configuration Found\n")
    print("=" * 50)
    print(f"LDAP Enabled: {'✅ Yes' if config.ldap_enabled else '❌ No'}")
    print(f"Server: {config.ldap_server}")
    print(f"Active Directory: {'✅ Yes' if config.is_active_directory else '❌ No'}")
    print(f"Base DN: {config.base_dn or '❌ NOT SET'}")
    print(f"Bind Username: {config.bind_username or '❌ NOT SET'}")
    print(f"Bind Password: {'✅ SET (length: {len(config.bind_password)})' if config.bind_password else '❌ NOT SET - THIS IS THE PROBLEM!'}")
    print(f"LDAP Filter: {config.ldap_filter}")
    print(f"Username Field: {config.ldap_username_field}")
    print("=" * 50)
    
    if not config.bind_password:
        print("\n⚠️  PROBLEM FOUND:")
        print("   The Bind Password is NOT set!")
        print("\n📝 TO FIX:")
        print("   1. Go to: /accounts/ldap/configuration/")
        print("   2. Enter the Bind Password")
        print("   3. Click 'Save LDAP Configuration'")
        print("   4. Try test login again")
    elif not config.bind_username:
        print("\n⚠️  PROBLEM FOUND:")
        print("   The Bind Username is NOT set!")
    else:
        print("\n✅ Configuration looks good!")
        print("   If you're still getting errors, check:")
        print("   - Server is reachable")
        print("   - Bind username format is correct")
        print("   - Bind password is correct")


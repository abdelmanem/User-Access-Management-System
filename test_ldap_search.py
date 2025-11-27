#!/usr/bin/env python
"""
LDAP Search Diagnostic Script
Tests different search configurations to find users
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from ldap3 import Server, Connection, ALL, SIMPLE, SUBTREE
from accounts.models import LDAPConfiguration

config = LDAPConfiguration.objects.first()

if not config:
    print("❌ No LDAP configuration found!")
    exit(1)

print("=" * 60)
print("LDAP Search Diagnostic")
print("=" * 60)
print(f"Server: {config.ldap_server}")
print(f"Base DN: {config.base_dn}")
print(f"Bind User: {config.bind_username}")
print(f"Filter: {config.ldap_filter}")
print("=" * 60)

try:
    # Connect to server
    server = Server(config.ldap_server, get_info=ALL)
    conn = Connection(
        server,
        user=config.bind_username,
        password=config.bind_password,
        authentication=SIMPLE,
        auto_bind=True
    )
    print("✅ Connected successfully!\n")
    
    # Test 1: Current filter
    print("TEST 1: Using your current filter")
    print(f"   Filter: {config.ldap_filter}")
    print(f"   Base DN: {config.base_dn}")
    conn.search(
        search_base=config.base_dn,
        search_filter=config.ldap_filter or '(&(objectClass=user)(objectCategory=person))',
        search_scope=SUBTREE,
        attributes=['sAMAccountName', 'cn', 'distinguishedName']
    )
    print(f"   Found: {len(conn.entries)} users")
    if conn.entries:
        print("   First 5 users:")
        for entry in conn.entries[:5]:
            print(f"      - {entry.entry_dn}")
    print()
    
    # Test 2: Simple filter - all users
    print("TEST 2: Simple filter (objectClass=user)")
    conn.search(
        search_base=config.base_dn,
        search_filter='(objectClass=user)',
        search_scope=SUBTREE,
        attributes=['sAMAccountName', 'cn']
    )
    print(f"   Found: {len(conn.entries)} entries")
    if conn.entries:
        print("   First 5:")
        for entry in conn.entries[:5]:
            sam = entry.sAMAccountName.value if hasattr(entry, 'sAMAccountName') else 'N/A'
            print(f"      - {sam} ({entry.entry_dn})")
    print()
    
    # Test 3: All persons
    print("TEST 3: Filter (objectClass=person)")
    conn.search(
        search_base=config.base_dn,
        search_filter='(objectClass=person)',
        search_scope=SUBTREE,
        attributes=['sAMAccountName', 'cn']
    )
    print(f"   Found: {len(conn.entries)} entries")
    print()
    
    # Test 4: Try CN=Users container specifically
    users_dn = f"CN=Users,{config.base_dn}"
    print(f"TEST 4: Search in CN=Users container")
    print(f"   Base DN: {users_dn}")
    try:
        conn.search(
            search_base=users_dn,
            search_filter='(objectClass=user)',
            search_scope=SUBTREE,
            attributes=['sAMAccountName', 'cn']
        )
        print(f"   Found: {len(conn.entries)} entries")
        if conn.entries:
            print("   First 5:")
            for entry in conn.entries[:5]:
                sam = entry.sAMAccountName.value if hasattr(entry, 'sAMAccountName') else 'N/A'
                print(f"      - {sam}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test 5: Check what OUs exist
    print("TEST 5: List Organizational Units (OUs)")
    conn.search(
        search_base=config.base_dn,
        search_filter='(objectClass=organizationalUnit)',
        search_scope=SUBTREE,
        attributes=['ou', 'distinguishedName']
    )
    print(f"   Found: {len(conn.entries)} OUs")
    for entry in conn.entries[:10]:
        print(f"      - {entry.entry_dn}")
    print()
    
    # Test 6: Check if filter excludes disabled accounts
    print("TEST 6: Include disabled accounts")
    conn.search(
        search_base=config.base_dn,
        search_filter='(&(objectClass=user)(objectCategory=person))',
        search_scope=SUBTREE,
        attributes=['sAMAccountName', 'userAccountControl']
    )
    print(f"   Found: {len(conn.entries)} total user accounts")
    
    enabled = 0
    disabled = 0
    for entry in conn.entries:
        if hasattr(entry, 'userAccountControl'):
            uac = int(entry.userAccountControl.value) if entry.userAccountControl.value else 0
            if uac & 2:  # Disabled flag
                disabled += 1
            else:
                enabled += 1
    print(f"   Enabled: {enabled}, Disabled: {disabled}")
    print()
    
    conn.unbind()
    
    print("=" * 60)
    print("RECOMMENDATIONS:")
    print("=" * 60)
    
    if len(conn.entries) == 0:
        print("❌ No users found with any filter!")
        print("   Possible causes:")
        print("   1. Base DN is incorrect")
        print("   2. Bind account doesn't have read permissions")
        print("   3. Users are in a different OU")
        print("\n   Try changing Base DN to a specific OU where users exist")
    else:
        print("✅ Users found! Your current filter might be too restrictive.")
        print("   Try this filter: (&(objectClass=user)(objectCategory=person))")
        
except Exception as e:
    print(f"❌ Connection Error: {e}")
    print("\nCheck:")
    print("  - Server is reachable")
    print("  - Bind credentials are correct")
    print("  - Firewall allows connection")


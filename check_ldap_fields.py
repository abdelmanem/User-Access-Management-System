#!/usr/bin/env python
"""
Check what LDAP fields are available and how they map to user fields
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from ldap3 import Server, Connection, ALL, SIMPLE, SUBTREE
from accounts.models import LDAPConfiguration

config = LDAPConfiguration.objects.first()

print("=" * 70)
print("LDAP Field Analysis - What fields are available in your AD")
print("=" * 70)

server = Server(config.ldap_server, get_info=ALL)
conn = Connection(
    server,
    user=config.bind_username,
    password=config.bind_password,
    authentication=SIMPLE,
    auto_bind=True
)

# Get one sample user with ALL attributes
conn.search(
    search_base=config.base_dn,
    search_filter='(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))',
    search_scope=SUBTREE,
    attributes='*',
    size_limit=1
)

if conn.entries:
    entry = conn.entries[0]
    print(f"\nSample User: {entry.entry_dn}\n")
    print("Available LDAP Attributes:")
    print("-" * 70)
    
    # Common fields we care about
    important_fields = [
        'sAMAccountName', 'givenName', 'sn', 'displayName', 'mail',
        'department', 'title', 'description', 'manager',
        'telephoneNumber', 'mobile', 'employeeNumber', 'employeeID',
        'streetAddress', 'l', 'st', 'postalCode', 'co', 'c',
        'physicalDeliveryOfficeName', 'company', 'distinguishedName',
        'userAccountControl', 'memberOf'
    ]
    
    print("\n📋 KEY FIELDS FOR USER SYNC:\n")
    for field in important_fields:
        value = None
        # Try different cases
        for attr in entry.entry_attributes:
            if attr.lower() == field.lower():
                value = entry[attr].value
                break
        
        if value:
            # Truncate long values
            val_str = str(value)
            if len(val_str) > 60:
                val_str = val_str[:60] + "..."
            print(f"  ✅ {field:30} = {val_str}")
        else:
            print(f"  ❌ {field:30} = (not set)")
    
    print("\n" + "-" * 70)
    print("\n📝 ALL AVAILABLE ATTRIBUTES:\n")
    for attr in sorted(entry.entry_attributes):
        value = entry[attr].value
        if value:
            val_str = str(value)
            if len(val_str) > 50:
                val_str = val_str[:50] + "..."
            print(f"  {attr:35} = {val_str}")

conn.unbind()

print("\n" + "=" * 70)
print("CURRENT FIELD MAPPING IN YOUR CONFIG:")
print("=" * 70)
print(f"  Username Field:      {config.ldap_username_field or 'samaccountname'}")
print(f"  First Name Field:    {config.ldap_firstname_field or 'givenname'}")
print(f"  Last Name Field:     {config.ldap_lastname_field or 'sn'}")
print(f"  Display Name Field:  {config.ldap_displayname_field or 'displayname'}")
print(f"  Email Field:         {config.ldap_email_field or 'mail'}")
print(f"  Department Field:    {config.ldap_department_field or 'department'}")
print(f"  Job Title Field:     {config.ldap_jobtitle_field or 'title'}")
print(f"  Phone Field:         {config.ldap_phone_field or 'telephonenumber'}")
print(f"  Mobile Field:        {config.ldap_mobile_field or 'mobile'}")
print(f"  Manager Field:       {config.ldap_manager_field or 'manager'}")
print(f"  Employee # Field:    {config.ldap_employeenumber_field or 'employeenumber'}")
print(f"  Address Field:       {config.ldap_address_field or 'streetaddress'}")
print(f"  City Field:          {config.ldap_city_field or 'l'}")
print(f"  State Field:         {config.ldap_state_field or 'st'}")
print(f"  Postal Code Field:   {config.ldap_postalcode_field or 'postalcode'}")
print(f"  Country Field:       {config.ldap_country_field or 'co'}")
print("=" * 70)


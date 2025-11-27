# LDAP/Active Directory Integration Guide

## Overview

The User Access Management System includes comprehensive LDAP/Active Directory (AD) integration for enterprise authentication and user synchronization. This feature allows organizations to:

- Authenticate users against their corporate LDAP/AD server
- Automatically sync user information from LDAP/AD
- Map LDAP attributes to user profile fields
- Support both Active Directory and generic LDAP servers
- Cache passwords locally for offline authentication

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Configuration](#configuration)
3. [Server Settings](#server-settings)
4. [Field Mapping](#field-mapping)
5. [Testing](#testing)
6. [User Synchronization](#user-synchronization)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

---

## Prerequisites

### Required Packages

The following Python packages are required and included in `requirements.txt`:

- `ldap3==2.9.1` - Pure Python LDAP client library
- `pyasn1==0.6.0` - ASN.1 types and codecs

Install them using:

```bash
pip install ldap3==2.9.1 pyasn1==0.6.0
```

**Why ldap3?** We use `ldap3` (pure Python) instead of `python-ldap` because:
- No C compiler required (works on Windows without Visual Studio)
- Cross-platform compatibility
- Easier installation
- Full-featured LDAP v3 client
- We built a custom authentication backend using `ldap3`

### LDAP Server Requirements

- Access to an LDAP or Active Directory server
- A service account with read access to the directory
- Network connectivity to the LDAP server (port 389 for LDAP, 636 for LDAPS)

---

## Configuration

### Accessing Configuration

1. Log in as a superuser
2. Navigate to **LDAP/AD Configuration** from the admin menu
3. Or access directly: `/accounts/ldap/configuration/`

### Server Settings

#### LDAP Integration

- **LDAP Enabled**: Toggle to enable/disable LDAP authentication
- **Active Directory**: Check if connecting to an Active Directory server
- **Cache LDAP Passwords**: When enabled, stores hashed passwords locally for offline authentication

#### Active Directory Domain

- Example: `example.com` or `corp.example.com`
- Often matches your email domain but not always

#### LDAP Server

Format: `protocol://hostname:port`

Examples:
- Unencrypted: `ldap://dc.example.com:389`
- SSL/TLS: `ldaps://dc.example.com:636`
- With STARTTLS: `ldap://dc.example.com:389` (enable "Use TLS" checkbox)

#### TLS/SSL Settings

- **Use TLS**: Enable STARTTLS for encrypted connection
- **Allow Invalid SSL Certificate**: For self-signed certificates (not recommended for production)
- **Client TLS Certificate/Key**: Required for Google Workspace Secure LDAP

### Bind Settings

#### Bind Username

The service account used to connect to LDAP. Format varies:

**Active Directory:**
- Distinguished Name: `CN=ServiceAccount,CN=Users,DC=example,DC=com`
- User Principal Name: `serviceaccount@example.com`

**OpenLDAP:**
- `cn=admin,dc=example,dc=com`

#### Bind Password

Password for the bind user account.

#### Base Bind DN

Starting point for LDAP searches.

Examples:
- Active Directory: `DC=example,DC=com`
- OpenLDAP: `ou=users,dc=example,dc=com`

### Search and Authentication

#### LDAP Filter

Filter to identify user objects.

**Active Directory:**
```
(&(objectClass=user)(objectCategory=person))
```

**OpenLDAP:**
```
(objectClass=inetOrgPerson)
```

#### LDAP Authentication Query

Custom authentication query (optional). Leave blank for default behavior.

#### Default Permission Group

Automatically assign new LDAP users to a Django group.

---

## Field Mapping

### Important Notes

- **Use lowercase** for Active Directory field names (e.g., `samaccountname`, not `sAMAccountName`)
- Fields left blank won't sync from LDAP
- Custom field mappings depend on your LDAP schema

### Basic Fields

| Field | AD Default | OpenLDAP Default | Description |
|-------|-----------|------------------|-------------|
| Username | `samaccountname` | `uid` | Login username |
| First Name | `givenname` | `givenName` | User's first name |
| Last Name | `sn` | `sn` | User's surname |
| Display Name | `displayname` | `displayName` | Full display name |
| Email | `mail` | `mail` | Email address |

### Extended Fields

| Field | AD Default | Description |
|-------|-----------|-------------|
| Employee Number | `employeenumber` | Employee ID |
| Department | `department` | Department name |
| Manager | `manager` | Manager's DN |
| Phone | `telephonenumber` | Primary phone |
| Mobile | `mobile` | Mobile phone |
| Job Title | `title` | Job position |

### Location Fields

| Field | AD Default | Description |
|-------|-----------|-------------|
| Address | `streetaddress` | Street address |
| City | `l` | City/locality |
| State | `st` | State/province |
| Postal Code | `postalcode` | ZIP/postal code |
| Country | `co` | Country |
| Location | - | Custom location field |

### Active Flag

Controls whether users can log in based on LDAP status.

**Active Directory:**
- Field: `useraccountcontrol`
- Logic: Checks bit 2 (disabled flag)
- Invert: When enabled, treats 0/false as active

**Generic LDAP:**
- Common fields: `active`, `enabled`, `accountStatus`
- Treats 1/true/enabled as active
- Use "Invert Active Flag" to reverse logic

---

## Testing

### Test Connection

1. Save your configuration
2. Click **Test Connection**
3. Verifies:
   - Server is reachable
   - Bind credentials are correct
   - TLS/SSL configuration works

### Test Login

1. Save your configuration
2. Enter valid LDAP credentials in the test form
3. Click **Test Login**
4. Verifies:
   - User can be found in directory
   - Authentication succeeds
   - Field mapping works correctly

**Success Example:**
```
✓ LDAP login successful for user: jdoe (John Doe)
```

**Failure Example:**
```
✗ LDAP login failed for user: jdoe. Check credentials and LDAP configuration.
```

---

## User Synchronization

### Manual Sync

1. Navigate to LDAP Configuration
2. Click **Sync All Users**
3. System will:
   - Search for all users matching the LDAP filter
   - Create new users or update existing ones
   - Sync all mapped fields
   - Apply default permission group

**Note:** Large directories may take several minutes to sync.

### Automatic Sync on Login

When a user logs in with LDAP credentials:
1. User is authenticated against LDAP
2. User account is created/updated automatically
3. All mapped fields are synced
4. Password is cached (if enabled)

### Sync Results

After sync, you'll see:
```
✓ Synced 150 users successfully, 3 errors
```

Check logs for detailed error information.

---

## Troubleshooting

### Common Issues

#### "Connection Failed"

**Causes:**
- Server unreachable
- Incorrect hostname/port
- Firewall blocking connection
- SSL/TLS configuration issues

**Solutions:**
- Verify server URL format
- Test network connectivity: `telnet dc.example.com 389`
- Check firewall rules
- Try without TLS first, then enable

#### "Bind Failed"

**Causes:**
- Incorrect bind username/password
- Service account locked/disabled
- Insufficient permissions

**Solutions:**
- Verify credentials with ldapsearch or AD tools
- Check account status in Active Directory
- Ensure service account has read permissions

#### "User Not Found"

**Causes:**
- Incorrect Base DN
- LDAP filter too restrictive
- User outside search scope

**Solutions:**
- Verify Base DN covers user location
- Test LDAP filter with ldapsearch
- Check user's OU/container path

#### "Login Succeeds but No Field Sync"

**Causes:**
- Field names incorrect (case-sensitive in some cases)
- Attributes not present in LDAP
- Permissions to read attributes

**Solutions:**
- Use lowercase for AD field names
- Verify attributes exist: `ldapsearch -x -b "CN=User,DC=example,DC=com" -s base`
- Check service account read permissions

#### "SSL Certificate Validation Failed"

**Causes:**
- Self-signed certificate
- Certificate chain incomplete
- Certificate expired

**Solutions:**
- Enable "Allow Invalid SSL Certificate" (development only)
- Install proper CA certificate
- Use non-SSL connection for testing

### Debug Logging

Enable debug logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'accounts.ldap_backend': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Security Considerations

### Best Practices

1. **Service Account Security**
   - Use dedicated service account with minimal permissions
   - Implement strong password policies
   - Rotate credentials regularly
   - Audit service account usage

2. **Connection Security**
   - Always use TLS/SSL in production
   - Never allow invalid certificates in production
   - Use LDAPS (port 636) or STARTTLS (port 389)

3. **Password Caching**
   - Enable for better availability
   - Passwords stored as Django-style hashes (bcrypt/PBKDF2)
   - Users can still login if LDAP is unavailable

4. **Access Control**
   - Restrict LDAP configuration to superusers only
   - Audit configuration changes
   - Monitor authentication logs

5. **Network Security**
   - Use VPN or private network for LDAP traffic
   - Implement IP restrictions on LDAP server
   - Use firewall rules to limit access

### Data Privacy

- LDAP data processed according to your privacy policy
- Synced data stored in Django database
- Consider GDPR/compliance requirements
- Implement data retention policies

---

## Configuration Examples

### Example 1: Active Directory (Standard)

```
LDAP Server: ldap://dc.corp.example.com:389
Use TLS: Yes
Bind Username: CN=ServiceAccount,CN=Users,DC=corp,DC=example,DC=com
Base DN: DC=corp,DC=example,DC=com
LDAP Filter: (&(objectClass=user)(objectCategory=person))
Username Field: samaccountname
Email Field: mail
```

### Example 2: Active Directory (LDAPS)

```
LDAP Server: ldaps://dc.corp.example.com:636
Use TLS: No (already using LDAPS)
Allow Invalid SSL: No
Bind Username: serviceaccount@corp.example.com
Base DN: DC=corp,DC=example,DC=com
LDAP Filter: (&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))
```

### Example 3: OpenLDAP

```
LDAP Server: ldap://ldap.example.com:389
Use TLS: Yes
Bind Username: cn=admin,dc=example,dc=com
Base DN: ou=users,dc=example,dc=com
LDAP Filter: (objectClass=inetOrgPerson)
Username Field: uid
Email Field: mail
```

### Example 4: Google Workspace Secure LDAP

```
LDAP Server: ldaps://ldap.google.com:636
Client TLS Certificate: [Paste certificate from Google Admin Console]
Client TLS Key: [Paste private key from Google Admin Console]
Bind Username: [Service account from Google]
Base DN: dc=example,dc=com
LDAP Filter: (objectClass=user)
```

---

## API Reference

### LDAPConfiguration Model

Located in `accounts/models.py`

**Key Methods:**
- `get_active_config()`: Returns the currently active LDAP configuration

### LDAPAuthenticationBackend

Located in `accounts/ldap_backend.py`

**Key Methods:**
- `authenticate(username, password)`: Authenticate user against LDAP
- `_ldap_authenticate()`: Handle LDAP connection and authentication
- `_update_user_from_ldap()`: Sync user data from LDAP

### LDAPSync Utility

**Methods:**
- `sync_all_users(ldap_config)`: Sync all users from LDAP directory
- `test_connection(ldap_config)`: Test LDAP server connection

---

## Migration from Other Systems

### From Manual User Management

1. Configure LDAP settings
2. Test connection and login
3. Run full user sync
4. Verify all users imported correctly
5. Enable LDAP authentication
6. Communicate change to users

### From Other LDAP Systems

1. Export current LDAP configuration
2. Map field names to new system
3. Import configuration
4. Test with sample users
5. Full migration during maintenance window

---

## Support

For issues or questions:

1. Check troubleshooting section
2. Review debug logs
3. Consult Django and ldap3 documentation
4. Contact your IT administrator for LDAP-specific questions

---

## Changelog

### Version 1.0 (Initial Release)
- Comprehensive LDAP/AD authentication
- User synchronization
- Field mapping for all user attributes
- Active Directory support
- Generic LDAP support
- TLS/SSL support
- Password caching
- Test tools (connection, login, sync)
- Admin interface
- Configuration management

---

## Related Documentation

- [User Management Guide](USER_GUIDE.md)
- [Administration Guide](administration.md)
- [Security Best Practices](best_practices.md)


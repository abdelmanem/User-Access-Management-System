# LDAP/Active Directory Integration

## Overview

The User Access Management System (UAMS) provides comprehensive LDAP/Active Directory integration for enterprise authentication and user synchronization. This allows organizations to:

- **Authenticate users** against corporate LDAP/AD servers
- **Automatically sync** user information from directory services
- **Map LDAP attributes** to user profile fields
- **Support both** Active Directory and generic LDAP servers
- **Cache passwords** locally for offline authentication

---

## Quick Start

### 1. Access Configuration

Navigate to **Application Settings** → **LDAP/Active Directory Integration** or directly to:

```
/accounts/ldap/configuration/
```

!!! note "Superuser Required"
    Only superusers can access and modify LDAP configuration.

### 2. Basic Configuration

| Setting | Example Value |
|---------|---------------|
| LDAP Enabled | ✓ Checked |
| Active Directory | ✓ Checked (for AD) |
| Cache Passwords | ✓ Recommended |
| LDAP Server | `ldap://dc.example.com:389` |
| Bind Username | `Administrator@example.com` |
| Bind Password | `••••••••` |
| Base DN | `DC=example,DC=com` |

### 3. Test & Sync

1. Click **Test Connection** to verify server connectivity
2. Click **Test Login** with actual user credentials
3. Click **Sync All Users** to import users

---

## Configuration Reference

### Server Settings

#### LDAP Integration Enabled
Toggle to enable/disable LDAP authentication system-wide.

#### Active Directory
Check this if connecting to a Microsoft Active Directory server. This enables AD-specific features like `userAccountControl` handling.

#### Cache LDAP Passwords
When enabled, user passwords are cached locally as secure hashes. This allows users to login even if the LDAP server is temporarily unavailable.

!!! warning "Security Note"
    Disabling password caching means users cannot login if LDAP is unreachable.

#### Active Directory Domain
Your AD domain name (e.g., `example.com`). Often matches your email domain.

---

### TLS/SSL Configuration

#### LDAP Server URL

Format: `protocol://hostname:port`

| Protocol | Port | Description |
|----------|------|-------------|
| `ldap://` | 389 | Unencrypted (use with STARTTLS) |
| `ldaps://` | 636 | SSL/TLS encrypted |

**Examples:**
```
ldap://dc.example.com:389
ldaps://dc.example.com:636
```

#### Use TLS (STARTTLS)
Enable STARTTLS encryption on standard LDAP port (389).

#### Allow Invalid SSL Certificate
For self-signed certificates in development/testing environments.

!!! danger "Production Warning"
    Never enable this in production. Use proper certificates.

#### Client TLS Certificate/Key
Required for Google Workspace Secure LDAP and some enterprise configurations.

---

### Bind Settings

#### Bind Username

The service account used to connect to LDAP. Supported formats:

| Format | Example |
|--------|---------|
| User Principal Name (UPN) | `serviceaccount@example.com` |
| Distinguished Name (DN) | `CN=ServiceAccount,CN=Users,DC=example,DC=com` |
| Domain\Username | `EXAMPLE\serviceaccount` |

!!! tip "Best Practice"
    Use a dedicated service account with minimal read-only permissions, not an administrator account.

#### Bind Password
Password for the bind account.

#### Base Bind DN
The starting point for LDAP searches.

**Examples:**
```
DC=example,DC=com                    # Search entire domain
OU=Users,DC=example,DC=com           # Search specific OU
OU=Employees,OU=Users,DC=example,DC=com  # Nested OU
```

---

### Search and Authentication

#### LDAP Filter
Filter to identify user objects during sync.

**Active Directory:**
```
(&(objectClass=user)(objectCategory=person))
```

**OpenLDAP:**
```
(objectClass=inetOrgPerson)
```

**Exclude disabled accounts (AD):**
```
(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))
```

#### LDAP Authentication Query
Custom query for authentication (optional). Leave blank for default behavior.

#### Default Permission Group
Automatically assign new LDAP users to a Django permission group.

---

## Field Mapping

### Overview

LDAP attributes are mapped to user profile fields during sync. Use **lowercase** field names for Active Directory compatibility.

### Basic Fields

| User Field | AD Attribute | OpenLDAP | Description |
|------------|--------------|----------|-------------|
| Username | `samaccountname` | `uid` | Login username |
| First Name | `givenname` | `givenName` | User's first name |
| Last Name | `sn` | `sn` | User's surname |
| Display Name | `displayname` | `displayName` | Full display name |
| Email | `mail` | `mail` | Email address |

### Extended Fields

| User Field | AD Attribute | Description |
|------------|--------------|-------------|
| Department | `department` | Auto-creates department |
| Position/Job Title | `title` | Job position |
| Description | `description` | User description |
| Phone | `telephonenumber` | Primary phone |
| Mobile | `mobile` | Mobile phone |
| Office Location | `physicaldeliveryofficename` | Office/building |
| Company | `company` | Stored in notes |
| Employee Number | `employeenumber` | Stored in notes |

### Address Fields

| User Field | AD Attribute | Description |
|------------|--------------|-------------|
| Address | `streetaddress` | Street address |
| City | `l` | City/locality |
| State | `st` | State/province |
| Postal Code | `postalcode` | ZIP/postal code |
| Country | `co` | Country name |

### System Fields

| User Field | AD Attribute | Description |
|------------|--------------|-------------|
| Distinguished Name | `distinguishedname` | Full AD path |
| Active Status | `useraccountcontrol` | Account enabled/disabled |
| AD Synced | (auto) | Marks user as synced |
| Last AD Sync | (auto) | Sync timestamp |

---

## Active Flag Settings

### userAccountControl (Active Directory)

For AD, the `userAccountControl` attribute determines account status:

| Value | Meaning |
|-------|---------|
| 512 | Normal active account |
| 514 | Disabled account |
| 544 | Active, password not required |
| 546 | Disabled, password not required |

The system automatically checks bit 2 (value 2) to determine if an account is disabled.

### Invert Active Flag

When enabled, inverts the logic:
- Normal: `0` or `false` = inactive
- Inverted: `0` or `false` = active

---

## Testing

### Test Connection

Verifies:
- Server is reachable
- Bind credentials are correct
- TLS/SSL configuration works

**Success:**
```
✓ LDAP connection successful
```

**Failure:**
```
✗ Connection failed: [error details]
```

### Test Login

Tests actual user authentication:

1. Enter valid LDAP username
2. Enter user's password
3. Click Test Login

**Success:**
```
✓ LDAP login successful for user: jdoe (John Doe)
```

### User Sync

Imports all users from LDAP:

```
✓ Synced 150 users successfully, 0 errors
```

!!! note "Sync Behavior"
    - Creates new users automatically
    - Updates existing user information
    - Skips computer accounts (ending with `$`)
    - Skips system accounts (krbtgt, guest)
    - Auto-creates departments from AD

---

## Configuration Examples

### Active Directory (Standard)

```yaml
LDAP Enabled: ✓
Active Directory: ✓
Cache Passwords: ✓

Server: ldap://dc.corp.example.com:389
Use TLS: ✓
Bind Username: svc-ldap@corp.example.com
Bind Password: ********
Base DN: DC=corp,DC=example,DC=com

Filter: (&(objectClass=user)(objectCategory=person))
Username Field: samaccountname
Email Field: mail
```

### Active Directory (LDAPS)

```yaml
Server: ldaps://dc.corp.example.com:636
Use TLS: ✗ (already using LDAPS)
Allow Invalid SSL: ✗
```

### OpenLDAP

```yaml
LDAP Enabled: ✓
Active Directory: ✗
Cache Passwords: ✓

Server: ldap://ldap.example.com:389
Use TLS: ✓
Bind Username: cn=admin,dc=example,dc=com
Bind Password: ********
Base DN: ou=users,dc=example,dc=com

Filter: (objectClass=inetOrgPerson)
Username Field: uid
Email Field: mail
```

### Google Workspace Secure LDAP

```yaml
Server: ldaps://ldap.google.com:636
Client TLS Certificate: [From Google Admin Console]
Client TLS Key: [From Google Admin Console]
Bind Username: [Service account]
Base DN: dc=example,dc=com
Filter: (objectClass=user)
```

---

## Troubleshooting

### Connection Issues

| Error | Cause | Solution |
|-------|-------|----------|
| Connection refused | Server unreachable | Check hostname, port, firewall |
| Invalid credentials | Wrong bind password | Verify credentials |
| Certificate error | SSL/TLS issue | Check certificate, try Allow Invalid SSL |

### Sync Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| 0 users synced | Empty filter | Set filter to `(&(objectClass=user)(objectCategory=person))` |
| Missing fields | Case sensitivity | Use lowercase field names |
| Users not found | Wrong Base DN | Verify Base DN includes user containers |

### Authentication Issues

| Error | Cause | Solution |
|-------|-------|----------|
| User not found | Filter too restrictive | Broaden LDAP filter |
| Invalid password | Cached password mismatch | Re-sync user or reset password |
| Account disabled | AD account disabled | Check userAccountControl |

### Diagnostic Commands

Run on server to diagnose issues:

```bash
# Check configuration
python check_ldap_config.py

# Test LDAP search
python test_ldap_search.py

# Manual sync
python -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()
from accounts.ldap_backend import LDAPSync
print(LDAPSync.sync_all_users())
"
```

---

## Security Best Practices

### Service Account

- Use dedicated service account, not administrator
- Grant minimal read-only permissions
- Rotate credentials regularly
- Monitor account usage

### Connection Security

- Always use TLS/SSL in production
- Use LDAPS (port 636) or STARTTLS
- Never allow invalid certificates in production
- Use certificate pinning if possible

### Password Handling

- Enable password caching for availability
- Passwords stored as Django hashes (bcrypt/PBKDF2)
- Never store plaintext passwords
- Implement password policies

### Access Control

- Restrict LDAP configuration to superusers
- Audit configuration changes
- Monitor sync operations
- Log authentication attempts

---

## Integration with Application Settings

The LDAP configuration is integrated into the **Application Settings** page for centralized management:

1. Navigate to **Dashboard** → **Application Settings**
2. Find the **LDAP/Active Directory Integration** card
3. View status and quick actions
4. Click **Manage LDAP Configuration** for full settings

### Status Indicators

| Status | Meaning |
|--------|---------|
| ✅ Active | LDAP enabled and configured |
| ⚪ Inactive | LDAP disabled |
| ⚠️ Not Configured | No configuration exists |

---

## API Reference

### Models

#### LDAPConfiguration

Located in `accounts/models.py`

```python
from accounts.models import LDAPConfiguration

# Get active configuration
config = LDAPConfiguration.get_active_config()

# Check if enabled
if config and config.ldap_enabled:
    print(f"LDAP Server: {config.ldap_server}")
```

### Backend

#### LDAPAuthenticationBackend

Located in `accounts/ldap_backend.py`

```python
from accounts.ldap_backend import LDAPAuthenticationBackend

backend = LDAPAuthenticationBackend()
user = backend.authenticate(request, username='jdoe', password='secret')
```

#### LDAPSync

```python
from accounts.ldap_backend import LDAPSync

# Test connection
result = LDAPSync.test_connection(config)
print(result['message'])

# Sync all users
result = LDAPSync.sync_all_users()
print(f"Synced: {result['synced_count']}")
```

---

## URLs

| URL | Description |
|-----|-------------|
| `/accounts/ldap/configuration/` | Main configuration page |
| `/accounts/ldap/test-connection/` | Test connection endpoint |
| `/accounts/ldap/test-login/` | Test login endpoint |
| `/accounts/ldap/sync-users/` | Sync users endpoint |
| `/dashboard/settings/application/` | Application settings (includes LDAP card) |

---

## Requirements

### Python Packages

```
ldap3==2.9.1
pyasn1==0.6.0
```

### Network Requirements

- Access to LDAP server (port 389 or 636)
- DNS resolution for LDAP hostname
- Firewall rules allowing LDAP traffic

### Active Directory Requirements

- Service account with read permissions
- Access to user containers/OUs
- Proper Base DN configuration

---

## Changelog

### Version 1.0

- Initial LDAP/AD integration
- Support for Active Directory and OpenLDAP
- Comprehensive field mapping (35+ fields)
- TLS/SSL support
- Password caching
- User synchronization
- Test tools
- Application Settings integration

---

## Related Documentation

- [Administration Guide](administration.md)
- [Application Settings](application_settings.md)
- [Security Best Practices](best_practices.md)
- [User Guide](USER_GUIDE.md)

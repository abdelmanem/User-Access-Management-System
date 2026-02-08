# Quick Reference - Custom LDAP Sync Field Selection

## What's New?
Two new LDAP sync pages where admins can select which specific fields to sync:
- User field selection sync
- Computer/hardware field selection sync

## How to Access

### From LDAP Configuration Page (Settings → LDAP/AD Configuration):
1. Scroll to **"Custom Field Selection Sync"** section
2. Click **"Configure & Sync Users"** or **"Configure & Sync Computers"**

## Quick Steps

### To Sync Users with Field Selection:
1. Click "Configure & Sync Users"
2. Check the fields you want to sync
3. Enter LDAP password
4. Click "Start Sync"

### To Sync Computers with Field Selection:
1. Click "Configure & Sync Computers"
2. Check the fields you want to sync
3. Enter LDAP password
4. Click "Start Sync"

## Available User Fields (11 total)
- ☑ First Name
- ☑ Last Name
- ☑ Email
- ☑ Phone
- ☑ Mobile
- ☑ Job Title
- ☑ Employee ID
- ☑ Department
- ☑ Active Status
- ☑ Display Name
- ☑ Other supporting fields

## Available Computer Fields (10 total)
- ☑ Computer Name
- ☑ Hardware Type
- ☑ Operating System
- ☑ OS Version
- ☑ IP Address
- ☑ DNS Hostname
- ☑ Location
- ☑ Enabled Status
- ☑ Description
- ☑ Asset Tag

## Key Features

✨ **Granular Control**: Choose exactly which fields to sync
✨ **Organized UI**: Fields grouped by category (Basic Info, Employment, etc.)
✨ **Secure**: Password never stored, used only for sync
✨ **Safe**: Only selected fields are updated; others remain unchanged
✨ **Protected**: Works with per-asset sync disable toggle
✨ **Reversible**: Easy to disable sync for specific records

## Common Scenarios

| Scenario | Fields to Select |
|----------|------------------|
| Monthly HR updates | Job Title, Department, Active Status |
| Quarterly inventory | Hardware Type, OS, Location, Enabled Status |
| Initial setup | SELECT ALL |
| Contact info only | Phone, Mobile, Email |
| Location updates | Office Location, City, State, Country |
| New employee | All fields |

## Protection Features

### Asset-Level (Per Record)
- Each user/computer has "Enable LDAP Sync" toggle
- Disabled = never syncs, regardless of field selection

### Field-Level (This Feature)
- Choose which fields sync in bulk operations
- Unselected fields never update

### Combined Effect
- Dual protection against unwanted data changes
- Maximum admin control and flexibility

## Workflow

```
Admin → Opens LDAP Config
      → Clicks custom sync button
      → Selects desired fields ✓
      → Enters LDAP password
      → Clicks "Start Sync"
      ↓
Backend → Connects to LDAP
        → Fetches data
        → Updates ONLY selected fields
        → Skips disabled records
        ↓
Result → Success/error message
      → Returns to LDAP config
      → Admins review results
```

## Important Notes

⚠️ **Password**: Never stored, used only for this sync session
⚠️ **Scope**: Only affects records with sync enabled
⚠️ **Fields**: Unselected fields keep existing values
⚠️ **New Records**: Created even if not all fields selected
⚠️ **Error Handling**: Graceful error messages with logging

## URLs

- User sync: `/accounts/ldap/sync-user-fields/`
- Computer sync: `/accounts/ldap/sync-computer-fields/`

## Permissions Required
- Superuser status required
- LDAP must be configured first
- Valid LDAP credentials needed for sync

## Documentation
- Technical: `CUSTOM_LDAP_SYNC_IMPLEMENTATION.md`
- User Guide: `CUSTOM_LDAP_SYNC_USER_GUIDE.md`
- Summary: `LDAP_SYNC_FIELD_SELECTION_SUMMARY.md`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Page not found | Ensure URLs are configured correctly |
| No LDAP config | Set up LDAP in Settings first |
| Password error | Verify LDAP bind credentials |
| No sync occurred | Check if asset has sync enabled |
| Fields unchanged | Verify you selected the fields |

## Files Involved

**Templates:**
- `ldap_sync_user_fields.html` - User field selection form
- `ldap_sync_computer_fields.html` - Computer field selection form

**Views:**
- `ldap_sync_user_fields()` - User sync handler
- `ldap_sync_computer_fields()` - Computer sync handler

**Forms:**
- `LDAPSyncFieldSelectionForm` - User field selection form
- `LDAPSyncComputerFieldSelectionForm` - Computer field selection form

**Backend:**
- `LDAPSync.sync_all_users()` - Enhanced with field filtering
- `LDAPComputerSync.sync_all_computers()` - Enhanced with field filtering
- `_update_user_from_ldap()` - Field-level update logic

**URLs:**
- `path('ldap/sync-user-fields/', ...)` - User sync page
- `path('ldap/sync-computer-fields/', ...)` - Computer sync page

## Status
✅ **COMPLETE AND READY FOR USE**

All components implemented, tested, and integrated.

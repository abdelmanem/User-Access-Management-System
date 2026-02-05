# Custom LDAP Sync Field Selection - User Guide

## Overview
This guide explains how to use the custom LDAP sync feature to select which specific fields should be synced from your LDAP/AD directory.

## Accessing the Feature

### From the Dashboard
1. Log in as an administrator
2. Navigate to **Settings** → **LDAP/AD Configuration**
3. Scroll down to the **"Custom Field Selection Sync"** section
4. Choose either:
   - **"Configure & Sync Users"** - to sync specific user fields
   - **"Configure & Sync Computers"** - to sync specific computer/hardware fields

## Syncing Users with Field Selection

### Step 1: Access User Field Selection Page
- Click the **"Configure & Sync Users"** button
- You'll see a form with all available user fields organized into categories

### Step 2: Select Fields to Sync
The form is organized into these sections:

| Section | Fields |
|---------|--------|
| **Critical Fields** ⚠️ | Username (required for sync) |
| **Basic Information** | First Name, Last Name, Email, Display Name |
| **Employment Information** | Employee ID, Department, Job Title |
| **Contact Information** | Phone, Mobile |
| **Location Information** | Office Location, Address, City, State, Country |
| **Account Status** | Active Status |

**How to Select:**
- Check the checkboxes next to fields you want to sync
- Unchecked fields will NOT be updated during sync
- Fields left unchecked keep their existing values in the system

### Step 3: Enter LDAP Credentials
- Scroll down to **"LDAP Credentials"** section
- Enter your LDAP bind password
- Note: This password is used ONLY for this sync and is NOT stored

### Step 4: Review Configuration
- The right sidebar shows your active LDAP configuration:
  - Server address
  - LDAP Type (Active Directory or Generic LDAP)
  - Base DN
- The "Sync Protection" info box explains asset-level sync disabling

### Step 5: Start Sync
- Click the **"Start Sync"** button
- The system will:
  1. Connect to your LDAP server
  2. Fetch user data from LDAP
  3. Update ONLY the selected fields
  4. Skip users with sync disabled
  5. Display results and return to configuration page

### Example: Sync Only Contact Information
1. Go to field selection page
2. Scroll to **Contact Information** section
3. Check only: ☑️ Phone, ☑️ Mobile
4. Uncheck all other fields
5. Enter password
6. Click "Start Sync"
7. **Result**: Phone and mobile numbers updated; all other fields remain unchanged

## Syncing Computers with Field Selection

### Step 1: Access Computer Field Selection Page
- Click the **"Configure & Sync Computers"** button
- You'll see a form with all available computer/hardware fields

### Step 2: Select Computer Fields to Sync
The form is organized into these sections:

| Section | Fields |
|---------|--------|
| **Critical Fields** ⚠️ | Computer Name (required for sync) |
| **Hardware Information** | Hardware Type, Asset Tag |
| **Operating System** | Operating System, OS Version |
| **Network Information** | IP Address, DNS Hostname |
| **Location & Status** | Location, Enabled Status, Description |

**How to Select:**
- Check the checkboxes next to fields you want to sync
- Unchecked fields will NOT be updated during sync
- Existing values remain unchanged for unselected fields

### Step 3: Enter LDAP Credentials
- Scroll to **"LDAP Credentials"** section
- Enter your LDAP bind password
- Password is used only for this sync session

### Step 4: Start Sync
- Click **"Start Sync"** button
- System will:
  1. Connect to LDAP/AD
  2. Fetch computer object data
  3. Update hardware assets with ONLY selected fields
  4. Skip computers with sync disabled (is_sync_enabled=False)
  5. Create new hardware assets if computer doesn't exist
  6. Display results

### Example: Update Only OS Information
1. Go to computer field selection page
2. Check only: ☑️ Operating System, ☑️ OS Version
3. Uncheck all other fields
4. Enter password
5. Click "Start Sync"
6. **Result**: OS and version updated; hardware type, location, etc. unchanged

## Understanding Sync Protection

### Asset-Level Control (is_sync_enabled)
- Each hardware asset has an **"Enable LDAP Sync"** toggle
- When disabled (🔴), the asset is NEVER synced, regardless of field selection
- When enabled (🟢), field selection determines what gets updated

### Field-Level Control (This Feature)
- Even with sync enabled, only SELECTED fields are updated
- Provides granular control over what data changes

### Combined Protection
```
Asset Sync    | Field Selected | Result
------------+----------------+--------
Disabled     | Yes            | NOT synced
Disabled     | No             | NOT synced
Enabled      | Yes            | SYNCED ✓
Enabled      | No             | NOT synced
```

## Common Use Cases

### 1. Update Employee Information Only
- Sync every month to update job titles and departments
- Select: Job Title, Department, Employee ID, Active Status
- Other fields remain manual
- **Benefit**: Keep phone numbers and addresses manual

### 2. Refresh Hardware Inventory
- Sync computers to update inventory status
- Select: Hardware Type, Operating System, Enabled Status
- **Benefit**: Auto-detect new/retired computers without overwriting manual notes

### 3: New Company with Legacy Data
- Initial full sync of all fields
- Select: ALL fields ✓
- **Benefit**: Complete import of LDAP data

### 4: Disable Sync for Specific Records
- Use per-asset "Enable LDAP Sync" toggle for exceptions
- Some users manually managed, others auto-sync
- **Benefit**: Mix automated and manual management

## Troubleshooting

### Issue: "LDAP is not configured"
- **Solution**: Go to LDAP Configuration page and configure LDAP settings first
- Ensure server address, bind username, and base DN are set

### Issue: "Bind password is required"
- **Solution**: Enter password in the LDAP Credentials field before syncing

### Issue: No fields were selected
- **Solution**: Check at least one field before clicking "Start Sync"

### Issue: Sync succeeded but data didn't change
- **Check**: Were the fields you selected actually checked? ✓
- **Check**: Is the asset's "Enable LDAP Sync" toggle turned ON? (for computers)
- **Solution**: Review LDAP configuration to ensure data is available

### Issue: Need to disable sync for specific users/computers
- Go to user/computer detail page
- Look for **"Enable LDAP Sync"** checkbox
- Uncheck to disable sync for that record
- That record will be skipped even if sync is run

## Best Practices

✅ **Test First**: Test with a small field selection before syncing all fields
✅ **Review Results**: Always check the sync results message
✅ **Document Changes**: Note which fields you're syncing for consistency
✅ **Regular Backups**: Back up user/computer data before major syncs
✅ **Staged Rollout**: Sync one department at a time if needed
✅ **Disable Manual Fields**: If syncing, don't manually edit those same fields
✅ **Monitor Logs**: Check application logs for detailed sync information

## Security Notes

🔒 **Password Safety**
- LDAP bind password is NEVER stored
- Used only for this sync session
- Not visible after entering
- Session is cleared after sync completes

🔒 **Access Control**
- Only administrators can access this feature
- Superuser authentication required
- All actions are logged

🔒 **Data Protection**
- Only selected fields are updated
- Manual edits protected from accidental overwrites
- Asset-level sync toggle prevents bulk unwanted changes

## Questions & Support

For additional help:
- Check the LDAP Configuration help section (on configuration page)
- Review asset details to see sync status per record
- Check application logs for detailed sync information
- Contact your system administrator

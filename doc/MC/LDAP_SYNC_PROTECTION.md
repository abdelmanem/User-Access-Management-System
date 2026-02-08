# LDAP Sync Protection - User Guide

## Problem Solved
Previously, when you ran LDAP sync for computers, it would overwrite ALL manual changes made in the UI. For example, if you changed a computer's type from "Desktop PC" to "Laptop", the next sync would revert it back to "Desktop PC".

## Solution
A new **"Enable LDAP Sync"** toggle has been added to each hardware asset that allows you to:
- **Enable (default)**: LDAP sync will update this asset's fields automatically
- **Disable**: LDAP sync will skip this asset entirely, allowing you to manually manage it

## How to Use

### Option 1: Protect Specific Assets
If you want to make manual edits to a specific asset and prevent LDAP sync from overwriting them:

1. Go to **Hardware Inventory**
2. Click **Edit** on the asset you want to protect
3. Under the **Ownership & Relations** tab, scroll down to find **"Enable LDAP Sync"**
4. **Uncheck** the box to disable LDAP sync for this asset
5. Click **Save Hardware**

Now when you run LDAP sync, this asset will be skipped and your manual edits will be preserved.

### Option 2: Re-enable Sync Later
If you want LDAP sync to resume controlling an asset:

1. Go to **Hardware Inventory** → **Edit** the asset
2. Check the **"Enable LDAP Sync"** box
3. Click **Save Hardware**

The next LDAP sync will update this asset again.

### Viewing Sync Status
In the asset's detail page, you'll see a badge showing the LDAP sync status:
- **"LDAP Sync: Enabled"** (blue) - Sync will update this asset
- **"LDAP Sync: Disabled (Manual)"** (orange) - Sync is disabled; asset is manually managed

## Recommendation
For assets that require manual customization (e.g., assets with custom hardware types not derived from LDAP):
1. Edit the asset and make your changes
2. Disable LDAP Sync to protect it
3. You can always re-enable sync later if LDAP is the source of truth

## LDAP Sync Behavior
- **New assets**: Created automatically with LDAP Sync enabled by default
- **Existing assets with sync enabled**: Updated with latest LDAP data
- **Existing assets with sync disabled**: Skipped during sync (not updated)

## Detailed Changes
- Added `is_sync_enabled` Boolean field (default: True) to HardwareAsset model
- Updated LDAP sync logic to check `is_sync_enabled` before updating existing assets
- Form and detail views updated to show/manage this setting

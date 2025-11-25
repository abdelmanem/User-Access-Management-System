---
title: Application Settings Console
---

## Overview

The **Application Settings** console is a restricted administration page designed for **system administrators and superusers**.  
It centralizes high‑impact configuration and maintenance actions for the User Access Management System (UAMS).

This page is intentionally **not** visible to regular users. It appears in the left sidebar only when the logged‑in account is a Django superuser or staff user.

Use it for:

- **Active Directory (AD) integration** metadata
- **Database purge / retention** for access‑history/audit data
- **System seeding utilities** for default accounts and templates
- A reserved **“future settings”** space where new toggles can be added without schema changes

> ⚠️ **Caution**  
> All changes on this page are global. Review your organization’s policies before enabling sync or purging data.

---

## Access & Permissions

- **Who can see it?**
  - Django **superusers** (`is_superuser=True`)
  - Django **staff/admin users** (`is_staff=True`)
- **Where is it?**
  - Sidebar entry: **Application Settings**
  - URL (default): `/dashboard/settings/application/`

If you do not see the menu item:

1. Confirm your account is marked as `staff` or `superuser` in Django admin.
2. Confirm you are logged in through the normal UAMS UI (not just browsing static docs).

---

## Page Layout

The console is divided into four main areas:

1. **Status Cards** (top row)
2. **Active Directory Integration** (left panel)
3. **Database Maintenance / Purge** (right panel)
4. **System Seed Utilities & Future Settings** (bottom row)

### 1. Status Cards

The top of the page shows three quick‑glance cards:

- **Directory Sync**
  - Shows whether AD integration is **Enabled** or **Disabled**
  - Last sync timestamp (if tracked)
  - Configured sync frequency (e.g. Daily)

- **Audit Trail Retention**
  - Current retention window in **days**
  - Time of the **last purge job**
  - Number of **rows removed** in the last purge

- **Seeding Jobs**
  - Number of **created** default account/ template rows in the last run
  - Last scope used (template catalog vs system defaults)
  - Last run timestamp

These cards are read‑only summaries pulled from underlying application settings.

---

## Active Directory Integration

The **Active Directory Integration** card manages metadata for future or existing AD sync jobs.

### Fields

- **Enable directory sync**
  - Toggles AD sync **on/off** at the configuration level.
  - When off, schedulers or external jobs *should* respect this and skip sync.

- **Domain Controller**
  - Hostname or IP address of the preferred Domain Controller.
  - Example: `dc01.corp.example.com`

- **Base DN**
  - LDAP base distinguished name used for queries.
  - Example: `DC=corp,DC=example,DC=com`

- **Service Account**
  - Username (or identifier) of the account used to bind to AD.
  - **Password is not stored here**; keep credentials in your secret manager or vault.

- **Sync Frequency**
  - Controls how often a scheduled job *should* run:
    - `Hourly`
    - `Daily` (default)
    - `Weekly`

> ℹ️ **Note**  
> This page stores sync configuration; the actual job (Celery/cron/other) must be wired to respect these settings.

### How to Update

1. Adjust the fields under **Active Directory Integration**.
2. Click **Save Settings**.
3. A confirmation message appears if the save succeeds.

The system records:

- `enabled` flag and connection metadata
- **Last updated** timestamp
- Optional last sync status text (if updated by your sync job)

---

## Database Maintenance (Purge)

The **Database Maintenance** section manages how long audit and access‑history data is retained.

> ⚠️ **Irreversible Operation**  
> Purging removes rows from the database and cannot be undone. Take a backup and validate your retention policy before running.

### Fields

- **Retention Window (days)**
  - Integer between **30** and **3650** days (1 month up to ~10 years).
  - The purge job deletes `AccessHistory` records **older** than this value.

- **I understand this permanently removes historical data**
  - Required confirmation checkbox to avoid accidental clicks.

### How Purge Works

When you click **Run Purge Job**:

1. The system validates the retention window and confirmation checkbox.
2. It computes a cutoff date:  
   `cutoff = now - retention_days`
3. All `AccessHistory` rows with `accessed_at < cutoff` are deleted.
4. The setting is updated with:
   - `retention_days`
   - `last_run` timestamp
   - `last_deleted` count
5. A success message displays how many rows were removed.

### Recommended Practices

- Start with a higher retention (e.g. 730 days / 2 years).
- Run purge in a **staging** environment first and validate:
  - Compliance reporting impact
  - Storage/backup impact
- Align retention with:
  - Internal audit requirements
  - Regulatory guidance (e.g., PCI, local law)

---

## System Seed Utilities

The **System Seed Utilities** panel lets you (re)run default‑data seeders shipped with UAMS—primarily for **Default Accounts**.

It integrates with existing services such as:

- `default_accounts.services.ensure_default_account_templates_seeded`
- `default_accounts.services.create_default_accounts_for_system`

### Seed Scope

- **Template Catalog**
  - Ensures the default account **template catalog** exists.
  - If templates are missing, they are created from built‑in fallback data.
  - Safe to run multiple times; existing templates are left intact.

- **Specific System Defaults**
  - Seeds `DefaultAccount` rows for a **single system** based on templates.
  - Skips any default accounts that already exist for that system.

### Target System

- Dropdown listing systems by name.
- **Required** when scope is **Specific System Defaults**.

### Running a Seeding Task

1. Choose **Seed Scope**:
   - `Template Catalog` or `Specific System Defaults`
2. If seeding a specific system, pick **Target System** from the dropdown.
3. Click **Run Seeding Task**.

After completion, the **Last Result** section shows:

- Last scope used
- Target system (if any)
- Number **created**
- Number **skipped**
- Last run timestamp

---

## Future Settings Placeholder

The last card is a **Future Settings** placeholder wired to a generic `ApplicationSetting` record.

Use this section to:

- Park upcoming toggles or flags you expect to add later.
- Document roadmap items for other admins.

Developers can:

- Register a new key in the `ApplicationSetting` defaults.
- Extend the Application Settings page template to surface new controls.

This pattern allows new global settings to be added **without extra database migrations**.

---

## Troubleshooting

**I don’t see Application Settings in the sidebar**

- Confirm your account:
  - Is authenticated
  - Has `is_staff` or `is_superuser` set to `True`

**Purge job ran but the counts look wrong**

- Verify the retention days you entered.
- Check that your database clock/time zone is correct.
- Review backups before re‑running with a more aggressive window.

**Seeding created fewer rows than expected**

- The seeding logic skips accounts that already exist for the system.
- Verify the templates in the **Default Accounts** template registry.

If issues persist, capture logs and database snapshots and contact the development/operations team for assistance.



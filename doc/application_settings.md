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

---

## Server Requirements (Ubuntu)

You do **not** need a separate “AD sync app” installed on the server, but your Ubuntu host running UAMS must have:

- A working **Python environment** for your Django project (already required by UAMS).
- Optional but recommended **LDAP / AD client libraries** if you plan to talk to AD directly from Django, for example:
  - System packages:
    - `sudo apt update`
    - `sudo apt install -y libsasl2-dev python3-dev libldap2-dev libssl-dev`
  - Python packages (add to your `requirements.txt` if using them):
    - `ldap3` (pure Python LDAP client), or
    - `django-auth-ldap` (Django integration helper)

If you use Microsoft Graph / REST APIs instead of LDAP, you’ll typically just need `requests` / `msal` in your Python env rather than the LDAP system libraries above.

---

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
  - **Password is not stored here**; keep credentials in your enterprise **secret manager** or **vault** (for example: Azure Key Vault, AWS Secrets Manager, HashiCorp Vault, or another secure store managed by your infra team). The UAMS application or background worker should read those secrets at runtime instead of saving them in this settings page or in the database.

- **Sync Frequency**
  - Controls how often a scheduled job *should* run:
    - `Hourly`
    - `Daily` (default)
    - `Weekly`

> ℹ️ **How the sync actually runs**  
> This page only stores configuration (enabled flag, domain, base DN, etc.). The *real* sync work is done by a **background job** such as Celery, a cron job, or another scheduler. That process should:
> - Read AD connection details and credentials from your secret manager  
> - Respect the `enabled` flag and `sync_frequency` set here  
> - Update the `last_sync` / `last_status` fields when it completes

### Manual Sync Button

If you need to trigger a sync outside the normal schedule, the page includes a **Run Manual AD Sync** button:

- Available only when **Enable directory sync** is turned on.
- Intended to be wired into the same underlying sync routine your scheduler uses.
- The current implementation records a manual sync request timestamp and status; you can extend the underlying sync function to perform a full AD import/update when this button is pressed.

---

## Handling the AD Password Securely

**Goal:** never store the AD bind password in plain text in:

- Django settings
- The UAMS database
- Logs or environment dumps

Typical patterns on Ubuntu:

- **Environment variables + external secret store**
  - Your deploy tool (Ansible, Kubernetes, systemd drop‑in, etc.) injects the password as an env var at runtime:
    - Example: `AD_BIND_PASSWORD` set via systemd unit, Docker secret, or Kubernetes secret.
  - Your sync code reads `os.environ["AD_BIND_PASSWORD"]` directly, never saving it to the DB.

- **Secret manager / vault**
  - Use a library/SDK to retrieve secrets from:
    - Azure Key Vault, AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault.
  - The sync function:
    1. Reads connection metadata (domain, base DN, service account) from **Application Settings**.
    2. Fetches the **password** from the vault.
    3. Connects to AD and performs the sync.

> ✅ **Best practice**  
> Treat the AD password like any other production secret: rotate regularly, restrict who can read it, and never paste it into the Application Settings UI.

---

## Creating Sync Jobs on Ubuntu

The Application Settings page exposes configuration. On Ubuntu, you still need something that **runs the sync code** on a schedule. Common options:

### Option 1: Cron + Management Command

1. Implement a Django **management command** (example name):  
   `python manage.py run_ad_sync`
2. On the server, edit the crontab for the service user:

```bash
crontab -e
```

3. Add a job that runs, for example, every day at 01:00:

```bash
0 1 * * * /usr/bin/bash -lc 'cd /opt/uams && source venv/bin/activate && python manage.py run_ad_sync >> /var/log/uams/ad_sync.log 2>&1'
```

Inside `run_ad_sync`, your code should:

- Read the **Application Settings** values (enabled flag, frequency, etc.).
- Decide whether to run based on those settings.
- Read the password from env/secret manager.
- Execute the AD synchronization logic.
- Update `last_sync` and `last_status` in the Application Settings record.

### Option 2: systemd Service + Timer

For more control than cron, use a **systemd timer**:

1. Create a unit file, e.g. `/etc/systemd/system/uams-ad-sync.service`:

```ini
[Unit]
Description=UAMS Active Directory Sync

[Service]
Type=oneshot
WorkingDirectory=/opt/uams
Environment="DJANGO_SETTINGS_MODULE=user_access_management.settings"
ExecStart=/usr/bin/bash -lc 'source venv/bin/activate && python manage.py run_ad_sync'
```

2. Create a timer file, e.g. `/etc/systemd/system/uams-ad-sync.timer`:

```ini
[Unit]
Description=Run UAMS AD sync periodically

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

3. Enable and start the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now uams-ad-sync.timer
```

This will run `run_ad_sync` daily; the command itself should still respect the **enabled** flag and **frequency** stored in the Application Settings page.

### Option 3: Celery Beat (if you already use Celery)

If your deployment uses **Celery**:

- Define a periodic task (e.g. `tasks.sync_active_directory`).
- Configure **Celery Beat** to run it on a schedule.
- Inside the task:
  - Read Application Settings for AD.
  - Check `enabled` / `sync_frequency`.
  - Call the same core sync function used by:
    - The periodic task
    - The **Run Manual AD Sync** button

---

## Summary

- You don’t need a separate Ubuntu “app” for AD sync; you need:
  - Python deps (and LDAP libs if using LDAP).
  - A **job runner** (cron, systemd timer, Celery beat, etc.).
- The **Application Settings** page holds configuration and shows status.
- Passwords belong in **secret managers** or controlled environments, not in the UI.
- Manual sync and scheduled jobs should both call the same sync routine and then update `last_sync`/`last_status` so admins can see what happened. 

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



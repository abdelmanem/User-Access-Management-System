# Service Account Governance & Rotation Alerts Guide

**Version:** 1.0  
**System:** User-Access-Management-System  
**Scope:** RHG / PCI Section 4.2 – Service / Privileged Account Password Requirements

---

## 1. Overview

This document describes how the User Access Management System implements tracking and evidence for **service and privileged accounts**, including:

- Governance and ownership tracking for service/privileged accounts.  
- Quarterly **attestation workflow** for account owners.  
- **Password rotation alerts** via scheduled job and email notifications.  
- Traceability to **change tickets, SOPs, and password storage locations**.  
- Pointers for **automated tests** that support audit defensibility.

The implementation lives primarily in the `service_accounts` Django app and `user_access_management/settings.py`.

---

## 2. Data Model Extensions (Service Accounts)

### 2.1 ServiceAccount – Governance Fields

`service_accounts/models.py`:

- **Privileged flag and admin linkage**
  - `is_privileged`: marks accounts that must be governed as privileged/admin.  
  - `admin_user`: links to the administrator (4.3) this account is associated with.

- **Traceability**
  - `change_request_id`: reference to the change ticket that created/modified the account.  
  - `sop_reference`: SOP ID/label covering usage and rotation of the account.  
  - `password_storage_location`: where the password is stored (vault/safe/password manager).

- **Attestation status**
  - `last_attested_at`: timestamp of the most recent owner attestation.  
  - `last_attested_by`: user who performed the latest attestation.  
  - `last_attestation_status`: `Confirmed`, `Pending Removal`, or `Unknown`.  
  - `last_attestation_notes`: notes/evidence captured during attestation.

- **Convenience properties**
  - `is_attestation_overdue`: `True` if the account is active and has never been attested or was last attested more than 90 days ago.  
  - `attestation_status_display`: friendly text describing the attestation state.

### 2.2 ServiceAccountAttestation – Attestation History

`service_accounts/models.py`:

- New model `ServiceAccountAttestation` capturing each review:
  - `service_account` – FK to `ServiceAccount`.  
  - `attested_at` – auto timestamp.  
  - `attested_by` – user who attested.  
  - `status` – `Confirmed`, `Pending Removal`, or `Unknown`.  
  - `storage_location` – password location as confirmed during the review.  
  - `notes` – free-text notes/evidence.

This provides a full historical trail of quarterly reviews for auditors.

---

## 3. Attestation Workflow (UI & Process)

### 3.1 Forms & Views

- **Form:** `ServiceAccountAttestationForm` (`service_accounts/forms.py`) exposes:
  - `status`, `storage_location`, `notes`.

- **View:** `service_account_attest` (`service_accounts/views.py`):
  - URL: `service_accounts:<int:pk>/attest/` (see `service_accounts/urls.py`).  
  - On `POST`, creates a `ServiceAccountAttestation` row and updates the parent `ServiceAccount`:
    - `last_attested_at`, `last_attested_by`, `last_attestation_status`, `last_attestation_notes`.  
    - Optionally updates `password_storage_location` if provided.

### 3.2 Templates

- **Attestation form:** `service_accounts/templates/service_accounts/service_account_attest.html`
  - Shows a compact form to record status, storage location, and notes.  
  - Provides a side panel summarising system, owner, privileged flag, expiry and current storage.

- **Detail view:** `service_accounts/templates/service_accounts/service_account_detail.html`
  - Displays:
    - **Privileged:** badge + linked admin user.  
    - **Change / SOP / Storage** table.  
    - **Latest Attestation** panel (status, date, attested by, notes).  
    - **Attestation History** table (recent attestations).
  - Includes an **“Attest”** button in the header that routes to the attestation form.

- **List view:** `service_accounts/templates/service_accounts/service_account_list.html`
  - Cards:
    - Total Accounts, Active, Compliant, Expired, **Privileged**, **Attestation Overdue**.
  - Filters:
    - `governance` filter with options:
      - `Privileged Only`  
      - `Attestation Overdue`  
      - `Missing Change/SOP/Storage`
  - Columns:
    - `Traceability` – shows Change ID, SOP, Storage and highlights missing values in red.  
    - `Last Attested` – date, status and an **Overdue** badge where applicable.  
    - Actions include view, update, **attest**, and delete.

### 3.3 How Owners Use It (Operational Steps)

1. Navigate to **Service Accounts** list.  
2. Filter by **Privileged Only** and/or **Attestation Overdue**.  
3. For each account:
   - Click **Attest** (clipboard icon).  
   - Choose **Status** (e.g. *Confirmed in Use*).  
   - Confirm **Password Storage Location** (vault/safe/manager).  
   - Enter **Notes/Evidence** (ticket IDs, screenshots, checks made).  
   - Submit the form.
4. Verify on the **Detail** screen:
   - The Latest Attestation panel is updated.  
   - Attestation History shows the new record.  
   - Traceability fields (Change/SOP/Storage) are correctly populated.

This process should be performed at least **quarterly** for all service and privileged accounts.

---

## 4. Password Rotation Alerts (Scheduled Job)

### 4.1 Management Command

`service_accounts/management/commands/check_service_account_rotation.py`:

- Command name: `check_service_account_rotation`.
- Arguments:
  - `--days N` – window in days for upcoming expirations (default `30`).  
  - `--recipient email@domain` – optional; can be specified multiple times. If omitted, falls back to `settings.ADMINS`.

Behaviour:

- Queries active `ServiceAccount` rows for:
  - **Expired** passwords (`password_expires_on < now`).  
  - **Expiring soon** passwords (`password_expires_on` in the next `N` days).
- Builds an email body listing:
  - Account name, system, owner, expiration/expired date.
- Sends the email via `django.core.mail.send_mail`:
  - `subject`: `[UAM] Service Account Password Alerts`  
  - `from_email`: `settings.DEFAULT_FROM_EMAIL` (with a fallback).  
  - `recipient_list`: all `--recipient` arguments or `settings.ADMINS`.
- If there are no recipients configured, it writes the message to stdout instead.

### 4.2 Email Settings

`user_access_management/settings.py`:

- **Backend**:

```python
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
```

For production, override via environment variables (e.g., SMTP backend).

- **From address**:

```python
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='no-reply@user-access-management.local')
```

- **Admins**:

```python
ADMINS = config(
    'ADMINS',
    default='IT Security <it.security@example.com>',
    cast=lambda v: [tuple(part.strip().rsplit(' ', 1)) for part in [v] if v],
)
```

For real deployments, set `EMAIL_BACKEND`, `DEFAULT_FROM_EMAIL`, and `ADMINS` via environment (e.g., `.env` or hosting configuration).

### 4.3 Manual Test of the Command

From the project root:

```bash
venv/Scripts/python.exe manage.py check_service_account_rotation --days 30 --recipient your.test@your-domain.com
```

Verify that:

- An email is sent to `your.test@your-domain.com` with the expected accounts listed.  
- Or, when using the console backend, the alert text appears in the terminal.

### 4.4 Scheduling on Windows (Task Scheduler)

Example daily schedule at 06:00 (run from an elevated PowerShell):

```powershell
$action = New-ScheduledTaskAction `
  -Execute "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" `
  -Argument "cd C:\trae\User-Access-Management-System; C:\trae\User-Access-Management-System\venv\Scripts\python.exe manage.py check_service_account_rotation --days 30 --recipient it.security@example.com"

$trigger = New-ScheduledTaskTrigger -Daily -At 06:00

Register-ScheduledTask -TaskName "UAMS_ServiceAccountRotationAlerts" -Action $action -Trigger $trigger -Description "Daily service account password rotation alerts"
```

Adjust the paths, time and recipients as needed for the environment.

---

## 5. Reporting & Exports

### 5.1 List View Dashboard

The main service account list exposes governance metrics:

- Cards:
  - **Total Accounts**, **Active**, **Compliant**, **Expired**, **Privileged**, **Attestation Overdue**.
- Filters:
  - System, account type, compliance status, governance, active/inactive.
- Columns:
  - `Traceability` – Change ID / SOP / Storage (with missing values highlighted).  
  - `Last Attested` – date, status, and an Overdue badge.  
  - Standard password expiry/compliance badges.

### 5.2 Excel Export

`export_service_accounts_to_excel` (`service_accounts/views.py`) includes:

- Privileged flag and linked admin user.  
- Purpose, owner.  
- Last password change and expiry.  
- Policy compliance fields.  
- `change_request_id`, `sop_reference`, `password_storage_location`.  
- Latest attestation date and status.  
- Active flag and overall compliance status.

This export can be stored as audit evidence for section 4.2.

---

## 6. Suggested Automated Tests

When extending or maintaining coverage, consider the following tests in `service_accounts/tests.py`:

### 6.1 Governance Filters

- `governance=privileged`: only returns `ServiceAccount` instances with `is_privileged=True`.  
- `governance=attestation_overdue`: returns active accounts with:
  - `last_attested_at` older than 90 days, or  
  - `last_attested_at` `NULL`.  
- `governance=missing_change_refs`: returns accounts where any of:
  - `change_request_id`, `sop_reference`, `password_storage_location` are blank.

### 6.2 Attestation Workflow

- Creating a `ServiceAccount` and posting to `service_account_attest`:
  - Asserts that a `ServiceAccountAttestation` row is created.  
  - Asserts the parent `ServiceAccount` has updated:
    - `last_attested_at`, `last_attested_by`, `last_attestation_status`, `last_attestation_notes`.  
    - `password_storage_location` (when provided).

### 6.3 Rotation Command

- With `EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'`:
  - One account with an **expired** password.  
  - One account with password **expiring within N days**.  
  - Call `check_service_account_rotation`:
    - Assert exactly one email sent.  
    - Assert the body contains both accounts and the expected status sections:
      - `EXPIRED PASSWORDS:`  
      - `EXPIRING SOON:`

---

## 7. Operational Checklist (Section 4.2)

To stay compliant with 4.2 using this system:

1. **Maintain the registry** of service and privileged accounts in `ServiceAccount`.  
2. Ensure **change ticket**, **SOP reference**, and **password storage** fields are populated.  
3. Run the **rotation alert command** daily via Task Scheduler and monitor the alerts.  
4. Have account owners perform **quarterly attestations**, especially for privileged accounts.  
5. Keep **Excel exports** and/or screenshots from the list/report views as audit evidence.  
6. Add and maintain **unit tests** for governance filters, attestation, and rotation alerts to prevent regressions.



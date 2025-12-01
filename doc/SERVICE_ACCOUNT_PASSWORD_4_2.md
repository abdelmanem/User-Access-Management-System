# Service Account & Privileged Account Password Requirements – RHG 4.2 Implementation Guide

**System:** User-Access-Management-System  
**Scope:** RHG 4.2 – *Application/Service and Privileged Accounts Password Requirements*  
**Status:** Implemented in application (evidence tracking only – not enforcement)

---

## 1. Objective

This document explains how the User-Access-Management-System documents and evidences compliance with RHG 4.2:

- Track that **external systems maintain service/application accounts** with passwords compliant with RHG Access Control Policy  
- Document **service accounts/application accounts** in external systems with:
  - Account name (in the external system)
  - What it's for (purpose)
  - Last password change date (in the external system)
- Track **privileged accounts** across all external systems  
- Document **password compliance** and rotation history

As with the rest of this system, these features provide **documentation and reporting**; they do **not** enforce password policies in AD, Opera Cloud, PMS, POS, etc.

---

## 2. Service Account Registry (`ServiceAccount`)

### 2.1 Model Overview

Implemented in `service_accounts.models.ServiceAccount`:

The `ServiceAccount` model provides comprehensive tracking of service, application, interface, backup, and privileged accounts across external systems.

### 2.2 Basic Account Information

- `account_name: CharField`
  - **Purpose:** Account name in the external system (e.g., 'svc_backup' in AD, 'interface_user' in Opera Cloud).
  - **Required:** Yes
  - **Help text:** "Account name in the external system"

- `system: ForeignKey(System)`
  - **Purpose:** Which external system the account exists in (AD, Opera Cloud, PMS, POS, etc.).
  - **Required:** Yes
  - Links to the `systems.System` model.

- `account_type: CharField(choices=ACCOUNT_TYPE_CHOICES)`
  - **Choices:**
    - `Service` – Service/Application Account
    - `Interface` – Interface Account
    - `Backup` – Backup Account
    - `Privileged` – Privileged/Admin Account
  - **Default:** `Service`
  - **Purpose:** Categorizes the account type for reporting and governance.

- `is_privileged: BooleanField`
  - **Purpose:** Marks if this service account should be governed as privileged/admin.
  - **Default:** `False`
  - **Critical for 4.2:** Identifies accounts that require enhanced governance.

- `admin_user: ForeignKey(CustomUser)`
  - **Purpose:** Links privileged service accounts to the administrator (4.3) this account is associated with.
  - **Nullable:** Yes
  - **Purpose:** Provides traceability to IT Administrators for privileged accounts.

### 2.3 Purpose and Ownership

- `purpose: TextField`
  - **Purpose:** Documented purpose of the service account (what it's used for).
  - **Required:** Yes
  - **Help text:** "What it's for - documented purpose of the service account"
  - **Critical for 4.2:** Auditors require documented business justification for each service account.

- `owner: ForeignKey(CustomUser)`
  - **Purpose:** Account owner/manager responsible for the account.
  - **Nullable:** Yes
  - **Help text:** "Account owner/manager"
  - **Critical for governance:** Identifies who is responsible for password rotation and attestation.

### 2.4 Password Compliance Tracking

- `password_last_changed: DateTimeField`
  - **Purpose:** Last password change date in the external system.
  - **Nullable:** Yes
  - **Critical for 4.2:** Documents when password was last rotated.

- `password_expires_on: DateTimeField`
  - **Purpose:** Password expiration date in the external system.
  - **Nullable:** Yes
  - **Critical for 4.2:** Tracks when password will expire (if applicable).

- `password_complies_with_policy: BooleanField`
  - **Purpose:** Documented compliance with RHG password policy in external system.
  - **Default:** `False`
  - **Critical for 4.2:** Evidence that password meets policy requirements.

- `password_policy_verified_date: DateTimeField`
  - **Purpose:** Date when password policy compliance was verified.
  - **Nullable:** Yes

- `password_policy_verified_by: ForeignKey(CustomUser)`
  - **Purpose:** User who verified password policy compliance.
  - **Nullable:** Yes
  - **Related name:** `password_policy_verifications`

These fields provide **complete audit evidence** that service account passwords comply with RHG policy.

### 2.5 Account Status and Metadata

- `is_active: BooleanField`
  - **Purpose:** Whether this service account is currently active.
  - **Default:** `True`

- `notes: TextField`
  - **Purpose:** Additional notes about the service account.
  - **Nullable:** Yes

- `created_at: DateTimeField(auto_now_add=True)`
- `updated_at: DateTimeField(auto_now=True)`
- `created_by: ForeignKey(CustomUser)`
- `updated_by: ForeignKey(CustomUser)`

### 2.6 Governance and Traceability Fields

- `change_request_id: CharField`
  - **Purpose:** Reference to change ticket that established/rotated this account.
  - **Max length:** 100
  - **Nullable:** Yes
  - **Critical for audit:** Links account to change management process (4.4).

- `sop_reference: CharField`
  - **Purpose:** Referenced SOP covering this account's use/rotation.
  - **Max length:** 200
  - **Nullable:** Yes
  - **Critical for audit:** Documents written procedures.

- `password_storage_location: CharField`
  - **Purpose:** Location of the password (vault/safe/password manager).
  - **Max length:** 255
  - **Nullable:** Yes
  - **Critical for security:** Documents where credentials are stored.

### 2.7 Attestation Fields

- `last_attested_at: DateTimeField`
  - **Purpose:** Timestamp of latest owner attestation.
  - **Nullable:** Yes

- `last_attested_by: ForeignKey(CustomUser)`
  - **Purpose:** User who performed the latest attestation.
  - **Nullable:** Yes

- `last_attestation_status: CharField(choices=ATTESTATION_STATUS_CHOICES)`
  - **Choices:** `Confirmed`, `Pending Removal`, `Unknown`
  - **Purpose:** Status from latest attestation.

- `last_attestation_notes: TextField`
  - **Purpose:** Notes/evidence captured during attestation.
  - **Nullable:** Yes

These fields support quarterly attestation workflows.

---

## 3. Service Account Password History (`ServiceAccountPasswordHistory`)

### 3.1 Model Overview

Implemented in `service_accounts.models.ServiceAccountPasswordHistory`:

The `ServiceAccountPasswordHistory` model provides an **append-only log** of all password changes for service accounts.

### 3.2 Password Change Documentation

- `service_account: ForeignKey(ServiceAccount)`
  - **Purpose:** Service account this password change belongs to.
  - **Related name:** `password_history`
  - **Required:** Yes

- `password_changed_date: DateTimeField`
  - **Purpose:** Date password was changed in the external system.
  - **Required:** Yes
  - **Critical for 4.2:** Documents when rotation occurred.

- `changed_by: ForeignKey(CustomUser)`
  - **Purpose:** Who documented the change.
  - **Nullable:** Yes
  - **Related name:** `service_account_password_changes`

- `documented_at: DateTimeField(auto_now_add=True)`
  - **Purpose:** When it was documented in this system.
  - **Auto-set:** Yes

- `expires_on: DateTimeField`
  - **Purpose:** Password expiration date.
  - **Nullable:** Yes

- `complies_with_policy: BooleanField`
  - **Purpose:** Whether password complies with RHG policy.
  - **Default:** `True`

- `notes: TextField`
  - **Purpose:** Notes about the password change.
  - **Nullable:** Yes

### 3.3 Automatic Status Updates

When a new `ServiceAccountPasswordHistory` entry is created:

- The parent `ServiceAccount.password_last_changed` is automatically updated to the latest entry's `password_changed_date`.
- The parent `ServiceAccount.password_expires_on` is updated if provided.
- The parent `ServiceAccount.password_complies_with_policy` is updated based on the latest entry.

This ensures the parent record always reflects the most recent password change.

### 3.4 History Properties

- `is_expired: property`
  - Returns `True` if `expires_on` is in the past.

- `days_until_expiry: property`
  - Returns number of days until password expires (or `None` if no expiration).

---

## 4. Service Account Management Interface

### 4.1 List View

View: `service_accounts.views.service_account_list`  
URL: `/service-accounts/` (`service_accounts:service_account_list`)

Features:

- **Filtering:**
  - By system
  - By account type (Service, Interface, Backup, Privileged)
  - By compliance status (compliant, non-compliant, expired, expiring soon)
  - By activity (active, inactive)
- **Search:** By account name, system name, purpose, notes
- **Ordering:** By account name, system, last changed date, expiration date
- **Pagination:** 25 records per page
- **Summary Cards:**
  - Total service accounts
  - Non-compliant accounts
  - Expired passwords
  - Expiring soon (within 30 days)
  - Privileged accounts

### 4.2 Detail View

View: `service_accounts.views.service_account_detail`  
URL: `/service-accounts/<id>/` (`service_accounts:service_account_detail`)

Displays:

- **Account Information:**
  - Account name, system, account type
  - Purpose, owner
  - Active status
- **Password Compliance:**
  - Last changed date
  - Expiration date
  - Compliance status (with badge)
  - Policy verification (verifier, date)
- **Governance:**
  - Change request ID
  - SOP reference
  - Password storage location
  - Attestation status (last attested, by whom, status)
- **Password History:**
  - Table of all password changes
  - Shows date, changed by, expiration, compliance, notes
- **Actions:**
  - Edit account
  - Add password history entry
  - Perform attestation
  - Delete account (if permitted)

### 4.3 Create/Update Forms

View: `service_accounts.views.service_account_create` / `service_account_update`  
Templates: `service_accounts/templates/service_accounts/service_account_form.html`

Form fields organized into sections:

- **Basic Information:**
  - Account name, system, account type
  - Purpose, owner
  - Active status
- **Password & Compliance:**
  - Last changed date
  - Expiration date
  - Compliance checkbox
  - Policy verification (date, verifier)
- **Governance:**
  - Change request ID
  - SOP reference
  - Password storage location
- **Additional Information:**
  - Notes

### 4.4 Password History Management

View: `service_accounts.views.service_account_password_history_add`  
URL: `/service-accounts/<id>/password-history/add/`

Form captures:

- Password changed date (in external system)
- Changed by (who documented it)
- Expiration date
- Compliance with policy
- Notes

Upon save:

- New `ServiceAccountPasswordHistory` entry is created.
- Parent `ServiceAccount` password fields are automatically updated.

---

## 5. Service Account Compliance Report

### 5.1 Overview

View: `service_accounts.views.service_account_compliance_report`  
URL: `/service-accounts/compliance/` (`service_accounts:service_account_compliance_report`)

Purpose:

- Provide **aggregated compliance view** across all service accounts.
- Highlight **non-compliant accounts** by system and account type.
- Show **expired and expiring passwords**.
- Support **audit exports**.

### 5.2 Report Structure

- **Summary by System:**
  - Total accounts per system
  - Compliant vs non-compliant counts
  - Expired passwords count
  - Expiring soon count (within 30 days)

- **Summary by Account Type:**
  - Service accounts
  - Interface accounts
  - Backup accounts
  - Privileged accounts

- **Non-Compliant Accounts Table:**
  - Lists all accounts that are:
    - Non-compliant with password policy
    - Have expired passwords
    - Have passwords expiring soon
    - Missing password change dates
    - Missing policy verification

### 5.3 Filters

- **System:** Filter by specific external system
- **Account Type:** Filter by account type
- **Compliance Status:** Show only non-compliant, expired, or expiring
- **Privileged:** Show only privileged accounts

### 5.4 Exports

The compliance report provides:

- **Excel Export:** `service_accounts_compliance.xlsx`
  - Includes all summary statistics and detailed account listings
  - Formatted for audit evidence
- **CSV Export:** `service_accounts_compliance.csv`
  - Raw data export for further analysis

Both exports include:

- Account name, system, account type
- Purpose, owner
- Password last changed, expiration date
- Compliance status, policy verification
- Change request ID, SOP reference
- Storage location, attestation status

---

## 6. Service Account Attestation Workflow

### 6.1 Attestation Form

View: `service_accounts.views.service_account_attest`  
URL: `/service-accounts/<id>/attest/`

Form fields:

- **Attestation Status:**
  - `Confirmed` – Account is still needed and properly managed
  - `Pending Removal` – Account should be removed
  - `Unknown` – Status unclear, requires investigation
- **Attestation Notes:**
  - Text field for evidence, justification, or action items
- **Attestation Date:**
  - Auto-set to current date/time

### 6.2 Attestation Process

1. Owner or designated user navigates to service account detail page.
2. Clicks **"Perform Attestation"** button.
3. Completes attestation form:
   - Selects status (Confirmed, Pending Removal, Unknown)
   - Enters notes (required for audit evidence)
4. Upon submission:
   - `last_attested_at` is set to current timestamp
   - `last_attested_by` is set to current user
   - `last_attestation_status` is updated
   - `last_attestation_notes` is saved
5. Success message confirms attestation completion.

### 6.3 Attestation Reporting

The compliance report highlights:

- Accounts with **overdue attestations** (last attested > 90 days ago)
- Accounts with **"Pending Removal"** status
- Accounts with **"Unknown"** status

This supports quarterly review processes.

---

## 7. Navigation & Access

The Service Account Management module is available under the **Service Accounts** menu:

- Navigation template: `templates/navigation.html`
- **Service Accounts → List**
  - URL: `/service-accounts/`
- **Service Accounts → Compliance Report**
  - URL: `/service-accounts/compliance/`
- **Service Accounts → Create**
  - URL: `/service-accounts/create/`
- **Service Accounts → Detail**
  - URL: `/service-accounts/<id>/`

Access is controlled by the same authentication/authorization model as other modules (standard Django auth and staff permissions).

---

## 8. How This Satisfies RHG 4.2 Requirements

**Audit Requirement → Implementation Mapping**

- **Track that external systems maintain service/application accounts with passwords compliant with RHG policy**
  - `ServiceAccount` model tracks all service accounts across external systems.
  - `password_complies_with_policy` field documents compliance.
  - `password_policy_verified_date` and `password_policy_verified_by` provide verification evidence.

- **Document service accounts with account name, purpose, and last password change date**
  - `account_name` captures the name in the external system.
  - `purpose` documents what the account is used for.
  - `password_last_changed` tracks last rotation date.
  - All fields are included in exports for audit evidence.

- **Track privileged accounts across all external systems**
  - `account_type` includes "Privileged" option.
  - `is_privileged` flag marks accounts requiring enhanced governance.
  - `admin_user` links privileged accounts to IT Administrators (4.3).
  - Compliance report filters by privileged accounts.

- **Document password rotation history**
  - `ServiceAccountPasswordHistory` provides append-only log of all password changes.
  - Each entry documents change date, expiration, compliance, and notes.
  - Parent `ServiceAccount` automatically reflects latest password status.

- **Provide evidence of password storage and change management**
  - `password_storage_location` documents where credentials are stored.
  - `change_request_id` links to change management process (4.4).
  - `sop_reference` documents written procedures.

---

## 9. Known Gaps and Future Enhancements

### 9.1 Privileged Account Governance Enhancements

**Status:** Partially implemented

**Current State:**
- `is_privileged` flag exists.
- `admin_user` links to IT Administrators.
- Basic compliance tracking exists.

**Gaps:**
- No dedicated **attestation workflow** specifically for privileged accounts.
- No **owner approval** requirement for privileged account creation.
- No **linkage to administrator accounts (4.3)** beyond `admin_user` field.

**Recommendation:**
- Add privileged account attestation workflow requiring IT Administrator approval.
- Require `admin_user` to be set for all privileged accounts.
- Add validation that only IT Administrators can create/manage privileged accounts.

### 9.2 Rotation Enforcement & Alerts

**Status:** Not yet implemented

**Gaps:**
- No **automated reminders** for upcoming password expirations.
- No **escalation** for overdue password changes.
- No **dashboard alerts** for non-compliant accounts.

**Recommendation:**
- Implement scheduled job to check for:
  - Passwords expiring within 30 days
  - Passwords expired
  - Passwords not changed within policy timeframe (e.g., 90 days)
- Send email notifications to account owners.
- Create dashboard widget showing accounts requiring attention.

### 9.3 Change/Incident Traceability Enhancements

**Status:** Partially implemented

**Current State:**
- `change_request_id` field exists.
- `sop_reference` field exists.

**Gaps:**
- No **validation** that change request ID is valid.
- No **linkage** to `change_management.AccountChangeRequest` model.
- No **break-glass procedure** documentation.

**Recommendation:**
- Add ForeignKey to `AccountChangeRequest` model (when available).
- Add break-glass procedure fields (when used, by whom, justification).
- Add incident ticket reference field.

---

## 10. Key URLs for 4.2 Evidence

- **Service Account List:**
  - `/service-accounts/`
- **Service Account Detail:**
  - `/service-accounts/<id>/`
- **Service Account Compliance Report:**
  - `/service-accounts/compliance/`
- **Service Account Create:**
  - `/service-accounts/create/`
- **Service Account Password History:**
  - `/service-accounts/<id>/password-history/add/`
- **Service Account Attestation:**
  - `/service-accounts/<id>/attest/`

These views, combined with the export files (CSV/Excel), provide complete, traceable evidence for RHG 4.2 that can be handed directly to auditors.

---

## 11. Export Evidence for Auditors

### 11.1 Service Account List Export

The Service Account List can be exported to:
- **CSV:** All service accounts with current filter applied
- **Excel:** Formatted spreadsheet with summary statistics

### 11.2 Compliance Report Export

The Compliance Report can be exported to:
- **Excel:** `service_accounts_compliance.xlsx`
  - Includes summary by system and account type
  - Detailed non-compliant accounts listing
  - Formatted for audit evidence
- **CSV:** `service_accounts_compliance.csv`
  - Raw data export

Both exports include:
- Account name, system, account type
- Purpose, owner
- Password last changed, expiration date
- Compliance status, policy verification (verifier, date)
- Change request ID, SOP reference
- Password storage location
- Attestation status (last attested, by whom, status)
- Password history summary (count, latest change date)

These exports are designed to be attached directly to audit evidence packages.

---

## 12. Integration with Other Modules

### 12.1 Administrator Access (4.3)

- `admin_user` field links privileged service accounts to IT Administrators.
- Compliance report can filter by administrator.
- Supports requirement that privileged accounts are limited to IT Administrators.

### 12.2 Change Management (4.4)

- `change_request_id` field references change tickets.
- Future enhancement: ForeignKey to `AccountChangeRequest` model.
- Provides traceability to change management process.

### 12.3 Default Account Management (4.7)

- Service accounts are distinct from default accounts.
- Default accounts are factory/vendor accounts (tracked separately).
- Service accounts are application/interface accounts created for business use.

---

**Document Prepared By:** AI Assistant  
**Review Status:** Pending Review  
**Last Updated:** 2025-11-17


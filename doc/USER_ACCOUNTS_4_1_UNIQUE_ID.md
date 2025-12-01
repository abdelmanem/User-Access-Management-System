# User Accounts – Unique User ID Assignment – RHG 4.1 Implementation Guide

**System:** User-Access-Management-System  
**Scope:** RHG 4.1 – *User Accounts: Unique User ID Assignment*  
**Status:** Implemented in application (evidence tracking only – not enforcement)

---

## 1. Objective

This document explains how the User-Access-Management-System documents and evidences compliance with RHG 4.1:

- Track that **external systems assign unique user IDs** to each person  
- Document that **generic accounts are not used** in external systems  
- Track that **password settings in external systems align** with RHG Access Control Policy  
- Document compliance across all systems: Active Directory, PMS, POS, Hotel Kit, Keylock system, payment portals, OTA websites, ReviewPro, etc.

As with the rest of this system, these features provide **documentation and reporting**; they do **not** enforce access in AD, Opera Cloud, PMS, POS, etc.

---

## 2. Unique User ID Tracking (`CustomUser`)

### 2.1 Employee ID Assignment

Implemented in `accounts.CustomUser`:

- `employee_id: CharField`
  - **Purpose:** System-generated unique identifier for each employee.
  - **Help text:** "Unique employee identifier (system-generated)".
  - Automatically generated on user creation to ensure uniqueness across the system.

- `employment_status: CharField`
  - Tracks employment status (Active, Terminated, On Leave, etc.).
  - Used to identify accounts that should be reviewed for deactivation.

- `department: ForeignKey(Department)`
  - Links users to organizational departments for reporting and access management.

### 2.2 User Account Documentation

The `CustomUser` model provides comprehensive employee metadata:

- Full name, email, phone
- Employment dates (hire date, termination date)
- Department and position
- Active/inactive status

This foundation ensures every user account in the system has a unique identity that can be traced across external systems.

---

## 3. System-Specific Username Tracking (`UserSystemAccess`)

### 3.1 Model Fields

Implemented in `access_management.models.UserSystemAccess`:

- **System-specific username**
  - `system_username: CharField`
  - **Purpose:** Captures the actual username used in each external system (e.g., 'john.doe' in AD, 'jdoe' in Opera Cloud).
  - **Critical for 4.1:** Documents that each employee has a unique username per external system.

- **Username uniqueness verification metadata**
  - `username_verified_by: ForeignKey(CustomUser)`
    - Records who verified that this external username is unique to the employee.
  - `username_verified_date: DateTimeField`
    - Date when the username uniqueness was last verified.
  - `username_verification_artifact: FileField`
    - Attachment (screenshot, export, etc.) showing proof of username uniqueness.
  - `username_verification_artifact_url: URLField`
    - Link to external evidence (ticket, document, etc.) for username uniqueness verification.

These fields provide **audit evidence** that usernames in external systems have been verified as unique and properly assigned.

### 3.2 Generic Account Detection and Remediation

- **Generic account flagging**
  - `is_generic_account: BooleanField`
    - Automatically detected when `system_username` matches known generic patterns (admin, guest, user, etc.).
    - Uses `access_management.utils.is_generic_username()` for pattern matching.

- **Remediation tracking**
  - `generic_account_remediated: BooleanField`
    - Indicates whether the generic account has been replaced with a unique account in the external system.
  - `remediation_date: DateTimeField`
    - Date when generic account was remediated in external system.
  - `remediation_notes: TextField`
    - Notes on how the generic account was remediated.
  - `remediated_by: ForeignKey(CustomUser)`
    - User who documented the remediation.

### 3.3 Auto-Detection Logic

The `UserSystemAccess` model automatically detects generic accounts:

```python
def mark_as_generic_if_needed(self):
    if self.system_username:
        self.is_generic_account = self.check_if_generic_account()
```

This ensures that generic accounts are flagged immediately upon assignment creation or update.

---

## 4. Generic Account Prevention in Access Assignment Workflow

### 4.1 Create Access Assignment

View: `access_management.views.access_assignment_create`

When creating a new access assignment:

- The form collects `system_username` (required for compliance tracking).
- Real-time validation warns if the username matches generic patterns:
  - Uses `GENERIC_USERNAME_PATTERNS` from `access_management.utils`.
  - Displays warning message: "Warning: Username appears to be a generic account."
- The form allows marking `is_generic_account` if needed (for documentation purposes).
- If generic, the form collects remediation fields:
  - `generic_account_remediated`
  - `remediation_date`
  - `remediation_notes`
  - `remediated_by` (auto-set to current user)

This ensures that generic accounts are identified and documented at the time of assignment creation.

### 4.2 Update Access Assignment

View: `access_management.views.access_assignment_update`

- The same generic account fields can be updated later.
- When marking as remediated:
  - `generic_account_remediated` is set to `True`.
  - `remediation_date` is set to current date/time.
  - `remediated_by` is set to the current user.
  - An `AccessHistory` entry is created documenting the remediation.

This supports the remediation workflow required by RHG 4.1.

---

## 5. Generic Accounts Report

### 5.1 Overview

View: `access_management.views.generic_accounts_report`  
URL: `/access-management/generic-accounts/` (`access_management:generic_accounts_report`)

Purpose:

- Provide a **single consolidated view** of all generic accounts across external systems.
- Highlight **unremediated generic accounts** that require action.
- Enable **remediation workflow** with one-click remediation marking.
- Provide **statistics** by system showing compliance status.

### 5.2 Filters

The report supports the following filters:

- **System:** Limit to a specific external system.
- **Show Remediated:** Toggle to include/exclude already remediated accounts.
- **Search:** Search by username, user name, or system name.

### 5.3 Summary Statistics

The report displays:

- **Total Generic Accounts:** Count of all generic accounts across systems.
- **Unremediated:** Count of generic accounts that have not been remediated.
- **Remediated:** Count of generic accounts that have been remediated.
- **By System:** Breakdown showing generic account counts per system.

### 5.4 Table Columns

Per generic account, the table displays:

- **User** (full name, employee ID, department)
- **System** (name and code)
- **Username** (system_username in external system)
- **Generic Account** flag
- **Remediation Status:**
  - **Red badge** if not remediated (requires action).
  - **Green badge** if remediated (with date).
- **Remediation Date** (if remediated)
- **Remediated By** (user who documented remediation)
- **Actions:**
  - Link to mark as remediated.
  - Link to view full assignment details.

### 5.5 Remediation Workflow

Users can mark generic accounts as remediated directly from the report:

- Click **"Mark as Remediated"** button.
- System prompts for:
  - Remediation date (defaults to today).
  - Remediation notes (required).
- Upon submission:
  - `generic_account_remediated` is set to `True`.
  - `remediation_date` is recorded.
  - `remediated_by` is set to current user.
  - `AccessHistory` entry is created.
  - Success message is displayed.

This provides a streamlined workflow for documenting remediation evidence.

---

## 6. Cross-System Account Mapping (User Matrix)

### 6.1 Overview

View: `access_management.views.cross_system_account_mapping`  
URL: `/access-management/cross-system-mapping/` (`access_management:cross_system_account_mapping`)

Purpose:

- Provide a **matrix view** showing each employee's usernames across all external systems.
- Enable **single view per employee** as required by RHG 4.1.
- Display **generic account flags** and **verification status** for each assignment.
- Support **export** for audit evidence.

### 6.2 Matrix Structure

The matrix displays:

- **Rows:** Employees (with employee ID, name, department).
- **Columns:** External systems (AD, PMS, POS, etc.).
- **Cells:** For each employee × system combination:
  - **Username** in that external system (`system_username`).
  - **Generic Account Badge** (if flagged).
  - **Verification Status:**
    - Green checkmark if verified.
    - Yellow warning if not verified.
  - **Link** to full assignment details.

### 6.3 Filters

The matrix supports:

- **User Search:** Filter by employee name or ID.
- **System Filter:** Show only specific systems.
- **Status Filter:** Show only active, suspended, or all assignments.
- **Generic Account Filter:** Show only generic accounts or exclude them.

### 6.4 Exports for Auditors

The matrix provides two export formats:

- **Excel:** `cross_system_account_mapping.xlsx`
  - Built by `export_cross_system_mapping_to_excel`.
- **CSV:** `cross_system_account_mapping.csv`
  - Built by `export_cross_system_mapping_to_csv`.

Both include:

- Employee ID, name, department
- System name and code
- Username per system (`system_username`)
- Generic account flag (Yes/No)
- Remediation status (if generic)
- Verification status (verified by, verified date)
- Access type and status

These exports provide complete audit evidence showing that each employee has unique usernames across systems.

---

## 7. Username Uniqueness Verification Workflow

### 7.1 Verification Fields

Each `UserSystemAccess` record includes verification metadata:

- `username_verified_by`: Who verified uniqueness.
- `username_verified_date`: When verification occurred.
- `username_verification_artifact`: File attachment (screenshot, export).
- `username_verification_artifact_url`: Link to external evidence (ticket, document).

### 7.2 Verification in Access Assignment Form

Template: `access_management/templates/access_management/access_assignment_form.html`

The form includes a **"Username Verification (4.1)"** section:

- **Verifier:** Dropdown to select who verified uniqueness.
- **Verification Date:** Date picker for when verification occurred.
- **Verification Artifact:** File upload for evidence.
- **Verification URL:** Text field for external evidence link.

This ensures that verification evidence is captured at assignment creation or update.

### 7.3 Verification in Assignment Detail View

Template: `access_management/templates/access_management/access_assignment_detail.html`

The detail view displays:

- **Verification Status:**
  - Green badge if verified (with verifier name and date).
  - Yellow badge if not verified (requires action).
- **Verification Evidence:**
  - Link to uploaded artifact (if present).
  - Link to external URL (if present).

This provides auditors with direct access to verification evidence.

---

## 8. Navigation & Access

The following views are available under the **Access** menu:

- Navigation template: `templates/navigation.html`
- **Access → Generic Accounts (4.1)**
  - URL: `/access-management/generic-accounts/`
- **Access → Cross-System Mapping**
  - URL: `/access-management/cross-system-mapping/`
- **Access → Access Assignments**
  - Individual assignments show username verification and generic account status.

Access is controlled by the same authentication/authorization model as other access management views (standard Django auth and staff permissions).

---

## 9. How This Satisfies RHG 4.1 Requirements

**Audit Requirement → Implementation Mapping**

- **Track that external systems assign unique user IDs to each person**
  - `system_username` field captures the actual username in each external system.
  - `username_verified_by`, `username_verified_date`, and verification artifacts document that uniqueness has been verified.
  - Cross-system mapping matrix shows all usernames per employee across systems.

- **Document that generic accounts are not used in external systems**
  - `is_generic_account` flag automatically detects generic usernames.
  - Generic Accounts Report lists all generic accounts with remediation status.
  - Remediation workflow documents when generic accounts are replaced with unique accounts.
  - Real-time warnings in access assignment forms prevent new generic account assignments.

- **Track that password settings in external systems align with RHG policy**
  - ⚠️ **Gap:** Password policy compliance tracking per account is not yet implemented.
  - **Recommendation:** Add `password_last_changed`, `password_expires_on`, `password_complies_with_policy`, and `password_policy_verified_date/by` fields to `UserSystemAccess`.

- **Document compliance across all systems**
  - `System` model catalogs all external systems (AD, PMS, POS, etc.).
  - `UserSystemAccess` provides per-system username tracking.
  - Cross-system exports include all systems for complete audit evidence.

---

## 10. Known Gaps and Future Enhancements

### 10.1 Password Policy Evidence per Account

**Status:** Not yet implemented

**Required Fields:**
- `password_last_changed: DateTimeField` – Last password change date in external system.
- `password_expires_on: DateTimeField` – Password expiration date in external system.
- `password_complies_with_policy: BooleanField` – Documented compliance with RHG password policy.
- `password_policy_verified_date: DateTimeField` – Date when compliance was verified.
- `password_policy_verified_by: ForeignKey(CustomUser)` – User who verified compliance.

**Recommendation:** Add these fields to `UserSystemAccess` and include them in access assignment forms and exports.

### 10.2 Policy Drift Monitoring

**Status:** Not yet implemented

**Required Features:**
- Alerting/reporting for usernames that have not been reviewed recently.
- Detection of overlapping usernames between users.
- Reporting on records missing external usernames (blank `system_username` entries).

**Recommendation:** Create a Policy Drift Monitoring dashboard that highlights:
- Assignments missing `system_username`.
- Assignments with unverified usernames (older than 90 days).
- Potential username conflicts (same username used by multiple employees).

---

## 11. Key URLs for 4.1 Evidence

- **Generic Accounts Report:**
  - `/access-management/generic-accounts/`
- **Cross-System Account Mapping (User Matrix):**
  - `/access-management/cross-system-mapping/`
- **Access Assignment Detail (per assignment):**
  - `/access-management/assignments/<id>/`
- **User Detail with Cross-System Accounts:**
  - `/accounts/users/<id>/`
  - `/access-management/users/<id>/cross-system-accounts/`

These views, combined with the export files (CSV/Excel), provide complete, traceable evidence for RHG 4.1 that can be handed directly to auditors.

---

## 12. Export Evidence for Auditors

### 12.1 Generic Accounts Export

The Generic Accounts Report can be exported to:
- **CSV:** Generic accounts list with remediation status.
- **Excel:** Formatted spreadsheet with statistics and filters applied.

### 12.2 Cross-System Mapping Export

The Cross-System Account Mapping can be exported to:
- **CSV:** `cross_system_account_mapping.csv`
- **Excel:** `cross_system_account_mapping.xlsx`

Both exports include:
- Employee ID, name, department
- System name and code
- Username per system
- Generic account flag and remediation status
- Verification metadata (verifier, date, evidence links)
- Access type and status

These exports are designed to be attached directly to audit evidence packages.

---

**Document Prepared By:** AI Assistant  
**Review Status:** Pending Review  
**Last Updated:** 2025-11-17


# Administrator Access Governance – RHG 4.3 Implementation Guide

**System:** User-Access-Management-System  
**Scope:** RHG 4.3 – *Administrator Equivalent Access Rights Limited to IT Administrators*  
**Status:** Implemented in application (evidence tracking only – not enforcement)

---

## 1. Objective

This document explains how the User-Access-Management-System documents and evidences compliance with RHG 4.3:

- Track that **administrator access in external systems is limited to IT Administrators**  
- Document that **master/default admin accounts are not used** for day-to-day work  
- Track that **workstation login accounts do not have domain admin** rights in AD  
- Document that **separate admin accounts exist** (e.g. `John.Doe_Admin`)  
- Track that **administrator passwords are stored securely** (e.g., in a safe or vault)  
- Document that **all administrators use individual accounts** in external systems  

As with the rest of this system, these features provide **documentation and reporting**; they do **not** enforce access in AD, PMS, POS, etc.

---

## 2. IT Administrator Identification (`CustomUser`)

### 2.1 Model Fields

Implemented in `accounts.CustomUser`:

- `is_it_administrator: BooleanField`
  - **Purpose:** Flag that the user is formally authorized as an IT Administrator.
  - **Help text:** “User is authorized as IT Administrator (RHG 4.3 scope)”.
- `it_admin_certification_date: DateField (nullable)`
  - **Purpose:** Date when the user was certified/approved as IT Administrator.
- `it_admin_certified_by: ForeignKey("CustomUser", nullable)`
  - **Purpose:** Records who certified/approved this user as IT Administrator.

### 2.2 Forms & Maintenance

Implemented in `accounts/forms.py`:

- The base user forms (`UserCreateForm` / `UserUpdateForm`) now include:
  - `is_it_administrator`
  - `it_admin_certification_date`
  - `it_admin_certified_by`

These can be managed by administrators via the existing **User Create/Update** screens.

### 2.3 Evidence in UI

- `accounts/templates/accounts/user_detail.html` shows:
  - Whether the user is an IT Administrator.
  - Optional certification date and certifying user.

This provides direct auditor evidence that only users marked as IT Administrators should hold administrator-equivalent assignments.

---

## 3. Administrator-Equivalent Access Tracking (`UserSystemAccess`)

### 3.1 Model Extensions

Implemented in `access_management.models.UserSystemAccess`:

- **Admin access flag**
  - `is_admin_access: BooleanField`
  - *Purpose:* Indicates that this assignment grants administrator or equivalent privileges in the external system.

- **Separate admin vs regular accounts**
  - `has_separate_admin_account: BooleanField`
  - `admin_account_username: CharField`
  - `regular_account_username: CharField`
  - *Purpose:*  
    - Evidence that users have a **dedicated admin ID** (`John.Doe_Admin`), separate from their normal login (`John.Doe`).  
    - Supports the RHG requirement that master/default admin accounts are not used for regular work.

- **Workstation vs Domain Admin**
  - `is_workstation_login: BooleanField`
  - `has_domain_admin: BooleanField`
  - *Purpose:*  
    - Records that this account is used as a **workstation login**.  
    - Tracks whether this same account has **domain admin or equivalent** rights.  
    - Enables reporting of **non-compliant combinations**: workstation login + domain admin.

- **Administrator password storage documentation**
  - `admin_password_storage_location: CharField`
    - Example: “Financial Controller safe”, “Password vault – entry ID 12345”.
  - `admin_password_stored_date: DateTimeField`
  - `admin_password_stored_by: ForeignKey(CustomUser)`
  - *Purpose:*  
    - Document **where** the admin credential is stored.  
    - Document **when** storage was last verified.  
    - Document **who** confirmed/placed the credential in the secure location.

> These fields are **per assignment and per external system**, so the same user can have different admin storage locations and patterns across AD, PMS, POS, etc.

---

## 4. Data Capture in Access Assignment Workflow

### 4.1 Create Access Assignment

View: `access_management.views.access_assignment_create`

When creating a new access assignment:

- `is_admin_access` is automatically set **true** if:
  - `access_type` is **Admin** or **Super Admin**, or
  - The “This assignment grants administrator / equivalent access” checkbox is ticked.
- The form collects:
  - `has_separate_admin_account`
  - `admin_account_username`
  - `regular_account_username`
  - `is_workstation_login`
  - `has_domain_admin`
  - `admin_password_storage_location`
  - `admin_password_stored_date`
- If `admin_password_stored_date` is provided:
  - `admin_password_stored_by` is automatically set to the **current user** creating the record.

This ensures that for every administrator-equivalent assignment, evidence can be captured at the time the access is created.

### 4.2 Update Access Assignment

View: `access_management.views.access_assignment_update`

- The same admin-related fields can be updated later:
  - Admin vs standard access.
  - Separate admin vs regular account.
  - Workstation login vs domain admin status.
  - Password storage location and verification date.
- When `admin_password_stored_date` is newly set and `admin_password_stored_by` is empty:
  - The application sets `admin_password_stored_by` to the **current user** updating the record.

This supports periodic review and re-verification of admin storage procedures.

---

## 5. Administrator Access Documentation in the UI

### 5.1 Access Assignment Form

Template: `access_management/templates/access_management/access_assignment_form.html`

New card: **“Administrator Access (4.3 Compliance)”** containing:

- **Checkboxes**
  - “This assignment grants administrator / equivalent access”
  - “User has separate admin account (e.g., John.Doe_Admin)”
  - “Account is used for workstation login”
  - “Account has domain admin / equivalent rights”
- **Admin / regular usernames**
  - `admin_account_username` (e.g., `John.Doe_Admin`)
  - `regular_account_username` (e.g., `John.Doe`)
- **Password storage**
  - `admin_password_storage_location`
  - `admin_password_stored_date`

These fields are available for both **create** and **update** operations and are pre-populated with existing values when editing records.

### 5.2 Access Assignment Detail View

Template: `access_management/templates/access_management/access_assignment_detail.html`

The **Security & Compliance** section now shows:

- Whether the assignment is **Admin / Elevated**.
- Whether there is a **separate admin account**, with admin + regular usernames.
- Whether the account is a **workstation login**, and if it also has **domain admin** (explicitly flagged as *non-compliant*).
- Where the **admin password is stored**, along with:
  - Last verified date.
  - Who verified/recorded the storage.

This gives a per-assignment “snapshot” that auditors can inspect directly from the UI.

---

## 6. Administrator Accounts Compliance Report

### 6.1 Overview

View: `access_management.views.admin_accounts_report`  
URL: `/access-management/admin-accounts/` (`access_management:admin_accounts_report`)

Purpose:

- Provide a **single consolidated view** of all administrator-equivalent assignments across systems.
- Highlight **non-compliant patterns**, including:
  - Admin access granted to **non-IT Administrators**.
  - Admin access **without separate admin IDs**.
  - **Workstation login** accounts that also have **domain admin**.
  - Admin accounts **without documented password storage**.

### 6.2 Filters

The report supports the following filters:

- **System:** Limit to a specific external system.
- **Department:** Limit to users within a specific department.
- **Focus (issue):**
  - `non_it` – Admin access to non-IT Administrators.
  - `no_separate` – Admin access without separate admin account.
  - `workstation_domain` – Workstation login accounts with domain admin rights.
  - `no_storage` – Admin accounts missing password storage documentation.
- **Search:** Search by user, username, or system name.

### 6.3 Summary Metrics

The report shows high-level counts for the currently filtered scope:

- **Admin Assignments (`total_admin`):**
  - Count of assignments where `is_admin_access = True` or `access_type` is **Admin/Super Admin**.
- **Non‑IT Admins (`non_it_admins`):**
  - Admin assignments where the user is **not marked** as `is_it_administrator`.
- **No Separate Admin ID (`no_separate_admin`):**
  - Admin assignments where there is **no** `has_separate_admin_account` or `admin_account_username`.
- **Workstation + Domain Admin (`workstation_domain_admin`):**
  - Assignments with `is_workstation_login = True` **and** `has_domain_admin = True` (explicit non‑compliance).

These metrics align directly with the RHG 4.3 audit asks.

### 6.4 Table Columns

Per assignment, the table displays:

- **User** (full name, login, department)
- **IT Admin** flag
- **System** (name and code)
- **Access Type** and whether it is marked as **Admin / Elevated**
- **Admin / Regular IDs**:
  - Admin account username (if present).
  - Regular account username (if present).
  - Badge if **no separate admin ID** exists.
- **Workstation / Domain** view:
  - Whether this is a workstation login.
  - Whether it also has domain admin (**non‑compliant** badge when both are true).
- **Password Storage**:
  - Storage location.
  - Last verified date (if available).
- **Status** (Active, Suspended, Revoked, etc.).

### 6.5 Exports for Auditors

The report provides two export formats for the current filter scope:

- **Excel:** `admin_accounts_compliance.xlsx`
  - Built by `export_admin_accounts_to_excel`.
- **CSV:** `admin_accounts_compliance.csv`
  - Built by `export_admin_accounts_to_csv`.

Both include:

- User, username, department, **IT Admin flag**
- System, system code
- Access type, **admin access flag**
- Admin account username, regular account username
- Workstation login flag, domain admin flag
- Password storage location, stored/verified date
- Status

These exports are designed to be attached directly to audit evidence packages.

---

## 7. Navigation & Access

The **Admin Accounts (4.3)** report is available under the **Access** menu:

- Navigation template: `templates/navigation.html`
- Sidebar path:
  - **Access → Admin Accounts (4.3)**
  - URL: `/access-management/admin-accounts/`

Access is controlled by the same authentication/authorization model as other access management views (standard Django auth and staff permissions).

---

## 8. How This Satisfies RHG 4.3 Requirements

**Audit Requirement → Implementation Mapping**

- **Admin access limited to IT Administrators**
  - `CustomUser.is_it_administrator` + `admin_accounts_report` filter `non_it` highlight admin rights given to non‑IT admins.

- **Master/default admin accounts not used**
  - `has_separate_admin_account`, `admin_account_username`, `regular_account_username` track use of personal admin IDs.
  - Report highlights assignments where **no separate admin ID** exists (`no_separate_admin` metric).

- **Workstation logins don’t have domain admin**
  - `is_workstation_login` + `has_domain_admin` fields and `workstation_domain_admin` metric show non‑compliant combinations.

- **Separate admin accounts exist (e.g., John.Doe_Admin)**
  - `admin_account_username` field documented per system.
  - Displayed in assignment detail and in the admin accounts report.

- **Administrator passwords stored securely**
  - `admin_password_storage_location`, `admin_password_stored_date`, `admin_password_stored_by` document storage and verification.
  - `no_storage` focus filter in the report highlights missing storage documentation.

- **All administrators use individual accounts**
  - Combination of:
    - IT Admin flag on `CustomUser`.
    - Separate admin account fields on `UserSystemAccess`.
    - Cross‑user reporting in the `admin_accounts_report`.

---

## 9. Key URLs for 4.3 Evidence

- **Administrator Accounts Compliance Report:**
  - `/access-management/admin-accounts/`
- **Access Assignment Detail (per admin assignment):**
  - `/access-management/assignments/<id>/`
- **User Detail with IT Administrator flag:**
  - `/accounts/users/<id>/`

These views, combined with the export files, provide complete, traceable evidence for RHG 4.3 that can be handed directly to auditors.  



# Change Management Process – RHG 4.4 Implementation Guide

**System:** User-Access-Management-System  
**Scope:** RHG 4.4 – *Change Management Process for User Accounts*  
**Status:** Implemented in application (evidence tracking only – not enforcement)

---

## 1. Objective

This document explains how the User-Access-Management-System documents and evidences compliance with RHG 4.4:

- **Document change management process** for creation / modification / deletion of user accounts in external systems.  
- **Track approvals** for all user account changes.  
- **Maintain written SOP documentation** for the process.  
- **Document that the System Owner authorizes user-id establishment** in external systems.  
- Maintain a **User Matrix** showing:
  - Systems each user has permission to access.  
  - Permissions/privileges they have been approved to have in each system.  
- Provide compliance evidence across all systems (AD, PMS, POS, Keylock, payment portals, OTA’s, etc.).

As with other modules, this system **documents and reports**; it does **not enforce** changes in AD, Opera Cloud, PMS, POS, etc.

---

## 2. Change Management Documentation (`AccountChangeRequest`)

### 2.1 Model

Implemented in `change_management.AccountChangeRequest`:

- `change_type: CharField(choices=CHANGE_TYPE_CHOICES)`  
  - Values: **Create**, **Modify**, **Delete**, **Suspend** (account in external system).  
- `user: ForeignKey(CustomUser, null=True)`  
  - Employee whose external account is being created/changed/deleted (if known).  
- `system: ForeignKey(System)`  
  - External system where the account change will occur (AD, PMS, POS, Doorlock, etc.).  
- `requested_by: ForeignKey(CustomUser)`  
  - Person requesting the account change.  
- `business_justification: TextField`  
  - **Legitimate business need** for the account change, required for RHG 4.4.  
- `system_owner: ForeignKey(CustomUser, null=True, related_name="system_owner_approvals")`  
  - System Owner required to authorize the change.  
- `system_owner_approved: BooleanField`  
  - Indicates whether the System Owner has approved this change request.  
- `system_owner_approval_date: DateTimeField(null=True)`  
  - When the System Owner approved the request.  
- `system_owner_approval_notes: TextField(null=True)`  
  - System Owner notes regarding the change.  
- `it_approval: ForeignKey(CustomUser, null=True, related_name="it_approved_account_changes")`  
  - Optional IT approval for the change.  
- `it_approval_date: DateTimeField(null=True)`  
  - When IT approved the change.  
- `status: CharField(choices=STATUS_CHOICES)`  
  - Workflow status: **Pending**, **Approved**, **Rejected**, **Completed** (in external system).  
- `completed_in_external_system: BooleanField`  
  - True once the change has been implemented in the external system.  
- `completed_date: DateTimeField(null=True)`  
  - When the external system change was completed.  
- `created_at: DateTimeField(auto_now_add=True)`  
  - Timestamp when the request was logged.

### 2.2 Front-End Change Request Console

- Fully integrated HTML module under **“Change Management (4.4)”** in the sidebar:
  - **List view** (`/change-management/requests/`): filter by status, change type, system, user, search; shows owner approval badges and quick actions.
  - **Create view** (`/change-management/requests/create/`): Bootstrap form that captures change type, system, optional user, business justification, System Owner approval metadata, optional IT approver, and completion status.
  - **Detail view** (`/change-management/requests/<id>/`): auditor-friendly summary with request metadata, approval history, and justification text.
  - **Update view** (`/change-management/requests/<id>/update/`): edit existing requests, mark completion in the external system, adjust approvals, etc.
- All pages require authentication (`@login_required`) and reuse the application layout, giving non-admin users full change-management capability without relying on Django admin.

### 2.3 Administration & Evidence

- Django admin (`change_management.admin.AccountChangeRequestAdmin`) still provides back-office filtering/search and read-only auditing (now without autocomplete dependencies).  
- Combined with the front-end console, every change request has a traceable record showing requester, approvals, timestamps, and completion state without modifying external systems directly.

---

## 3. System Owner Authorization on Access Assignments (`UserSystemAccess`)

### 3.1 Model Extensions

Implemented in `access_management.UserSystemAccess`:

- `system_owner_approved: BooleanField`  
  - Indicates that the **System Owner has authorized** this access in the external system.  
- `system_owner_approval_date: DateTimeField(null=True)`  
  - When the System Owner approved this access assignment.  
- `system_owner_approver: ForeignKey(CustomUser, null=True, related_name="system_owner_access_approvals")`  
  - System Owner who authorized the access.  
- `legitimate_business_need: TextField(null=True)`  
  - Explicit **legitimate business need** for the access, as agreed with the System Owner.

These fields are stored **per user / per system** and complement the existing:

- `business_justification` (requester-side justification).  
- `approved_by`, `approval_date` (standard access approval workflow).

### 3.2 Access Assignment Form (Create/Update)

Template: `access_management/access_assignment_form.html`  
Views: `access_assignment_create`, `access_assignment_update`

New section: **“System Owner Authorization & Business Justification (4.4)”**:

- **Checkbox:** `system_owner_approved`
  - “System Owner has authorized this access”.  
- **Date/Time:** `system_owner_approval_date`
  - Records when the System Owner gave approval.  
- **Selector:** `system_owner_approver`
  - Dropdown of users to identify the System Owner.  
- **Text area:** `business_justification` (existing, required).  
- **Text area:** `legitimate_business_need`
  - Optional but recommended; captures the business need wording agreed with the System Owner.

All values are persisted on the `UserSystemAccess` instance and surfaced in reports.

### 3.3 Access Assignment Detail View

Template: `access_management/access_assignment_detail.html`

- **Approval Information card** shows:
  - Standard approval (approver, approval date, comments).  
  - **System Owner approval block**:
    - Badge if System Owner approval is **present** (with date and approver).  
    - Warning badge if System Owner approval is **missing**.  
- **Business Justification card**:
  - Displays **business justification** text.  
  - Shows **legitimate business need (4.4)** if recorded.

This gives auditors a per-assignment snapshot of **who approved**, **why**, and **when**.

---

## 4. User Matrix & Cross-System Mapping Enhancements (4.4 Evidence)

### 4.1 Cross-System Account Mapping View

View: `access_management.views.cross_system_account_mapping`  
Template: `access_management/templates/access_management/cross_system_account_mapping.html`

The cross-system matrix (employee × systems) is extended to reflect 4.4 metadata:

- For each active/approved `UserSystemAccess`:
  - **System Owner approval flags**:
    - `system_owner_approved` shown as:
      - **Green “Owner Approved” badge** when true.  
      - **Yellow “Owner Approval Missing” badge** when false.  
    - `system_owner_approval_date` displayed when available.  
  - **Legitimate business need**:
    - Short, truncated snippet displayed under the username in the matrix cell.  
  - Existing verification details remain:
    - Username verification status, verifier, verification date, and evidence links.  
    - Generic account flag (if applicable).

### 4.2 Cross-System Exports

Helpers: `build_cross_system_mapping_rows`,  
`export_cross_system_mapping_to_csv`, `export_cross_system_mapping_to_excel`

Each export row now includes the additional 4.4 fields:

- `system_owner_name` – current `System.system_owner` full name (if set).  
- `system_owner_approved` – “Yes/No”.  
- `system_owner_approval_date` – formatted date/time.  
- `business_justification` – full text from `UserSystemAccess`.  
- `legitimate_business_need` – full text from `UserSystemAccess`.

These columns appear in:

- `cross_system_account_mapping.csv`  
- `cross_system_account_mapping.xlsx`

This allows auditors to:

- Filter for **missing System Owner approvals**.  
- Review the **business need** and **legitimate need** for each assignment.  
- Correlate approvals with specific external system usernames.

---

## 5. SOP Documentation Module (`StandardOperatingProcedure`)

### 5.1 Model

Implemented in `documentation.StandardOperatingProcedure`:

- `title: CharField`  
  - e.g., “User Account Creation Process”, “Quarterly Access Review SOP”.  
- `version: CharField`  
  - Version identifier, e.g. “v1.0”, “2025-Q4”.  
- `content: TextField`  
  - Full SOP content (markdown or rich text).  
- `approved_by: ForeignKey(CustomUser, null=True)`  
  - Person who approved this SOP version.  
- `approved_date: DateTimeField(null=True)`  
  - When the SOP was approved.  
- `is_active: BooleanField`  
  - Marks which SOPs are currently in force.  
- `created_at: DateTimeField(auto_now_add=True)`.

- Exposed via Django admin (`documentation.admin.StandardOperatingProcedureAdmin`) with filtering/search (no autocomplete dependency).  
- Supports storing and versioning:
  - **User account creation/deletion/change procedures**.  
  - **System Owner approval process descriptions**.  
  - **Quarterly/monthly review routines** related to access management.

These records serve as **written SOP documentation** that can be exported or printed for audit.

---

## 6. How This Satisfies RHG 4.4 Requirements

**Audit Requirement → Implementation Mapping**

- **Document change management process for user account creation/deletion/changes in external systems**
  - `AccountChangeRequest` records each requested change, with type, system, target user, requester, approvals, and completion status.

- **Track that all changes to user accounts in external systems are documented and approved**
  - Change requests carry **System Owner** and optional **IT approvals**, plus workflow status.  
  - Access assignments (`UserSystemAccess`) hold per-system owner authorization flags.

- **Maintain written SOP documentation**
  - `StandardOperatingProcedure` model stores versioned SOPs for account management processes.

- **Document that System Owner authorizes user-id establishment**
  - `UserSystemAccess.system_owner_approved`, `system_owner_approver`, `system_owner_approval_date` capture owner sign-off for each access.  
  - Cross-system matrix visually highlights missing or present owner approvals.

- **Maintain User Matrix of systems and permissions**
  - Cross-system mapping (`cross_system_account_mapping` view + exports) shows:
    - Each employee’s username per system.  
    - Access type, status, generic flag, verification evidence.  
    - System Owner approval and legitimate business need for each assignment.

- **Document compliance across all systems (AD, PMS, POS, Doorlock, etc.)**
  - `System` model catalogs systems, while `UserSystemAccess` and `AccountChangeRequest` provide per-system assignments and change logs.  
  - Cross-system exports and SOP records are suitable as **audit evidence** across all in-scope systems.

---

## 7. Key URLs for 4.4 Evidence

- **Cross-System Account Mapping (User Matrix):**  
  - `/access-management/cross-system-mapping/`  
- **Access Assignment List & Detail:**  
  - `/access-management/assignments/`  
  - `/access-management/assignments/<id>/`  
- **Change Management Console:**  
  - `/change-management/requests/` (list)  
  - `/change-management/requests/create/` (new request)  
  - `/change-management/requests/<id>/` (detail)  
- **Change Requests (admin / optional):**  
  - `/admin/change_management/accountchangerequest/`  
- **SOP Documentation (admin):**  
  - `/admin/documentation/standardoperatingprocedure/`

These views, combined with the CSV/Excel exports, `AccountChangeRequest` records, and SOP entries, provide a complete, traceable evidence set for RHG 4.4 that can be handed directly to auditors.



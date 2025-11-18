# Access Approval Compliance – RHG 4.6

This document explains how the User Access Management System satisfies the RHG 4.6 control
“Routines to Ensure Employees Only Have Approved Access,” covering new data models, workflows,
dashboards, and evidence capture.

---

## Objectives

RHG 4.6 requires proof that:

1. Employees only have access that was explicitly approved.
2. External-system accounts are reviewed quarterly to confirm they match approved assignments.
3. Obsolete accounts (terminated, inactive, expired) are reviewed at least monthly and deactivated.
4. All access removals in external systems are documented and verified.
5. Unauthorized access is detected and remediated quickly across critical systems (AD, PMS, POS, etc.).

---

## Data Model Enhancements (`access_management/models.py`)

### `QuarterlyActiveUserReview`

Records quarterly reconciliation between external systems and approved assignments.

Key fields:
- `review_quarter`, `system`, `reviewed_by`, `review_date`
- Counts: `total_active_users_in_external_system`, `approved_users_count`, `unapproved_users_count`
- Evidence: `unapproved_users_list`, `discrepancies`, `review_completed`

### `MonthlyObsoleteAccountReview`

Captures monthly sweeps for obsolete accounts (terminated, inactive, stale review, expired).

Fields:
- `review_month`, `reviewed_by`, `review_date`
- `obsolete_accounts_identified` (JSON payload)
- Metrics: `accounts_deactivated_in_external_systems`, `accounts_pending_deactivation`
- `review_completed`, `notes`

### `AccessRemovalDocumentation`

Provides evidence that access was removed in external systems for a given `UserSystemAccess`.

Fields:
- `user_system_access`, `removed_from_external_system_date`, `removed_by`
- `removal_reason`, `verified_removal`, `verified_by`, `verified_date`, `notes`

Indexes + Django admin registrations were added so auditors can browse these records natively.

---

## Utilities (`access_management/utils.py`)

- `identify_obsolete_accounts()` – returns queryset buckets (terminated users, inactive >90 days, expired assignments still active, stale reviews >180 days) to drive monthly reviews/removals.
- `get_unapproved_access_records()` – surfaces active assignments missing approvals or system-owner authorization.

These helper outputs feed the dashboard metrics and JSON payloads stored in review logs.

---

## Forms (`access_management/forms.py`)

New ModelForms keep data-entry fast and consistent:

- `QuarterlyActiveUserReviewForm`
- `MonthlyObsoleteAccountReviewForm`
- `AccessRemovalDocumentationForm`

All use datetime pickers, Bootstrap classes, and sensible defaults (current quarter/month, timestamps, reviewer = current user).

---

## Dashboard UI (`access_management/access_approval_compliance.html`)

Route: `/access-management/access-approval-compliance/` (see `access_management/urls.py`)

Features:

1. **KPI Cards** – show total active assignments, detected unapproved access, quarterly/monthly review totals, pending removals.
2. **Forms** – inline sections to document quarterly active-user reviews, monthly obsolete-account reviews, and access removal evidence.
3. **Logs** – latest 20 quarterly reviews, 12 monthly reviews, 20 removal records, with badges indicating completion / verification status.
4. **Unapproved Access List** – highlights assignments missing IT or system-owner approvals.
5. **Obsolete Account Summary** – counts terminated users, inactive users, expired assignments, stale reviews to guide remediation.

All interactions post to the same view (`access_management/views.py::access_approval_compliance`), which routes to the appropriate form handler (`form_type` hidden input).

---

## Navigation & Admin

- Sidebar entry under **Access** → “Access Compliance (4.6)” (see `templates/navigation.html`).
- Django admin sections for each new model ensure back-office reporting is possible without custom SQL.

---

## Evidence Collection Workflow

1. **Quarterly Active User Review**
   - Pull external system list (AD, PMS, POS, etc.)
   - Enter counts and discrepancies using systems’ exports
   - Attach unapproved account details; mark complete when remediation finished

2. **Monthly Obsolete Account Review**
   - Use the built-in `identify_obsolete_accounts()` output or imported data
   - Document JSON list of accounts, counts deactivated/pending, and notes

3. **Access Removal Documentation**
   - Whenever a user leaves or changes roles, log the removal date, actor, reason
   - Mark “verified” when system owner/IT confirms external access is gone

4. **Unapproved Access Monitoring**
   - Dashboard surfaces any active assignment lacking approvals; review and remediate right away

5. **Audit Readiness**
   - Export via Django admin or database queries; logs include timestamps, reviewers, and notes
   - Combine with 4.5 quarterly review exports for comprehensive access governance evidence

---

## Future Extensions

- Integrate external system APIs or scheduled imports so `obsolete_accounts_identified` contains live data.
- Expand `get_unapproved_access_records()` to include automated cross-system reconciliations where APIs are available.
- Add CSV export buttons on the 4.6 dashboard similar to the 4.5 page for auditor-ready packets.

With these additions, the application now documents all required RHG 4.6 routines: quarterly active-user attestation, monthly obsolete-account reviews, and verified access removals, plus real-time detection of unapproved access across critical hotel systems.


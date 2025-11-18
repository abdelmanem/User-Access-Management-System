# Quarterly Access Review & Permission Change Documentation (RHG 4.5)

This document describes how the User Access Management System implements RHG 4.5 compliance
for quarterly permission reviews and external-system change documentation.

## Overview

The 4.5 control requires:

- Verified evidence that external permissions match internally approved permissions
- Quarterly review scheduling, logging, and owner confirmation
- Documentation that external permission changes were approved via change management
- Reporting that proves every active user is reviewed at least once per year

The application adds two core data models, a real-time dashboard, a bulk review generator,
and associated exports to satisfy these requirements.

---

## Data Model Enhancements

### `QuarterlyAccessReview`

Located in `access_management/models.py`, this model stores every quarterly review entry
with the following fields:

| Field | Description |
| ----- | ----------- |
| `review_quarter` | `YYYY-Q#` label (e.g., `2025-Q1`) |
| `reviewed_user` | Employee whose external permissions were verified |
| `system` | External system reviewed |
| `user_system_access` | Optional link to the underlying access assignment record |
| `reviewed_by` | IT reviewer who performed the check |
| `review_date` | Timestamp of the review |
| `approved_permissions` / `actual_permissions_in_external_system` | Comparison data for audit evidence |
| `matches_approved` | Boolean flag identifying discrepancies |
| `discrepancies` | Detailed notes if mismatches are detected |
| `system_owner` / `system_owner_confirmed` / `system_owner_confirmed_date` | Tracks system owner attestation |
| `review_completed` | Indicates remediation steps are finished |
| `created_at` | Auto timestamp for audit trail |

Indexes on `review_quarter`, `system`, and `reviewed_user` optimize dashboard filters and exports.

### `PermissionChangeDocumentation`

Also in `access_management/models.py`, this model tracks proof that permission changes in
external systems received the proper approvals.

Key fields:

- `user_system_access` reference
- `old_permissions` & `new_permissions`
- `changed_in_external_system_date`
- `has_approval` plus optional `approval_reference` to `AccountChangeRequest`
- `documented_by` and general `notes`

These entries are created through the RHG 4.5 dashboard and provide an audit-ready trail
linking change management tickets to actual external-system changes.

---

## UI & Workflow

### Quarterly Review Dashboard (`/access-management/quarterly-reviews/`)

Template: `access_management/templates/access_management/quarterly_access_reviews.html`

Highlights:

- KPI cards showing total reviews, completions, mismatches, and owner confirmations
- Annual coverage alert indicating progress toward reviewing every active user
- Filter controls (quarter, system, match status, owner confirmation, review status)
- Inline creation forms for single review entries and permission-change documentation
- Due/overdue reminders pulled from assignment `next_review_date`
- Export button (CSV) for audit evidence

Annual coverage percentages are calculated via `_annual_review_progress()` in
`access_management/views.py`. The logic compares distinct users reviewed in the current year
against all active users and shows whether the team is on track based on the current quarter.

### Bulk Quarterly Review Generator (`/access-management/quarterly-reviews/bulk/`)

Template: `access_management/templates/access_management/bulk_quarterly_reviews.html`

Use cases:

- Auto-select multiple assignments per system for a given quarter
- Preview which users will receive a review entry (ensures no duplicates)
- Generate records in a single action (with optional “match approved permissions” and “mark as completed” switches)
- Update underlying assignments’ `last_review_date` / `next_review_date` to keep scheduling accurate
- Surface skipped assignments if a review already exists or data is incomplete

Scheduler logic lives in `_select_assignments_for_bulk()` and `_update_assignment_review_schedule()`
within `access_management/views.py`. The form used on this page is `BulkQuarterlyReviewForm`
in `access_management/forms.py`.

### Navigation & Routing

- Sidebar links under **Access**:
  - `Quarterly Reviews (4.5)` → dashboard
  - `Bulk Reviews` → generator
- URLs declared in `access_management/urls.py`:
  - `/access-management/quarterly-reviews/`
  - `/access-management/quarterly-reviews/bulk/`

---

## User Guidance

1. **Document single reviews**
   - Navigate to the dashboard
   - Use the “Log Quarterly Review” form to capture approvals, actual permissions, and owner confirmation
   - Add permission-change evidence when updates occur outside the system

2. **Bulk-generate reviews**
   - Visit the Bulk generator, select quarter + system + number of users
   - Preview the auto-selected assignments
   - Click “Generate Reviews” to create entries and update scheduling metadata

3. **Monitor coverage**
   - Track annual progress on the dashboard banner
   - Use filters + CSV export for audit prep
   - Address mismatches and missing owner confirmations flagged in the list

4. **Change management linkage**
   - When documenting permission changes, attach the relevant `AccountChangeRequest`
   - Ensure `has_approval` is true once change management signs off

---

## Compliance Evidence

- **Quarterly review log**: Proves who was reviewed, when, by whom, and whether permissions match approvals.
- **System owner confirmation**: Captured as boolean/date fields plus notes.
- **Change management linkage**: `PermissionChangeDocumentation` entries can reference `AccountChangeRequest` IDs.
- **Annual coverage tracker**: Shows auditors that all active users are reviewed each year and highlights gaps.
- **Exports**: CSV files for both reviews and change logs provide ready-made audit artifacts.

This implementation closes the RHG 4.5 compliance gaps identified in `AUDIT_COMPLIANCE_ANALYSIS.md`
by providing fully documented, reportable, and repeatable review routines tied directly to the
core User Access Management workflow.



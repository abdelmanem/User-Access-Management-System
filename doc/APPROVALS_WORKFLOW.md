**Approvals Workflow — Change Management & Access Management**

Overview
- This document describes how approvals work in the project and how the two approval types relate.
- Two separate workflows exist: Change Management (account lifecycle) and Access Management (access/assignment approvals). A unified dashboard aggregates pending items from both.

1) Change Management (Account Change Requests)
- Model: `AccountChangeRequest` (`change_management/models.py`). Key fields:
  - `change_type` — Create / Modify / Delete / Suspend
  - `system_owner` — user who must authorize the request
  - `system_owner_approved` (bool) and `system_owner_approval_date`
  - `it_approval` and `it_approval_date` (optional IT approver)
  - `status` — one of `Pending`, `Approved`, `Rejected`, `Completed`
  - `completed_in_external_system` and `completed_date`
- Typical flow:
  1. Request created with `status='Pending'`.
  2. System Owner reviews → sets `system_owner_approved=True` and optionally `system_owner_approval_date`.
  3. If an IT approver is required, IT sets `it_approval` and `it_approval_date`.
  4. Once implemented in external system, mark `completed_in_external_system=True` and set `completed_date`; change `status` to `Completed`.
- Views & templates:
  - List: `change_management:change_request_list`
  - Detail: `change_management:change_request_detail`
  - Edit/Manage: `change_management:change_request_update` (use this to approve/manage)

2) Access Management (Access Assignments & Approval Workflows)
- Models involved (examples): `UserSystemAccess`, `ApprovalWorkflow`, workflow `Step` objects (see `access_management/models.py` and `access_management/views_new.py`). Key fields:
  - `UserSystemAccess.status` (e.g., `Pending`, `Approved`, etc.)
  - `approved_by` — direct approver (optional)
  - `system.system_owner` — system owner for that system
  - `ApprovalWorkflow` — groups `UserSystemAccess` into a multi-step approval process
  - Workflow steps reference an `approver` (user) and `step_number`
- Two variants:
  - Direct assignment: `UserSystemAccess.status='Pending'`, a single approver acts or the system owner approves.
  - Workflow-based: `ApprovalWorkflow` with ordered steps; approvers act in sequence.
- Views & templates:
  - Unified approvals page (new): `/access-management/approvals/` → `access_management:approval_dashboard`
  - Single assignment detail: `access_management:access_assignment_detail`
  - Approve workflow step: `access_management:approve_access_request`

3) Unified Approval Dashboard
- Purpose: show pending Change Requests and Access Assignments in one place for reviewers.
- Implementation (where to look):
  - View: `access_management/views_new.py` → `approval_dashboard` (now collects:
    - `AccountChangeRequest` with `status='Pending'` filtered for the current user (system owner or IT approver),
    - `ApprovalWorkflow` steps where the current user is an approver,
    - `UserSystemAccess` direct pending assignments the user can approve.)
  - Template: `access_management/templates/access_management/approval_dashboard.html` — displays two card types: "CHANGE REQUEST" and "ACCESS REQUEST" with direct links to review/approve.
- Behavior:
  - Items are filtered by user role: superuser/staff see all; regular users see only items where they are the approver or system owner.
  - Items are sorted by creation time (most recent first).
  - Dashboard auto-refreshes (30s) to surface new items.

4) How to clear pending items
- For Change Requests: open the change request detail (`change_management:change_request_detail`), have the System Owner set approval fields (or the IT approver set `it_approval`), and update `status` as appropriate.
- For Access Assignments: either approve via direct assignment detail (`access_assignment_detail`) or follow the workflow step (`approve_access_request`) to move to next step or mark approved.

5) Permissions & roles
- Superusers/staff: can view/approve all pending items.
- System Owner: visible for items where `system.system_owner` equals the user.
- IT Approver: visible for change requests where `it_approval` is set to the user.
- Workflow approver: visible for workflow steps assigned to the user.

6) Quick links (templates & endpoints)
- Unified dashboard: `/access-management/approvals/` → `access_management:approval_dashboard`
- Change requests list/detail/manage: `change_management:change_request_list`, `change_management:change_request_detail`, `change_management:change_request_update`
- Access assignment detail & approval: `access_management:access_assignment_detail`, `access_management:approve_access_request`

7) Notes for developers
- The unified dashboard collects different model types and represents them in a common structure for rendering. See `access_management/views_new.py` for the aggregation logic.
- If you want change requests to automatically approve corresponding access assignments, implement a post-approval hook in `change_management/signals.py` or the change request approval view that locates matching `UserSystemAccess` records and sets `status='Approved'` (ensure you record audit logs).
- Template style: cards are visually separated and link to the native workflows for each item.

If you want, I can:
- Add this new doc into `mkdocs.yml` navigation.
- Implement an automatic post-approval hook to propagate approvals from Change Requests to Access Assignments.

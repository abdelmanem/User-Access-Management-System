# Access Assignment Deletion Workflow Changes

## Overview
Updated the access assignment deletion flow to enforce approval requirements and maintain full audit compliance with RHG 4.4 Change Management requirements. Deletions no longer bypass the approval process.

## Changes Made

### 1. **Soft-Delete Implementation** (`access_management/models.py`)
- Added `ActiveAccessManager` custom manager to automatically exclude soft-deleted records
- `UserSystemAccess.objects` now excludes `is_deleted=True` records by default
- `UserSystemAccess.all_objects` provides access to all records including deleted ones
- Fields already existed for tracking deletion:
  - `is_deleted` (boolean)
  - `deleted_date` (datetime)
  - `deleted_by` (ForeignKey to CustomUser)
  - `deletion_reason` (text)

### 2. **Updated Helper Function** (`access_management/views.py`)
- **`_create_change_request_for_assignment()`** now accepts optional `change_type` parameter
- Defaults to `CHANGE_TYPE_CREATE` when not specified (backward compatible)
- Supports `CHANGE_TYPE_DELETE` for deletion workflows
- Sets appropriate `business_justification` based on change type

### 3. **Single Delete Flow** (`access_management/views.py`)
**Function:** `access_assignment_delete()`

**Old Flow:**
- Direct hard-delete
- Only AccessHistory entry created with action='Revoked'
- No change request created

**New Flow:**
- Soft-delete: sets `is_deleted=True`, `deleted_date`, `deleted_by`, `deletion_reason`
- Creates AccessHistory entry with action='Deletion Requested'
- Creates `AccountChangeRequest` with `CHANGE_TYPE_DELETE`
- Redirects to change request detail page for approval workflow
- User sees message: "Deletion requested and change request created for approval"

### 4. **Bulk Delete Flows** (`access_management/views.py`)
**Functions:** `user_access_assignments()` and `system_access_assignments()`

**Bulk Delete Changes:**
- Per-assignment soft-deletion (not batch delete)
- Each assignment gets its own change request for deletion
- AccessHistory action changed to 'Deletion Requested'
- Success message updated: "Successfully requested deletion for X assignments. Change requests have been created for approval."

### 5. **Delete Confirmation Template** (`access_management/templates/access_management/access_assignment_confirm_delete.html`)
**UI Enhancements:**
- Alert changed from "danger" (red) to "warning" (orange) with updated messaging
- Replaces "Impact of Deletion" section with "What Happens Next?" section
- Shows approval workflow step-by-step
- Highlights audit compliance and RHG 4.4 alignment
- Button changed from "Delete" (red/danger) to "Request Deletion" (orange/warning)
- Confirmation checkbox text updated to reflect approval requirement
- Deletion reason field labeled as recommended (vs optional)
- Enhanced help text explaining where reason appears in change request

## Approval Workflow for Deletions

When a user requests deletion:

1. **Request Created:** Soft-deleted assignment + change request created
2. **System Owner Review:** System Owner receives notification to approve/reject
3. **IT Approval:** IT approver confirms the deletion is valid
4. **Approval Completion:** Upon all approvals:
   - Change request status → "Completed"
   - Can create hard-delete or mark as fully deleted (policy decision)
5. **Audit Trail:** Full history maintained with:
   - Who requested deletion and when
   - Reason for deletion
   - Approvers and timestamps
   - Complete change request record

## Database Queries Impact

- **Default queries** (via `UserSystemAccess.objects`) exclude soft-deleted records
- **Include deleted** use `UserSystemAccess.all_objects` explicitly
- No migration needed (soft-delete fields already exist)
- Queries automatically filtered at ORM level

## Backward Compatibility

- Helper function `_create_change_request_for_assignment()` remains backward compatible
- Existing create flows unaffected (default change_type still 'Create')
- No breaking changes to model or API

## Testing Considerations

1. **Single Delete:** Request deletion → verify soft-delete occurs → verify change request created
2. **Bulk Delete:** Multiple deletions → each gets own change request → status message shows count
3. **Queries:** Verify soft-deleted records excluded from default lists
4. **Approval Flow:** Approve/reject deletion change request → verify audit trail
5. **History:** Verify AccessHistory shows 'Deletion Requested' action

## Compliance Benefits

✅ **RHG 4.4 Compliance:** All deletions now go through change management  
✅ **Audit Trail:** Complete history of deletion requests and approvals  
✅ **Approval Enforcement:** System Owner and IT approver must sign off  
✅ **Reason Capture:** Business justification recorded for all deletions  
✅ **Data Retention:** Soft-delete preserves historical records  
✅ **Traceability:** Full chain of custody maintained  

## Configuration/Policy Notes

The actual hard-deletion can be triggered by:
- Automatic process after change request approval completion
- Scheduled task (daily/weekly cleanup of approved deletions)
- Manual admin action from change request detail page

Current implementation: soft-delete only (hard-delete deferred to separate policy).

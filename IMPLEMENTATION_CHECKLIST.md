# Deletion Workflow Implementation Checklist

## Code Changes Completed ✅

### Backend Changes
- [x] Modified `_create_change_request_for_assignment()` to accept optional `change_type` parameter
- [x] Updated `access_assignment_delete()` to soft-delete and create change request
- [x] Updated `user_access_assignments()` bulk_delete to soft-delete and create change requests
- [x] Updated `system_access_assignments()` bulk_delete to soft-delete and create change requests
- [x] Added `ActiveAccessManager` to exclude soft-deleted records by default
- [x] Set `UserSystemAccess.objects` to use custom manager
- [x] Added `UserSystemAccess.all_objects` for accessing deleted records

### Template Changes
- [x] Updated `access_assignment_confirm_delete.html`:
  - Alert message updated (danger → warning)
  - Workflow explanation section added
  - Compliance section added
  - Button text updated ("Request Deletion")
  - Confirmation checkbox text updated
  - Deletion reason field marked as recommended

### Database
- [x] No migration needed (soft-delete fields already exist in model)
- [x] Soft-delete fields utilized: `is_deleted`, `deleted_date`, `deleted_by`, `deletion_reason`

### Documentation
- [x] Created `DELETION_WORKFLOW_CHANGES.md` with full details
- [x] Workflow documented
- [x] Compliance benefits listed
- [x] Testing considerations outlined

## Pre-Deployment Verification

### Code Quality
- [x] No syntax errors in views.py
- [x] No syntax errors in models.py
- [x] No import errors
- [x] Manager implementation follows Django best practices

### Database State
- [ ] Verify soft-delete fields present in UserSystemAccess model
  ```sql
  SELECT is_deleted, deleted_date, deleted_by_id, deletion_reason 
  FROM access_management_usersystemaccess LIMIT 1;
  ```
- [ ] Verify no existing records have `is_deleted=True` before deployment
  ```sql
  SELECT COUNT(*) FROM access_management_usersystemaccess WHERE is_deleted = TRUE;
  ```

### Feature Testing Required

#### Single Deletion Flow
- [ ] Navigate to access assignment detail
- [ ] Click "Delete" button
- [ ] Review confirmation page (check updated messaging)
- [ ] Enter deletion reason
- [ ] Check confirmation checkbox
- [ ] Click "Request Deletion" button
- [ ] Verify:
  - Redirect to change request detail page
  - Change request has type "Delete"
  - Status is "Pending"
  - System Owner is assigned
  - Message displays success

#### Verify Soft Delete
- [ ] Check database:
  ```sql
  SELECT is_deleted, deleted_date, deleted_by_id FROM access_management_usersystemaccess 
  WHERE id = <test_record_id>;
  ```
- [ ] Verify soft-delete fields populated

#### Verify Exclusion from Lists
- [ ] Go to Access Assignment List
- [ ] Verify deleted assignment NOT shown
- [ ] Go to User Access Assignments
- [ ] Verify deleted assignment NOT shown
- [ ] Go to System Access Assignments
- [ ] Verify deleted assignment NOT shown

#### Bulk Delete Flow
- [ ] Select multiple assignments from user access view
- [ ] Choose "Bulk Delete" action
- [ ] Verify each assignment soft-deleted
- [ ] Verify change request created for each
- [ ] Check success message count

#### Change Request Approval
- [ ] Open created change request
- [ ] Verify:
  - Change type is "Delete"
  - Business justification contains deletion reason
  - System Owner can approve/reject
  - Status transitions to "Completed" on approval

#### AccessHistory Verification
- [ ] Check AccessHistory records for soft-deleted assignment
- [ ] Verify action = "Deletion Requested"
- [ ] Verify action_description contains requester name

#### Manager Testing (Django shell)
```python
from access_management.models import UserSystemAccess

# Default query should exclude soft-deleted
active_count = UserSystemAccess.objects.count()

# all_objects should include soft-deleted
all_count = UserSystemAccess.all_objects.count()

# all_count should be >= active_count
assert all_count >= active_count
```

### Regression Testing
- [ ] Create new access assignment (normal flow) - should still work
- [ ] Approve access assignment - should still work
- [ ] Reject access assignment - should still work
- [ ] Update access assignment - should still work
- [ ] Revoke access assignment (if separate from delete) - should still work

### Performance Validation
- [ ] Access Assignment List loads in reasonable time
- [ ] Bulk delete with 50+ assignments completes
- [ ] No N+1 queries on list views

## Post-Deployment Tasks

### Production Checklist
- [ ] Backup database before deployment
- [ ] Deploy code changes
- [ ] Test deletion workflow in production environment
- [ ] Monitor logs for any errors
- [ ] Verify existing reports/exports still work
- [ ] Update user documentation/training materials
- [ ] Notify stakeholders of change in workflow

### Monitoring
- [ ] Set up alerts for failed change request creation
- [ ] Monitor pending deletion change requests count
- [ ] Track average time-to-approval for deletions

### Rollback Plan
If issues found:
1. Revert code changes to previous version
2. Soft-deleted records still queryable via `all_objects`
3. Hard-deleted records are permanently lost (so backup is critical)
4. Change requests created remain as historical records

## Documentation To Update

- [ ] User guide: explain new deletion workflow
- [ ] System owner documentation: note deletion approval requirement
- [ ] Admin guide: document soft-delete manager usage
- [ ] API documentation (if applicable): document change_type parameter
- [ ] Help desk: update ticket templates for deletion requests

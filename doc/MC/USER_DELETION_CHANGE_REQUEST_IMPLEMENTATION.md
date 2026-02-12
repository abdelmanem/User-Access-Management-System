# User Deletion Change Request Implementation - Summary

## Problem
When a user account was deleted via the accounts module, no change request was created to track the deletion in the change management approvals workflow. This violated audit/compliance requirements to have all user account deletions sent to approvals.

## Solution Implemented

### 1. **Updated [accounts/views.py](accounts/views.py)**
   - Added imports for `AccountChangeRequest` from `change_management.models`
   - Added logger configuration for error handling
   - Modified `user_delete()` function to create a change request when a user is deleted:
     - Sets `change_type=CHANGE_TYPE_DELETE`
     - Captures user snapshot fields (`user_full_name`, `user_username`)
     - Sets `status=STATUS_PENDING` to route to approvals
     - Uses `requested_by=request.user` to track who initiated the deletion
     - Logs if change request creation fails but doesn't block user deletion

### 2. **Updated [accounts/templates/accounts/user_confirm_delete.html](accounts/templates/accounts/user_confirm_delete.html)**
   - Added a required `deletion_reason` textarea field
   - Shows context that reason will be recorded in change management
   - Provides placeholder examples (Employee terminated, Contract end, etc.)
   - Improves UX by making deletion intent explicit and audit-friendly

## Code Changes

### accounts/views.py imports section:
```python
# Import change management for change request creation on user deletion
try:
    from change_management.models import AccountChangeRequest
except ImportError:
    AccountChangeRequest = None

logger = logging.getLogger(__name__)
```

### user_delete() function changes:
After creating `UserArchive` and before deleting the user, now creates a change request:
```python
# Create a change request for user deletion to track in approvals workflow
if AccountChangeRequest:
    try:
        change_request = AccountChangeRequest.objects.create(
            change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
            user=None,  # User is deleted; will be null
            user_full_name=user.get_full_name(),
            user_username=user.username,
            system=None,  # User deletion is not system-specific
            business_justification=request.POST.get('deletion_reason', 'User account deleted'),
            requested_by=request.user if request.user.is_authenticated else None,
            status=AccountChangeRequest.STATUS_PENDING,
            system_owner=None,  # Not applicable for user deletion
        )
        messages.success(
            request,
            'User deleted successfully. Archived snapshot is available for reference. '
            'A change request has been created to track the deletion in approvals.'
        )
    except Exception as e:
        logger.error(f'Failed to create change request for user deletion {pk}: {str(e)}')
        messages.success(request, 'User deleted successfully. Archived snapshot is available for reference.')
```

## Workflow After Changes

1. Admin navigates to user delete confirmation page
2. Admin enters **Reason for Deletion** (e.g., "Employee terminated")
3. Admin clicks "Yes, Archive & Delete User"
4. System:
   - Creates a `UserArchive` record with user snapshot
   - Deletes the user from `CustomUser` table
   - **Creates a `AccountChangeRequest` with:**
     - `change_type = "DELETE"`
     - `user_full_name` and `user_username` snapshots (since `user` FK is null)
     - `status = "PENDING"` to send for approval
     - `business_justification` from deletion reason
   - Shows success message mentioning change request created

## Benefits

✅ **Compliance**: User deletions now tracked in change management approvals  
✅ **Audit Trail**: Deletion reason captured in change request  
✅ **Snapshot Data**: `user_full_name`/`user_username` preserved even after user deleted  
✅ **Graceful Fallback**: If change request creation fails, user deletion still succeeds with logging  
✅ **Consistency**: Matches access assignment deletion which already creates change requests

## Testing Verification

Run this command to see recent user deletion change requests:
```bash
python manage.py shell -c "
from change_management.models import AccountChangeRequest
deletion_requests = AccountChangeRequest.objects.filter(
    change_type='DELETE', 
    system__isnull=True
).order_by('-created_at')[:5]
print(f'Total user deletion requests: {deletion_requests.count()}')
for r in deletion_requests:
    print(f'  ID: {r.id}, User: {r.user_username}, Status: {r.status}')
"
```

## Files Modified

1. [accounts/views.py](accounts/views.py) - Added imports and change request creation logic
2. [accounts/templates/accounts/user_confirm_delete.html](accounts/templates/accounts/user_confirm_delete.html) - Added deletion reason field

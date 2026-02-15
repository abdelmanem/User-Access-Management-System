# 🚨 CONFIRMED: Change Management Rejection Issue 

**Status:** ✗ **CRITICAL ISSUE FOUND**  
**Date:** February 12, 2026  
**Verified:** YES - Real data in system shows the problem

---

## 📋 Issue Summary

When a System Owner or IT rejects a change request for **user creation/deletion**, the actual action (user created/deleted) has **already been executed** and cannot be reversed. The rejection is only an audit record with no control effect.

### Live Example from Your System

```
Change Request #16: User Deletion
├─ Change Type: Delete
├─ Status: REJECTED ✗
├─ User: "Auto Test 823344"
├─ User exists in DB: NO (already deleted)
├─ Rejection Reason: "Automated reject 2"
└─ Impact: INEFFECTIVE - user gone despite rejection
```

---

## 🔴 ROOT CAUSE

### Two Different Architectural Patterns in Your System

| Pattern | Feature | Implementation | Result |
|---------|---------|-----------------|--------|
| **Reactive** | User Create/Delete | Signal fires AFTER action | ❌ Rejection ineffective |
| **Proactive** | Access Assignment | Status=Pending BEFORE approval | ✅ Rejection effective |

### Code Flow Comparison

**USER DELETION (WRONG - Reactive):**
```python
# Step 1: Action executed immediately
user.delete()  # User gone from DB

# Step 2: Signal fires AFTER deletion
@receiver(post_delete, sender=CustomUser)
def track_user_deletion(sender, instance, **kwargs):
    # Too late! User already deleted
    AccountChangeRequest.objects.create(
        status='Pending'  # Just records it
    )
```

**ACCESS ASSIGNMENT (RIGHT - Proactive):**
```python
# Step 1: Create in Pending state
access = UserSystemAccess.objects.create(
    status='Pending'  # User CANNOT use yet
)

# Step 2: Create change request for audit
change_req = _create_change_request_for_assignment(access)

# Step 3: Approval gates activation
access.approve_access()  # Only changes status

# Step 4: Additional activation step needed
access.activate_access()  # NOW user can use
```

---

## 📊 What Happens in Each Workflow

### User Deletion Rejection (Ineffective)
```
┌─────────────────────────────────────────────────────────────┐
│ Timeline of Rejection NOT Working                          │
├─────────────────────────────────────────────────────────────┤
│ T=0:   Admin clicks "Delete User"                          │
│ T=1:   user.delete() executed immediately ✓               │
│        → User GONE from database                           │
│ T=2:   Change request created (signal fires)              │
│        → Status: Pending                                   │
│ T=3:   Email sent: "Change requires approval"             │
│ T=7:   System Owner reviews and clicks REJECT ✗           │
│        → Change request.status = 'Rejected'               │
│        → Approval notes saved                             │
│        → User is STILL GONE (no rollback)                 │
│                                                             │
│ Result: Rejection recorded but ineffective                │
└─────────────────────────────────────────────────────────────┘
```

### Access Assignment Rejection (Effective)
```
┌─────────────────────────────────────────────────────────────┐
│ Timeline of Rejection Working Correctly                    │
├─────────────────────────────────────────────────────────────┤
│ T=0:   Manager/HR requests access                         │
│ T=1:   Access created with status='Pending' ✓            │
│        → User CANNOT use (not active)                     │
│ T=2:   Change request created (for audit)                │
│        → Status: Pending                                  │
│ T=3:   Email sent: "Access requires approval"            │
│ T=7:   System Owner reviews and clicks REJECT ✓          │
│        → Access.status = 'Rejected'                       │
│        → User never gets the access                       │
│        → Rejection prevents activation                    │
│                                                             │
│ Result: User blocked from getting access!                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Analysis of Your System

### Change Management Implementation

**File:** [change_management/views.py](change_management/views.py#L359) - `change_request_quick_reject()`

```python
def change_request_quick_reject(request, pk):
    change_request = get_object_or_404(AccountChangeRequest, pk=pk)
    
    # When System Owner rejects:
    change_request.status = AccountChangeRequest.STATUS_REJECTED
    change_request.system_owner_approved = False
    change_request.system_owner_approval_notes = rejection_reason
    change_request.save()
    
    # ✗ NO ROLLBACK
    # ✗ NO UNDO OF ORIGINAL ACTION
    # ✗ Just changes status in database
```

**What it does:**
- ✅ Updates change request status to "Rejected"
- ✅ Records rejection reason
- ✅ Creates audit trail
- ❌ **Does NOT undo the actual user/access action**

### Why The Issue Exists

The system uses **Django signals** for change tracking:

**File:** [change_management/signals.py](change_management/signals.py#L50)

```python
@receiver(post_delete, sender=CustomUser)
def track_user_deletion(sender, instance, **kwargs):
    """Fires AFTER user deleted."""
    # At this point, user is already gone
    AccountChangeRequest.objects.create(
        change_type=CHANGE_TYPE_DELETE,
        status=STATUS_PENDING,
        # ... snapshots captured, but user is gone
    )
```

**The Problem:**
- Signal is `post_delete` - fires AFTER deletion happens
- No way to prevent or rollback the action
- Change request is just an audit log, not a control gate

---

## 📈 Scope of the Issue

### Which Operations Are Affected?

| Operation | Status | Issue | Evidence |
|-----------|--------|-------|----------|
| User Creation | ❌ BROKEN | No pre-approval gate | Signal fires after creation |
| User Deletion | ❌ BROKEN | No pre-approval gate | Change request #16: user deleted despite rejection |
| User Modification | ⚠️ PARTIAL | Some fields tracked after change | Signals catch changes too late |
| Access Assignment | ✅ WORKING | Proper Pending status gate | Access blocked until approved |
| Access Approval | ✅ WORKING | Status transitions prevent use | Rejection keeps access Pending |

### Non-Compliance Impact

**RHG 4.4 Requirement:**
> "All account creations/modifications/deletions must be requested AND approved before execution"

**Your System Status:**
- ✅ **Access**: Compliant (approval gates before activation)
- ❌ **User Ops**: Non-compliant (approval after execution)

---

## 💡 Solutions

### Option 1: Soft Delete + Rollback ⭐ RECOMMENDED

Implement reversible deletion with approval-gated execution:

```python
# Instead of hard delete immediately:
# 1. Create DeletionRequest (Pending)
# 2. System Owner approves
# 3. Only THEN execute deletion
# 4. If rejected, restoration logic can run

class DeletionRequest(models.Model):
    user = ForeignKey(CustomUser)
    status = CharField(choices=[
        'Pending',
        'Approved by Owner',
        'Approved by IT',
        'Executed',  # Only here is deletion allowed
        'Rejected',
        'Rolled Back'  # Can restore from soft-delete
    ])

def handle_rejection(deletion_request):
    """Rollback capability"""
    if deletion_request.status == 'Rejected':
        deletion_request.user.is_deleted = False
        deletion_request.user.save()
```

**Pros:**
- ✅ Fully reversible
- ✅ RHG 4.4 compliant
- ✅ Complete audit trail
- ✅ Matches access workflow pattern

**Cons:**
- Requires schema changes (soft-delete flags)
- More complex logic

---

### Option 2: Pre-Approval Workflow

Change user operations to require change request BEFORE action:

```python
# Create change request first
change_req = AccountChangeRequest.objects.create(
    change_type='Delete',
    status='Pending'
)

# Then review
system_owner.approve(change_req)

# ONLY then execute
if change_req.status == 'Approved':
    user.delete()
```

**Pros:**
- ✅ Simple to implement
- ✅ Follows existing pattern
- ✅ No schema changes needed

**Cons:**
- Blocks immediate deletions (workflow overhead)
- Not reversible if executed

---

### Option 3: Hybrid - Soft Delete Only

Use soft-delete without pre-approval: **Not recommended** - still not compliant but better than current state

---

## ✅ Immediate Actions

1. **Document the Issue** (DONE - this file)
2. **Stop Using Hard Deletes** - Switch to soft-delete pattern
3. **Update User Deletion View** - Require approval first
4. **Update Signals** - Check if they're catching intended changes
5. **Add Rollback Logic** - For when requests are rejected
6. **Update Tests** - Verify rejection workflow

---

## 🔗 Key Code Locations

| File | Line | Issue |
|------|------|-------|
| [accounts/views.py](accounts/views.py#L679) | 679 | user_delete() - no pre-approval |
| [change_management/signals.py](change_management/signals.py#L50) | 50 | post_delete signal (too late) |
| [change_management/views.py](change_management/views.py#L359) | 359 | reject_change() - no rollback |
| [access_management/views.py](access_management/views.py#L2730) | 2730 | approve_access() (CORRECT) |
| [access_management/models.py](access_management/models.py#L584) | 584 | approve_access state transition (CORRECT) |

---

## 📝 Test Case

**File:** [test_rejection_issue.py](test_rejection_issue.py)

Run this to verify the issue in your system:
```bash
python manage.py shell -c "
from change_management.models import AccountChangeRequest
rejected = AccountChangeRequest.objects.filter(
    status='Rejected',
    change_type='Delete'
).first()
if rejected:
    print(f'User exists: {rejected.user is not None}')
    print(f'Request status: {rejected.status}')
    print('→ If user=None but status=Rejected, issue is confirmed')
"
```

---

## 🎯 Summary Table

| Aspect | Current | Should Be | Gap |
|--------|---------|-----------|-----|
| User delete execution | Before approval | After approval | ❌ CRITICAL |
| Rejection prevents action | NO | YES | ❌ CRITICAL |
| Rollback on reject | NO | YES | ❌ CRITICAL |
| Audit trail | YES | YES | ✅ |
| Approval recorded | YES | YES | ✅ |
| RHG 4.4 Compliance | PARTIAL | FULL | ❌ CRITICAL |

---

## 🚀 Next Steps

1. Choose remediation approach (Soft Delete recommended)
2. Design new user lifecycle state machine
3. Update [accounts/views.py](accounts/views.py) user_delete() function
4. Add rollback/restoration logic
5. Update signals to respect approval gates
6. Add comprehensive tests for rejection workflows
7. Update documentation and user training

---

## 📞 Questions to Consider

1. **How many users have been deleted despite rejection?** → Check AccountChangeRequest with status='Rejected'
2. **Can we recover deleted users?** → Only if UserArchive records exist
3. **Who needs to approve deletions?** → System Owner? IT Admin? Both?
4. **What about other user modifications?** → Should those also require approval?
5. **Timeline for fix?** → High priority for compliance

---

**Document Generated:** February 12, 2026  
**Issue Status:** CONFIRMED AND ANALYZED  
**Severity:** CRITICAL  
**Files Created:**
- [CHANGE_MANAGEMENT_REJECTION_ISSUE_ANALYSIS.md](CHANGE_MANAGEMENT_REJECTION_ISSUE_ANALYSIS.md)
- [WORKFLOW_COMPARISON_VISUAL.md](WORKFLOW_COMPARISON_VISUAL.md)  
- [test_rejection_issue.py](test_rejection_issue.py)
- [check_rejected_request.py](check_rejected_request.py)

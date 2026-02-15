# Change Management Rejection Issue Analysis

**Date:** February 12, 2026  
**Issue:** When System Owner or IT rejects a change request, the underlying user/access has **already been created or deleted**, making the rejection ineffective.

---

## 🔴 PROBLEM SUMMARY

### Current Behavior (Reactive Approach)
```
ACTION HAPPENS FIRST                           APPROVAL HAPPENS SECOND
┌──────────────────────────────────┐          ┌─────────────────────────────┐
│ User Created/Deleted/Access      │          │ Change Request Created      │
│ Change Executed Immediately      │   ──→    │ Sent for Approval           │
│ ✗ NO GATE/CONTROL                │          │ Too Late to Prevent Action  │
└──────────────────────────────────┘          └─────────────────────────────┘
```

**Result:** Even if change request is rejected, the action already happened.

---

## 📋 DETAILED BREAKDOWN BY FEATURE

### 1️⃣ USER CREATION

**File:** [accounts/views.py](accounts/views.py#L679) - `user_delete()` function

**Current Flow:**
```python
# When user is DELETED:
1. UserArchive created (snapshot)
2. User DELETED from database ✓ (DONE)
3. Change request created (PENDING) ← Too late!
4. If rejected later, user is already gone ✗
```

**Code Reference:**
```python
# accounts/views.py (lines 679-709)
- User is deleted: user.delete()
- THEN change request created: AccountChangeRequest.objects.create()
- Status = STATUS_PENDING (waiting for approval)
- But user is already gone from database!
```

**Impact:**
- ❌ Deletion cannot be reversed if rejected
- ❌ No approval gate before deletion
- ❌ Change request is just audit trail, not control mechanism

---

### 2️⃣ USER DELETION (from signals)

**File:** [change_management/signals.py](change_management/signals.py#L50) - `track_user_creation_or_modification()`

**Current Flow:**
```python
# When user is CREATED (signal fires):
@receiver(post_save, sender=CustomUser)
def track_user_creation_or_modification(sender, instance, created, **kwargs):
    if created:
        # User is CREATED in database ✓ (DONE)
        # THEN change request created (PENDING)
        AccountChangeRequest.objects.create(
            change_type=CHANGE_TYPE_CREATE,
            status=STATUS_PENDING  ← User already exists!
        )
```

**Impact:**
- ❌ User already active when change request is pending
- ❌ User can access systems while awaiting approval
- ❌ Rejection has no effect on already-created user

---

### 3️⃣ ACCESS ASSIGNMENTS (Better Design)

**File:** [access_management/views.py](access_management/views.py#L1996)

**Current Flow:**
```
1. Access assignment CREATED with status='Pending'
2. Change request CREATED (also PENDING)
3. System Owner/IT MUST APPROVE before activation
4. Only after approval can access be activated
```

**Code Reference:**
```python
# access_management/views.py (lines 1996-2005)
access_assignment = UserSystemAccess.objects.create(
    status='Pending',  ← NOT yet active
    # ... 
)
change_request = _create_change_request_for_assignment(access_assignment, request.user)
```

**Status Lifecycle:**
```
Pending → Approved → Active
         ↓
      Rejected (blocks activation)
```

**Impact:**
- ✅ Access created but NOT active
- ✅ Change request gates activation
- ✅ Rejection prevents user from ever getting access

---

## 🔍 REJECTION WORKFLOW - What Actually Happens

### Change Request Rejection (Currently)
**File:** [change_management/views.py](change_management/views.py#L359)

```python
def change_request_quick_reject(request, pk):
    # Owner rejection
    if rejection_type == "owner":
        change_request.status = AccountChangeRequest.STATUS_REJECTED
        change_request.system_owner_approved = False
        change_request.save()  ← Just changes status!
        # NO ROLLBACK OF ACTUAL ACTION
```

**What it does:**
- ✅ Changes `status` to "Rejected"
- ✅ Records rejection reason
- ✅ Logs the rejection
- ❌ **Does NOT undo the actual user/access creation/deletion**

### Access Rejection (Correctly)
**File:** [access_management/models.py](access_management/models.py#L612)

```python
@transition(field='status', source='Pending', target='Rejected')
def reject_access(self, rejecter, reason):
    # Blocks activation - access stays Pending/Rejected
    # User never gets the access
```

**What it does:**
- ✅ Rejects access before it's activated
- ✅ User never gains access

---

## 🎯 ROOT CAUSE

### Architecture Problem

The system uses **two different patterns**:

| Feature | Pattern | Issue |
|---------|---------|-------|
| **User Create/Delete** | Signal-based (reactive) | Action → Approval |
| **Access Assignment** | Manual + Change Request | Approval → Activation |

**The Real Issue:**
- User operations use Django signals that fire **AFTER** the action happens
- Change requests are created as an **audit trail**, not a **control gate**
- No mechanism to prevent/rollback actions if rejected

---

## 📊 COMPARISON TABLE

| Aspect | User Create/Delete | Access Assignment |
|--------|-------------------|-------------------|
| When is it created? | Immediately (by user/admin) | In Pending state |
| When is change request created? | After (signal fires) | After (but access not active) |
| Is approval required before action? | ❌ No | ✅ Yes (before activation) |
| Can rejection prevent the action? | ❌ No | ✅ Yes |
| Audit trail captured? | ✅ Yes | ✅ Yes |
| Compliance with RHG 4.4? | ⚠️ Partial | ✅ Full |

---

## 🚨 COMPLIANCE IMPACT

**RHG 4.4 Requirement:**
> "All account creations/modifications/deletions must be requested and approved"

**Current Status:**
- ✅ Access assignments: Compliant (approval gates action)
- ❌ User creation/deletion: Non-compliant (no approval gate)

---

## 💡 RECOMMENDED SOLUTIONS

### Option 1: Soft Delete Pattern (Recommended)
User deletions create a **Deletion Request** (like Change Request) that must be approved before actual deletion:

```
Delete Request (Pending) 
    → System Owner approves
    → IT approves
    → Only THEN hard-delete happens
    → If rejected, cancellation record created
```

**Pros:**
- Reversible
- Full approval workflow
- Complete audit trail

**Cons:**
- Requires schema changes
- More complex logic

---

### Option 2: Pre-Approval Workflow (Current Change Management)
User creation/deletion requires change request FIRST:

```
1. Admin creates change request for user deletion
2. System Owner reviews
3. If approved, THEN deletion happens
4. If rejected, deletion is cancelled
```

**Pros:**
- Follows existing change management pattern
- Simple to implement
- Consistent with access workflow

**Cons:**
- Blocks immediate deletions (workflow overhead)

---

### Option 3: Hybrid Approach
- Keep user creation/deletion quick (current)
- Require approval for certain operations (e.g., termination)
- Use change request for audit trail
- Add "Rollback" action for rejections

**Pros:**
- Respects operational reality
- Audit trail maintained
- Some reversibility

**Cons:**
- Complex state management
- Unclear when rollback is acceptable

---

## 🔗 RELATED CODE FILES

### Change Management
- [change_management/views.py](change_management/views.py#L359) - Rejection logic
- [change_management/workflow.py](change_management/workflow.py#L125) - Rejection method
- [change_management/models.py](change_management/models.py#L5) - Status definitions

### Accounts/Users
- [accounts/views.py](accounts/views.py#L679) - User deletion with change request
- [change_management/signals.py](change_management/signals.py#L50) - User creation signal

### Access Management
- [access_management/views.py](access_management/views.py#L2730) - Approval logic
- [access_management/models.py](access_management/models.py#L584) - State transitions

---

## ✅ IMMEDIATE CHECK

Run this to see the issue:

```bash
python manage.py shell
```

```python
from change_management.models import AccountChangeRequest
from accounts.models import CustomUser

# Check some rejected user deletion requests
rejected_deletes = AccountChangeRequest.objects.filter(
    change_type='Delete',
    status='Rejected'
)[:5]

for req in rejected_deletes:
    # The user is already gone (user FK is null)
    user_still_exists = req.user is not None
    print(f"Request {req.id}: User snapshot='{req.user_full_name}', "
          f"Still exists={user_still_exists}, Status={req.status}")
```

**Expected Output:**
```
Request 1: User snapshot='John Smith', Still exists=False, Status=Rejected
Request 2: User snapshot='Jane Doe', Still exists=False, Status=Rejected
```

The users are gone even though the requests were rejected! ✗

---

## 📝 NEXT STEPS

To fix this issue properly:

1. **Decide on approach** (Soft Delete, Pre-Approval, or Hybrid)
2. **Design state machine** for user lifecycle
3. **Add reversal logic** where rejections can cancel actions
4. **Update signals** to respect approval gates
5. **Test rejection workflows** thoroughly
6. **Update audit trail** to show rollbacks

---

## 📌 SUMMARY

| Issue | Current Status | Impact |
|-------|---|---|
| User deletion rejection | ❌ Cannot prevent deletion | User permanently lost |
| User creation rejection | ❌ Cannot prevent creation | Unauthorized user active |
| Access rejection | ✅ Prevents activation | User never gets access |
| Audit trail | ✅ Recorded | Compliance satisfied |
| Approval gate | ⚠️ Partial | RHG 4.4 only partial compliance |

**Bottom Line:** Access management has proper approval gates, but user creation/deletion does not. The change requests are audit logs, not control mechanisms.

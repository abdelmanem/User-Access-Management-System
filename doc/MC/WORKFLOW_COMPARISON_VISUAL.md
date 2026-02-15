# Change Management Rejection Workflow - Visual Analysis

## 🔄 Workflow Comparison

### PROBLEM: User Deletion (Reactive - Wrong Pattern)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: ADMIN INITIATES DELETION                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Admin clicks "Delete User" → Confirmation form                      │
│  Admin enters: "Employee terminated"                                 │
│  Admin clicks: "Yes, Archive & Delete User"                          │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 2: ACTION EXECUTED IMMEDIATELY ✗ (NO GATE)                    │
├─────────────────────────────────────────────────────────────────────┤
│  UserArchive.objects.create(...)  ✓ Snapshot saved                  │
│  user.delete()                     ✓ User DELETED from DB           │
│                                                                      │
│  At this point:                                                      │
│  ✓ User is permanently gone                                          │
│  ✓ User's accesses removed (cascade delete)                          │
│  ✗ No approval yet!                                                  │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 3: CHANGE REQUEST CREATED (AFTER the fact)                    │
├─────────────────────────────────────────────────────────────────────┤
│  change_management/signals.py fires post_delete signal              │
│  AccountChangeRequest.objects.create(                               │
│    change_type='Delete',                                             │
│    status='Pending',  ← WAITING FOR APPROVAL                        │
│    user_full_name='John Smith',  ← Snapshot only!                   │
│    user=None,  ← User FK is null (already deleted)                  │
│  )                                                                   │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 4: SYSTEM OWNER REVIEWS (Days Later)                          │
├─────────────────────────────────────────────────────────────────────┤
│  Email: "Change Request #123 pending your approval"                 │
│  System Owner sees:                                                  │
│    - Type: Delete                                                    │
│    - User: John Smith (snapshot - user is already gone)             │
│    - Reason: Employee terminated                                     │
│                                                                      │
│  System Owner has options:                                           │
│  [✓ APPROVE] or [✗ REJECT]                                          │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 5: REJECTION (Too Late!)                                       │
├─────────────────────────────────────────────────────────────────────┤
│  System Owner clicks: REJECT                                        │
│  Reason: "User needed - was on leave, now returning"               │
│                                                                      │
│  What happens:                                                       │
│  ✓ Change request.status = 'Rejected'                               │
│  ✓ Rejection reason saved                                           │
│  ✓ Audit log created                                                │
│  ✗ User is STILL DELETED ← Cannot be reversed!                      │
│                                                                      │
│  Result:                                                             │
│  ✗ Approval was ineffective                                         │
│  ✗ Data is lost                                                     │
│  ✗ Compliance issue - needed rollback capability                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

### CORRECT: Access Assignment (Proactive - Right Pattern)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Step 1: MANAGER REQUESTS ACCESS                                    │
├─────────────────────────────────────────────────────────────────────┤
│ Manager/HR requests access for user to system:                      │
│   User: Sarah Peters                                                │
│   System: Accounting Software                                       │
│   Access Type: Read/Write                                           │
│   Reason: New hire, Finance Dept                                    │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 2: ACCESS CREATED IN PENDING STATE ✓ (GATED)                  │
├─────────────────────────────────────────────────────────────────────┤
│  UserSystemAccess.objects.create(                                   │
│    user=sarah,                                                      │
│    system=accounting,                                               │
│    status='Pending',  ← NOT YET ACTIVE!                             │
│    access_type='Read/Write'                                         │
│  )                                                                   │
│                                                                      │
│  At this point:                                                      │
│  ✓ Access record created                                            │
│  ✓ User CANNOT USE THE ACCESS (status = Pending)                    │
│  ✓ Awaiting approval                                                │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 3: CHANGE REQUEST CREATED (for audit/workflow)                │
├─────────────────────────────────────────────────────────────────────┤
│  _create_change_request_for_assignment()                            │
│  AccountChangeRequest.objects.create(                               │
│    change_type='Create',  ← Creating access                         │
│    status='Pending',                                                │
│    user=sarah,                                                      │
│    system=accounting                                                │
│  )                                                                   │
│                                                                      │
│  Note: Access is STILL in Pending state!                            │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Step 4: SYSTEM OWNER APPROVES/REJECTS                              │
├─────────────────────────────────────────────────────────────────────┤
│  Email: "New access request for Sarah Peters"                      │
│  System Owner reviews:                                              │
│    - User: Sarah Peters (verified)                                 │
│    - System: Accounting (looks good)                               │
│    - Access Type: Read/Write (appropriate for role)                │
│                                                                      │
│  Two options:                                                        │
│  [✓ APPROVE] or [✗ REJECT]                                          │
└──────────────────┬──────────────────────────────────────────────────┘
                   │
              ┌────┴─────┬──────────────────────────────┐
              │           │                              │
              ▼           ▼                              ▼
      ┌──────────────┐  ┌───────────────────┐  ┌──────────────────┐
      │ APPROVED     │  │ REJECTED          │  │ APPROVED (IT)    │
      └──────────────┘  └───────────────────┘  └──────────────────┘
              │           │                              │
              ▼           ▼                              ▼
      ┌──────────────────────────────────┐  ┌──────────────────────┐
      │ Access.status = 'Approved'       │  │ Access.status =      │
      │ ✓ User can now get access        │  │   'Rejected'         │
      │ (after IT approval too)          │  │ ✗ User never gets    │
      │                                  │  │   the access         │
      │ One more step:                   │  │                      │
      │ 1. activate_access()             │  │ Rejection effective! │
      │ 2. Access.status = 'Active'      │  └──────────────────────┘
      │ 3. User can now use system       │
      └──────────────────────────────────┘
```

---

## 📊 Side-by-Side Comparison

### When Rejection Happens

```
┌────────────────────────────────┬────────────────────────────────┐
│ USER DELETION REJECTION        │ ACCESS REJECTION               │
├────────────────────────────────┼────────────────────────────────┤
│ Timeline:                      │ Timeline:                      │
│ T=0:  User DELETED ✓ (done)   │ T=0:  Access created as        │
│ T=1:  Request PENDING          │       Pending (not usable)     │
│ T=7:  Rejection recorded ✗     │ T=1:  Request created as       │
│       (User already gone)      │       Pending (audit)          │
│                                │ T=7:  Rejection recorded ✓     │
│ Impact of Rejection:           │       (Access never used)      │
│ ✗ Cannot recover user          │                                │
│ ✗ Data lost                    │ Impact of Rejection:           │
│ ✗ Violates compliance          │ ✓ User blocked from access     │
│ ✗ Audit trail only             │ ✓ No unauthorized access       │
│                                │ ✓ Full compliance              │
│                                │ ✓ Rejection effective          │
└────────────────────────────────┴────────────────────────────────┘
```

---

## 🔀 State Machine Diagrams

### Current USER Deletion (BROKEN)
```
┌─────────────┐
│   Pending   │  ← Request created AFTER deletion
│ (audit log) │
└──────┬──────┘
       │
       ├──────────────────────┬─────────────────────┐
       │                      │                     │
       ▼                      ▼                     ▼
   ┌────────┐             ┌────────┐           ┌──────────┐
   │Approved│ (no effect) │Rejected│ (too late)│Completed │
   └────────┘             └────────┘           └──────────┘
                              │
                              ▼
   ✗ USER ALREADY GONE
     (Rejection ineffective)
```

### Correct ACCESS Assignment (RIGHT)
```
         ┌─────────┐
         │ Pending │  ← User created, NOT usable
         └────┬────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
   ┌────────┐    ┌────────┐
   │Approved│    │Rejected│  ← User blocked forever
   └───┬────┘    └────────┘
       │
       ▼
   ┌────────┐
   │ Active │  ← User can now use
   └────┬───┘
        │
        └──────────────────────┬─────────────────┐
                               │                 │
                               ▼                 ▼
                            ┌────────┐     ┌─────────┐
                            │Suspended│    │Revoked │
                            └────────┘     └─────────┘
```

---

## 💾 Database State Comparison

### Scenario: "Deletion Request Rejected"

#### USER DELETION (Current - BROKEN)
```sql
-- Before Deletion
SELECT * FROM accounts_customuser WHERE id = 5;
└─ Returns: John Smith, username='jsmith', is_active=true

-- After Admin Deletes (STEP 1)
SELECT * FROM accounts_customuser WHERE id = 5;
└─ Returns: NOTHING (user deleted)

-- After Rejection Recorded (STEP 2) 
SELECT * FROM change_management_accountchangerequest WHERE id = 123;
└─ Returns:
   id: 123
   user_id: NULL (user deleted!)
   user_full_name: 'John Smith'  (snapshot only)
   status: 'Rejected'
   
-- Trying to restore?
└─ ✗ IMPOSSIBLE - no data to restore, only snapshots
```

#### ACCESS REQUEST (Correct Pattern)
```sql
-- After Request Created (Pending)
SELECT * FROM access_management_usersystemaccess WHERE id = 789;
└─ Returns:
   id: 789
   user_id: 5
   system_id: 8
   status: 'Pending'
   approved_by: NULL
   
-- User CANNOT access system because status != 'Active'

-- After Rejection Recorded
SELECT * FROM access_management_usersystemaccess WHERE id = 789;
└─ Returns:
   status: 'Rejected'
   approved_by: NULL
   
-- ✓ User still exists in database, never got access
```

---

## 🎯 Key Architectural Issues

| Aspect | Issue | Impact |
|--------|-------|--------|
| **Timing** | Action happens BEFORE approval | Cannot be prevented/reversed |
| **Change Request Role** | Audit log, not control gate | Rejection is just documentation |
| **Data Integrity** | Hard delete with snapshot | Cannot recover deleted user |
| **Compliance** | Not RHG 4.4 compliant | Gaps in approval workflow |
| **User Experience** | Rejection seems to work but doesn't | Confusing feedback to admins |

---

## ✅ What Should Happen

### Correct User Deletion Flow

```
Step 1: Admin submits DELETION REQUEST
        └─ Status: Pending

Step 2: System Owner REVIEWS
        ├─ [APPROVE] → Move to next step
        └─ [REJECT] → Mark rejected, cancellation recorded, user stays

Step 3: If Approved, IT REVIEWS
        ├─ [APPROVE] → Ready to execute
        └─ [REJECT] → Cancellation recorded, user stays

Step 4: Only after ALL approvals
        └─> EXECUTE deletion (user removed from database)
        └─> Mark change request as "Completed"

Result:
✓ Approval is a gate, not a log
✓ Rejection prevents action
✓ Audit trail shows full workflow
✓ RHG 4.4 compliant
```

---

## 📝 Code Pattern Differences

### WRONG Pattern (Current User Deletion)
```python
# Step 1: DELETE USER
user.delete()  # ← User gone immediately

# Step 2: CREATE CHANGE REQUEST (SIGNAL)
@receiver(post_delete, sender=CustomUser)
def track_user_deletion(sender, instance, **kwargs):
    AccountChangeRequest.objects.create(
        status='Pending'  # ← Too late!
    )
```

### CORRECT Pattern (Access Assignment)
```python
# Step 1: CREATE ACCESS (STATUS=PENDING)
access = UserSystemAccess.objects.create(
    status='Pending'  # ← Gated
)

# Step 2: CREATE CHANGE REQUEST (for audit)
change_req = _create_change_request_for_assignment(access)

# Step 3: APPROVAL GATES ACTIVATION
@transition(source='Pending', target='Approved')
def approve_access(self, approver):
    pass  # Requires approval

# Step 4: ACTIVATION REQUIRES ADDITIONAL STEP
@transition(source='Approved', target='Active')
def activate_access(self):
    pass  # Still not usable
```

---

## 🚀 Recommended Fix

Implement a **Soft Delete + Rollback** pattern:

```python
# User Deletion Workflow (PROPOSED)

class DeletionRequest(models.Model):
    user = ForeignKey(CustomUser)
    requested_by = ForeignKey(User)
    status = CharField(choices=[
        'Pending',
        'Approved by Owner',
        'Approved by IT',
        'Executing',
        'Completed',
        'Rejected',
        'Rolled Back'  ← Recovery option
    ])

# When rejection comes: AUTOMATICALLY RESTORE
if status == 'Rejected':
    # User was soft-deleted, restore it
    user.is_deleted = False
    user.save()
    
    # Create rollback record
    DeletionRequest.status = 'Rolled Back'
    DeletionRequest.rolled_back_by = admin_user
    DeletionRequest.save()
```

This makes rejections actually functional!

---

**Summary:** The system treats user deletions as immediately-executed with approval-after-the-fact (wrong), while access assignments implement proper pre-action approval gates (correct). User deletion workflow needs to be redesigned to match the access assignment pattern.

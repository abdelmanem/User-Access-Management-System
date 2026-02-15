# Rejection Tracking - Quick Reference Guide

**Last Updated:** 2026-02-12  
**Status:** ✅ Production Ready

---

## 🚀 Quick Start

### Reject a Change Request (in code)

```python
from change_management.workflow import ChangeRequestWorkflow
from change_management.models import AccountChangeRequest

change_req = AccountChangeRequest.objects.get(id=123)

# Option 1: System Owner rejects
ChangeRequestWorkflow.reject_change_by_owner(
    change_req,
    rejected_by=current_user,
    rejection_reason="User lacks required training"
)

# Option 2: IT rejects
ChangeRequestWorkflow.reject_change_by_it(
    change_req,
    rejected_by=current_user,
    rejection_reason="Security policy violation"
)
```

### Check Rejection Status

```python
if change_req.is_rejected():
    print(f"Rejected by: {change_req.system_owner_rejected_by}")
    print(f"Date: {change_req.system_owner_rejection_date}")
    print(f"Reason: {change_req.system_owner_rejection_reason}")
```

---

## 📋 Available Fields

```python
change_request.system_owner_rejected          # True/False
change_request.system_owner_rejection_date    # 2026-02-12 14:35:22
change_request.system_owner_rejection_reason  # "User lacks training"
change_request.system_owner_rejected_by       # <User object>

change_request.it_rejected                    # True/False
change_request.it_rejection_date              # 2026-02-12 14:35:22
change_request.it_rejection_reason            # "Security violation"
change_request.it_rejected_by                 # <User object>

change_request.updated_at                     # 2026-02-12 14:35:22
```

---

## 🔍 Query Examples

### Find All Rejections
```python
rejected = AccountChangeRequest.objects.filter(status='Rejected')
```

### Find Owner Rejections Only
```python
owner_rejected = AccountChangeRequest.objects.filter(system_owner_rejected=True)
```

### Find IT Rejections Only
```python
it_rejected = AccountChangeRequest.objects.filter(it_rejected=True)
```

### Find Rejections by User
```python
user_rejections = AccountChangeRequest.objects.filter(
    system_owner_rejected_by=user_id
)
```

### Find Rejections in Date Range
```python
from datetime import datetime, timedelta

start = datetime.now() - timedelta(days=7)
recent = AccountChangeRequest.objects.filter(
    system_owner_rejection_date__gte=start
)
```

### Get Rejection Reasons
```python
reasons = AccountChangeRequest.objects.filter(
    system_owner_rejected=True
).values('system_owner_rejection_reason').distinct()

for reason in reasons:
    print(reason['system_owner_rejection_reason'])
```

### Count Rejections by User
```python
from django.db.models import Count

stats = AccountChangeRequest.objects.filter(
    system_owner_rejected=True
).values('system_owner_rejected_by__username').annotate(
    total=Count('id')
).order_by('-total')

for stat in stats:
    print(f"{stat['system_owner_rejected_by__username']}: {stat['total']}")
```

---

## 📊 Audit Trail

### Get Rejection Log
```python
from change_management.audit import get_change_audit_trail

logs = get_change_audit_trail(change_request_id=123)

for log in logs:
    if log.action == 'rejected':
        print(f"Rejected at: {log.timestamp}")
        print(f"By: {log.performed_by}")
        print(f"Reason: {log.notes}")
```

### View All Actions
```python
for log in logs:
    print(f"{log.timestamp} - {log.action} by {log.performed_by}")
    if log.old_values:
        print(f"  Before: {log.old_values}")
    if log.new_values:
        print(f"  After: {log.new_values}")
```

---

## 🛠️ Common Patterns

### Pattern 1: Reject with Validation
```python
def reject_request_safely(request_id, user, reason):
    req = AccountChangeRequest.objects.get(id=request_id)
    
    # Validations
    if req.status != 'Pending':
        raise ValueError("Can only reject pending requests")
    
    if not reason or len(reason) < 10:
        raise ValueError("Please provide detailed reason")
    
    # Reject
    ChangeRequestWorkflow.reject_change_by_owner(req, user, reason)
    return True
```

### Pattern 2: Bulk Reject
```python
def bulk_reject_requests(request_ids, user, reason):
    results = {'success': 0, 'failed': 0}
    
    for req_id in request_ids:
        try:
            req = AccountChangeRequest.objects.get(id=req_id)
            ChangeRequestWorkflow.reject_change_by_owner(req, user, reason)
            results['success'] += 1
        except Exception as e:
            results['failed'] += 1
            print(f"Failed to reject {req_id}: {e}")
    
    return results
```

### Pattern 3: Auto-Reject with Reason
```python
def auto_reject_expired(days=30):
    from datetime import datetime, timedelta
    
    cutoff = datetime.now() - timedelta(days=days)
    old_requests = AccountChangeRequest.objects.filter(
        status='Pending',
        created_at__lt=cutoff
    )
    
    system_user = CustomUser.objects.get(username='system')
    
    for req in old_requests:
        ChangeRequestWorkflow.reject_change_by_it(
            req,
            rejected_by=system_user,
            rejection_reason=f"Auto-rejected: Pending for more than {days} days"
        )
```

---

## 📈 Reporting

### Rejection Summary Report
```python
from django.db.models import Count
from datetime import datetime, timedelta

def rejection_summary(days=30):
    cutoff = datetime.now() - timedelta(days=days)
    
    total = AccountChangeRequest.objects.filter(
        status='Rejected',
        updated_at__gte=cutoff
    ).count()
    
    owner_rejections = AccountChangeRequest.objects.filter(
        system_owner_rejected=True,
        system_owner_rejection_date__gte=cutoff
    ).count()
    
    it_rejections = AccountChangeRequest.objects.filter(
        it_rejected=True,
        it_rejection_date__gte=cutoff
    ).count()
    
    top_reasons = AccountChangeRequest.objects.filter(
        status='Rejected',
        updated_at__gte=cutoff
    ).values('system_owner_rejection_reason').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return {
        'total': total,
        'owner_rejections': owner_rejections,
        'it_rejections': it_rejections,
        'top_reasons': list(top_reasons)
    }

report = rejection_summary(days=7)
print(f"Total rejections (7 days): {report['total']}")
print(f"Owner rejections: {report['owner_rejections']}")
print(f"IT rejections: {report['it_rejections']}")
```

### User Rejection Activity
```python
def user_rejection_stats(user_id):
    stats = {
        'owner_rejections': 0,
        'it_rejections': 0,
        'total': 0,
        'recent': []
    }
    
    owner_rejects = AccountChangeRequest.objects.filter(
        system_owner_rejected_by_id=user_id
    ).count()
    
    it_rejects = AccountChangeRequest.objects.filter(
        it_rejected_by_id=user_id
    ).count()
    
    recent = AccountChangeRequest.objects.filter(
        system_owner_rejected_by_id=user_id
    ).order_by('-system_owner_rejection_date')[:10]
    
    stats['owner_rejections'] = owner_rejects
    stats['it_rejections'] = it_rejects
    stats['total'] = owner_rejects + it_rejects
    stats['recent'] = list(recent.values('id', 'created_at', 'system_owner_rejection_date'))
    
    return stats
```

---

## 🧪 Testing

### Test Rejection
```python
from django.test import TestCase
from change_management.models import AccountChangeRequest
from change_management.workflow import ChangeRequestWorkflow

class RejectionTrackingTest(TestCase):
    def test_rejection_tracking(self):
        # Create change request
        cr = AccountChangeRequest.objects.create(
            action='DELETE',
            status='Pending'
        )
        
        # Reject it
        from django.contrib.auth import get_user_model
        User = get_user_model()
        rejector = User.objects.first()
        
        ChangeRequestWorkflow.reject_change_by_owner(
            cr,
            rejector,
            "Test rejection"
        )
        
        # Verify
        cr.refresh_from_db()
        self.assertTrue(cr.system_owner_rejected)
        self.assertIsNotNone(cr.system_owner_rejection_date)
        self.assertEqual(cr.system_owner_rejected_by, rejector)
        self.assertEqual(cr.system_owner_rejection_reason, "Test rejection")
        self.assertEqual(cr.status, 'Rejected')
```

---

## ⚠️ Important Notes

1. **Always use workflow methods**
   ```python
   # ✅ CORRECT
   ChangeRequestWorkflow.reject_change_by_owner(...)
   
   # ❌ WRONG - doesn't create audit log
   change_request.system_owner_rejected = True
   change_request.save()
   ```

2. **Rejection reason is required**
   ```python
   # ✅ CORRECT
   reject_change_by_owner(..., "Lacks training certification")
   
   # ❌ WRONG - empty reason
   reject_change_by_owner(..., "")
   ```

3. **Status is updated automatically**
   ```python
   # After rejection, status is automatically 'Rejected'
   # No need to set manually
   ```

4. **Timestamps are automatic**
   ```python
   # Never set timestamps manually
   # They're set by the workflow method
   ```

---

## 🐛 Troubleshooting

### Problem: No timestamp recorded
**Solution:** Use workflow method instead of direct field assignment
```python
# ✅ Correct
ChangeRequestWorkflow.reject_change_by_owner(...)

# ❌ Wrong
change_request.system_owner_rejected = True
change_request.save()  # No timestamp!
```

### Problem: Audit log not created
**Solution:** Ensure method completes without exceptions
```python
try:
    ChangeRequestWorkflow.reject_change_by_owner(...)
except Exception as e:
    print(f"Error: {e}")  # Check what went wrong
```

### Problem: Can't query by rejection date
**Solution:** Make sure field is not NULL
```python
# This won't find anything if date is NULL
rejected = AccountChangeRequest.objects.filter(
    system_owner_rejection_date__isnull=False
)
```

### Problem: User field is NULL
**Solution:** Ensure rejected_by parameter is passed
```python
# ✅ Correct - must pass user
reject_change_by_owner(cr, user, "Reason")

# ❌ Wrong - no user
reject_change_by_owner(cr, None, "Reason")
```

---

## 📚 Related Documentation

- [REJECTION_TRACKING_IMPLEMENTATION.md](REJECTION_TRACKING_IMPLEMENTATION.md) - Full implementation guide
- [CHANGE_MANAGEMENT_REJECTION_SOLUTION.md](CHANGE_MANAGEMENT_REJECTION_SOLUTION.md) - Problem & solution analysis
- [test_rejection_tracking.py](test_rejection_tracking.py) - Test examples
- [change_management/models.py](change_management/models.py) - Model source
- [change_management/workflow.py](change_management/workflow.py) - Workflow source

---

## 🔗 Key Methods

| Method | Purpose | Returns |
|--------|---------|---------|
| `reject_change_by_owner()` | Record System Owner rejection | None |
| `reject_change_by_it()` | Record IT rejection | None |
| `is_rejected()` | Check if rejected | Boolean |
| `is_approved()` | Check if fully approved | Boolean |
| `get_change_audit_trail()` | Get audit logs | QuerySet |
| `log_change_action()` | Create audit log entry | ChangeAuditLog |

---

## 🎯 Typical Workflow

1. **User submits change request**
   ```
   Status: Pending
   ```

2. **System Owner reviews**
   ```
   Decides to REJECT
   ```

3. **Call rejection method**
   ```python
   ChangeRequestWorkflow.reject_change_by_owner(
       change_request,
       system_owner_user,
       "User lacks training certification"
   )
   ```

4. **Fields updated automatically**
   ```
   system_owner_rejected = True
   system_owner_rejection_date = 2026-02-12 14:35:22
   system_owner_rejected_by = system_owner_user
   system_owner_rejection_reason = "User lacks training certification"
   status = "Rejected"
   updated_at = 2026-02-12 14:35:22
   ```

5. **Audit log created**
   ```
   action = "rejected"
   timestamp = 2026-02-12 14:35:22
   performed_by = system_owner_user
   notes = "System Owner Rejection: User lacks training certification"
   ```

6. **Requester can see rejection**
   ```
   Can view reason on request details
   Can resubmit with changes
   ```

---

**Keep this guide handy for quick reference!**

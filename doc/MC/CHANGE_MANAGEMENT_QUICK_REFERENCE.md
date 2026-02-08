# Change Management - Quick Reference Card

## 🚀 Get Started in 60 Seconds

### 1. Run Migrations
```bash
python manage.py makemigrations change_management
python manage.py migrate change_management
```

### 2. Test It Works
```bash
python manage.py shell
```
```python
from accounts.models import CustomUser
from change_management.models import AccountChangeRequest

# Create a user - change request auto-created!
user = CustomUser.objects.create(username='testuser', email='test@test.com')

# Verify change request exists
change = AccountChangeRequest.objects.filter(user=user).first()
print(f"✓ Change request created: {change}")
```

### 3. Access Admin
- Go to: http://localhost:8000/admin/
- Login with superuser
- Go to: **Change Management** → **Account Change Requests**
- Try: **Approve Selected** button

### 4. Test API
```bash
curl http://localhost:8000/api/change-requests/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📋 Common Tasks

### List Pending Changes
**Admin UI**: Change Management → Filter by "Pending"
**API**: `GET /api/change-requests/?status=Pending`
**CLI**: `python manage.py process_changes --list-pending`

### Approve a Change
**Admin UI**: Select change → Click "Approve Selected"
**API**: `POST /api/change-requests/1/approve/`
**Code**: 
```python
ChangeRequestWorkflow.approve_change(change, admin_user)
```

### View Audit Trail
**Admin UI**: Open change → Scroll to "Audit Trail" section
**API**: `GET /api/change-requests/1/`
**Query**: `AccountChangeRequest.objects.get(id=1).audit_logs.all()`

### Get Statistics
**Admin UI**: N/A (shown in admin list)
**API**: `GET /api/change-requests/statistics/`
**Code**: See ViewSet statistics method

### Bulk Approve
**Admin UI**: Select multiple → "Approve Selected"
**API**: `POST /api/change-requests/bulk-action/`

## 🔑 Key Models & Methods

### AccountChangeRequest
```python
# Fields
.change_type              # Create, Modify, Delete, Suspend
.user                     # User affected
.system                   # System where change occurs
.status                   # Pending, Approved, Rejected, Completed
.business_justification   # Why this change
.system_owner             # Who approves
.requested_by             # Who requested
```

### Workflow Helpers
```python
# Create
ChangeRequestWorkflow.create_account_change()

# Approve/Reject/Complete
ChangeRequestWorkflow.approve_change()
ChangeRequestWorkflow.reject_change()
ChangeRequestWorkflow.complete_change()

# Query
ChangeRequestWorkflow.get_pending_approvals()
ChangeRequestWorkflow.get_pending_completion()
ChangeRequestWorkflow.get_overdue_approvals(days=7)
ChangeRequestWorkflow.get_changes_by_system(system_id)
ChangeRequestWorkflow.get_changes_by_user(user_id)
```

### Audit Logging
```python
# Manual logging
log_change_action(change, action, user, notes="...")

# Query audit
get_change_audit_trail(change_request_id)
get_user_change_history(user_id)
export_audit_logs(start_date, end_date)
```

## 📊 API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/change-requests/` | List all changes |
| GET | `/api/change-requests/{id}/` | Get change details |
| POST | `/api/change-requests/` | Create change |
| PATCH | `/api/change-requests/{id}/` | Update change |
| DELETE | `/api/change-requests/{id}/` | Delete change |
| POST | `/api/change-requests/{id}/approve/` | Approve |
| POST | `/api/change-requests/{id}/reject/` | Reject |
| POST | `/api/change-requests/{id}/mark-completed/` | Complete |
| GET | `/api/change-requests/statistics/` | Get stats |
| POST | `/api/change-requests/bulk-action/` | Bulk ops |
| GET | `/api/change-requests/pending-approvals/` | Pending |

## 🎯 Management Commands

```bash
# List pending
python manage.py process_changes --list-pending

# Show stats
python manage.py process_changes

# Approve all (with confirmation)
python manage.py process_changes --approve-all

# Dry run first
python manage.py process_changes --approve-all --dry-run

# Complete old (>7 days)
python manage.py process_changes --complete-old 7

# Filter by system
python manage.py process_changes --list-pending --system AD
```

## 🔍 Query Examples

```python
from change_management.models import AccountChangeRequest

# Pending changes
pending = AccountChangeRequest.objects.filter(
    status=AccountChangeRequest.STATUS_PENDING
)

# By user
user_changes = AccountChangeRequest.objects.filter(user_id=1)

# By system
ad_changes = AccountChangeRequest.objects.filter(system__code='AD')

# Created today
from django.utils import timezone
from datetime import timedelta
today = timezone.now().date()
today_changes = AccountChangeRequest.objects.filter(
    created_at__date=today
)

# Slow approvals (>24 hours)
slow = AccountChangeRequest.objects.filter(
    status=AccountChangeRequest.STATUS_APPROVED
).exclude(system_owner_approval_date__isnull=True).filter(
    system_owner_approval_date__gt=timezone.now() - timedelta(hours=24)
)
```

## 📈 Monitoring Dashboard

View in Django admin:
1. Go to: **Change Management**
2. **Account Change Requests** - see list with stats
3. **Change Audit Logs** - see all actions

View via API:
```bash
curl http://localhost:8000/api/change-requests/statistics/
```

Returns:
```json
{
  "total_requests": 150,
  "pending_requests": 12,
  "approved_requests": 98,
  "completed_requests": 35,
  "rejected_requests": 5,
  "average_approval_time_hours": 4.5,
  "by_system": {...},
  "by_change_type": {...},
  "by_status": {...}
}
```

## ⚠️ Troubleshooting

### Changes not auto-creating?
```python
# Check signals are registered
from django.apps import apps
app = apps.get_app_config('change_management')
print(app.ready())  # Should be called
```

### Admin actions not showing?
- Ensure user is staff/superuser
- Check INSTALLED_APPS includes 'change_management'
- Restart Django server

### API returns 403?
- Add `Authorization: Bearer TOKEN` header
- Or login in browser first
- Check user has permissions

### Audit logs not appearing?
```python
# Verify migration applied
python manage.py showmigrations change_management
# Should show all green checkmarks
```

## 📞 Quick Links

- **Main Guide**: [CHANGE_MANAGEMENT_INTEGRATION.md](CHANGE_MANAGEMENT_INTEGRATION.md)
- **Checklist**: [CHANGE_MANAGEMENT_IMPLEMENTATION_CHECKLIST.md](CHANGE_MANAGEMENT_IMPLEMENTATION_CHECKLIST.md)
- **Summary**: [CHANGE_MANAGEMENT_SUMMARY.md](CHANGE_MANAGEMENT_SUMMARY.md)

## 🎯 Next Steps

1. ✅ Run migrations
2. ✅ Test in Django shell
3. ✅ Try admin interface
4. ✅ Test API endpoints
5. ✅ Run management commands
6. ✅ Review audit logs
7. ✅ Deploy to production
8. ✅ Set up monitoring

## 💡 Pro Tips

- Use `--dry-run` with management commands first
- Check audit logs for troubleshooting
- Export statistics monthly
- Monitor average approval time
- Set up email notifications (enhancement)
- Use API for automation

---

**Status**: Production Ready ✅
**Files**: 9 new/modified files
**Components**: 6 major features
**Documentation**: Complete
**Testing**: Ready for production

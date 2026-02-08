# Change Management Integration Guide

## Overview
The Change Management system is now fully integrated with other applications in your User Access Management System. It automatically tracks account changes across the entire system with full audit trail support.

## Architecture

### Components

#### 1. **Automatic Signal Handlers** (`signals.py`)
Automatically creates change requests when:
- New users are created in the system
- User employment status changes (especially termination)
- Service accounts are created, modified, or deleted
- Hardware assets change status
- User system access is approved or revoked

**File**: [change_management/signals.py](change_management/signals.py)

#### 2. **REST API** (`views.py`, `serializers.py`, `urls.py`)
Full REST API for programmatic access:

**Endpoints**:
- `GET /api/change-requests/` - List change requests
- `GET /api/change-requests/{id}/` - Get details
- `POST /api/change-requests/{id}/approve/` - Approve change
- `POST /api/change-requests/{id}/reject/` - Reject change
- `POST /api/change-requests/{id}/mark-completed/` - Mark completed
- `GET /api/change-requests/statistics/` - Get statistics
- `POST /api/change-requests/bulk-action/` - Bulk operations
- `GET /api/change-requests/pending-approvals/` - Pending approvals

**Files**:
- [change_management/serializers.py](change_management/serializers.py)
- [change_management/views.py](change_management/views.py)
- [change_management/urls.py](change_management/urls.py)

#### 3. **Admin Interface** (`admin.py`, `admin_actions.py`)
Enhanced Django admin with:
- Quick approval/rejection/completion actions
- Audit trail visualization
- Advanced filtering and search
- Bulk operations

**Files**:
- [change_management/admin.py](change_management/admin.py)
- [change_management/admin_actions.py](change_management/admin_actions.py)

#### 4. **Audit Logging** (`audit.py`, `models.py`)
Complete audit trail with:
- User action tracking
- Old/new value comparison
- IP address logging
- Compliance reporting

**File**: [change_management/audit.py](change_management/audit.py)

#### 5. **Workflow Utilities** (`workflow.py`)
Helper classes for:
- Creating changes programmatically
- Approving/rejecting/completing changes
- Querying pending items
- Notifications
- External system integration

**File**: [change_management/workflow.py](change_management/workflow.py)

#### 6. **Management Commands** (`management/commands/process_changes.py`)
Command-line tools for:
- Listing pending changes
- Batch approvals
- Auto-completion of old changes
- Statistics reporting

**File**: [change_management/management/commands/process_changes.py](change_management/management/commands/process_changes.py)

## Usage Examples

### From Django Shell

```python
from change_management.workflow import ChangeRequestWorkflow, ChangeNotificationManager
from systems.models import System
from accounts.models import CustomUser

# Create a change request
user = CustomUser.objects.get(username='john.doe')
system = System.objects.get(code='AD')
approver = CustomUser.objects.get(username='admin')

change = ChangeRequestWorkflow.create_account_change(
    change_type='Create',
    system=system,
    business_justification='New employee onboarding',
    user=user,
    requested_by=approver,
    system_owner=approver
)

# Approve the change
ChangeRequestWorkflow.approve_change(
    change,
    approved_by=approver,
    approval_notes="Approved for onboarding"
)

# Get pending approvals
pending = ChangeRequestWorkflow.get_pending_approvals()
for change in pending:
    print(f"Pending: {change.change_type} for {change.user}")

# Complete the change
ChangeRequestWorkflow.complete_change(
    change,
    completed_by=approver,
    completion_notes="Implemented in AD"
)
```

### REST API Usage

```bash
# List pending change requests
curl http://localhost:8000/api/change-requests/?status=Pending

# Get statistics
curl http://localhost:8000/api/change-requests/statistics/

# Approve a change
curl -X POST http://localhost:8000/api/change-requests/1/approve/ \
  -H "Content-Type: application/json" \
  -d '{"approval_notes": "Approved"}'

# Bulk approve changes
curl -X POST http://localhost:8000/api/change-requests/bulk-action/ \
  -H "Content-Type: application/json" \
  -d '{
    "ids": [1, 2, 3],
    "action": "approve",
    "notes": "Batch approved"
  }'
```

### Management Commands

```bash
# List pending changes
python manage.py process_changes --list-pending

# Approve all pending (with confirmation)
python manage.py process_changes --approve-all

# Dry-run to see what would happen
python manage.py process_changes --approve-all --dry-run

# Complete changes older than 7 days
python manage.py process_changes --complete-old 7

# Filter by system
python manage.py process_changes --list-pending --system AD
```

### Direct Database Queries

```python
from change_management.models import AccountChangeRequest

# Get all pending changes
pending = AccountChangeRequest.objects.filter(
    status=AccountChangeRequest.STATUS_PENDING
)

# Get changes for a specific user
user_changes = AccountChangeRequest.objects.filter(user_id=1)

# Get changes by system
ad_changes = AccountChangeRequest.objects.filter(system__code='AD')

# Get overdue approvals (> 7 days old)
from change_management.workflow import ChangeRequestWorkflow
overdue = ChangeRequestWorkflow.get_overdue_approvals(days=7)
```

## Integration Points

### 1. **User Management** (`accounts` app)
When a user is created or terminated:
- Automatically creates "Create" or "Delete" change requests
- Links to appropriate system (AD/LDAP)
- Tracks business justification

### 2. **Service Accounts** (`service_accounts` app)
When a service account changes:
- Creates change requests for creation/modification/deletion
- Tracks account-specific details
- Links to owner for approval

### 3. **Hardware Management** (`hardware` app)
When hardware status changes:
- Logs status transitions (Retired, Disposed, etc.)
- Tracks equipment lifecycle

### 4. **Access Management** (`access_management` app)
When user system access is approved:
- Creates "Create" change requests
- When access is revoked: creates "Delete" change requests
- Links change request to access record

### 5. **Systems Registry** (`systems` app)
- Uses System model for change routing
- Identifies System Owners for approval
- Tracks system-specific change requirements

## Database Schema

New models:
- `AccountChangeRequest` - Core change tracking
- `ChangeAuditLog` - Complete audit trail

Indexes created for performance:
- `(status, -created_at)`
- `(system, -created_at)`
- `(user, -created_at)`
- `(change_request, -timestamp)` on audit logs

## Admin Features

### Quick Actions
- **Approve Selected** - Approve multiple changes at once
- **Reject Selected** - Reject multiple changes
- **Mark Completed** - Mark changes as implemented

### Filtering
- By status (Pending, Approved, Rejected, Completed)
- By change type (Create, Modify, Delete, Suspend)
- By system
- By date created
- By approval status

### Search
- User name, email, username
- System name/code
- Business justification text

### Audit Trail
- View all actions taken on a change request
- See who did what and when
- Collapsible section with recent history

## Migration Steps

After deployment:

1. **Create migrations for new models**:
   ```bash
   python manage.py makemigrations change_management
   python manage.py migrate change_management
   ```

2. **Test signals in development**:
   ```bash
   # Create a test user and verify change request is created
   python manage.py shell
   # Then run the examples from "Usage Examples" section
   ```

3. **Run initial statistics**:
   ```bash
   python manage.py process_changes
   ```

4. **Monitor audit logs**:
   - Visit Django admin
   - Check "Change Audit Logs" section
   - Verify logging is working

## Compliance & Audit

### Traceability
- Every action logged with timestamp and user
- Old and new values captured
- IP address and user-agent tracked
- Full change lifecycle documented

### Reporting
- Export audit logs for compliance audits
- Statistics dashboard via REST API
- Change history by user or system
- Approval times and patterns

### Best Practices
1. Regularly review pending changes
2. Monitor overdue approvals
3. Archive completed changes periodically
4. Export audit logs monthly for retention
5. Set up email notifications (optional enhancement)

## Configuration

### Settings
Add to `settings.py` if needed:

```python
# Change Management Configuration
CHANGE_MANAGEMENT = {
    'AUTO_CREATE_ON_USER_CREATION': True,  # Default: True
    'AUTO_CREATE_ON_SERVICE_ACCOUNT': True,  # Default: True
    'AUTO_CREATE_ON_ACCESS_APPROVAL': True,  # Default: True
    'DEFAULT_SYSTEM_CODE': 'AD',  # Default system for changes
    'AUDIT_LOG_RETENTION_DAYS': 365,  # Days to keep audit logs
}

# Logging
LOGGING = {
    'handlers': {
        'change_management': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/change_management.log',
        },
    },
    'loggers': {
        'change_management': {
            'handlers': ['change_management'],
            'level': 'INFO',
        },
    },
}
```

## Troubleshooting

### Changes not being created automatically
1. Check that signals are registered in `apps.py` ready() method
2. Verify `change_management` is in INSTALLED_APPS
3. Check logs for errors: `tail -f logs/change_management.log`

### Audit logs not appearing
1. Ensure ChangeAuditLog migration is applied
2. Check user has change_add permission
3. Verify log_change_action is being called

### API returning 403 Forbidden
1. Ensure user is authenticated (use token or session)
2. Check user permissions
3. Use `DjangoModelPermissions` or custom permissions as needed

## Future Enhancements

Potential additions:
1. Email notifications on approval/rejection
2. Slack/Teams integration
3. External ITSM system sync (ServiceNow, Jira)
4. Change scheduling and rollback procedures
5. Multi-level approvals (Manager → System Owner → IT Admin)
6. Change impact analysis
7. Automated compliance reports
8. Change rollback capabilities

## Support & Questions

For issues or questions:
1. Check logs in `logs/change_management.log`
2. Review audit trails in Django admin
3. Check database constraints and indexes
4. Verify all migrations are applied: `python manage.py showmigrations`

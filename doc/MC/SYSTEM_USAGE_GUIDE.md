# Change Management System - Access & Usage Guide

## 🚀 Quick Start

The system is running on `http://localhost:8000/`

### Three Ways to Access Change Management

#### 1️⃣ Web Admin Interface
**URL:** http://localhost:8000/admin/  
**Path:** Change Management > Change Requests  
**Features:**
- View all change requests
- Approve/Reject with bulk actions
- Full audit trail visible
- Advanced filtering and search

#### 2️⃣ REST API
**Base URL:** http://localhost:8000/api/change-requests/  
**Authentication:** Required (Session or Token)

**Common Endpoints:**
```
GET    /api/change-requests/              # List all (with filters)
GET    /api/change-requests/statistics/   # Get stats
GET    /api/change-requests/pending-approvals/  # Pending items
POST   /api/change-requests/{id}/approve/ # Approve request
POST   /api/change-requests/{id}/reject/  # Reject request
```

**Example with curl:**
```bash
# Get authentication token (one-time)
curl -X POST http://localhost:8000/api-token-auth/ \
  -d "username=admin&password=your_password"

# Use token for API requests
curl -H "Authorization: Token YOUR_TOKEN" \
  http://localhost:8000/api/change-requests/
```

#### 3️⃣ Command Line Interface (CLI)
**Command:** `python manage.py process_changes`

**Operations:**
```bash
# List pending requests
python manage.py process_changes --list-pending

# View statistics
python manage.py process_changes --statistics

# Auto-approve all pending
python manage.py process_changes --approve-all

# Preview changes (dry-run)
python manage.py process_changes --approve-all --dry-run
```

---

## 📋 System Architecture

### Automatic Integration

Whenever these actions occur in other systems, a change request is automatically created:

| Trigger | System | Change Type | Auto Status |
|---------|--------|-------------|------------|
| User Created | Accounts | ACCOUNT_CREATION | Pending |
| User Deactivated | Accounts | ACCOUNT_TERMINATION | Pending |
| Service Account Added | Service Accounts | SERVICE_ACCOUNT_CREATION | Pending |
| Hardware Assigned | Hardware | HARDWARE_ASSIGNMENT | Pending |
| Access Approved | Access Management | ACCESS_GRANT | Pending |
| Access Revoked | Access Management | ACCESS_REVOCATION | Pending |

### Approval Workflow

```
Change Created → Pending System Owner Approval → 
Pending IT Approval → Completed → Audit Logged
```

### Audit Trail

Every change request has a complete immutable audit log recording:
- Who made the change
- When it was made
- What changed
- IP address and user agent
- Notes and approval comments

---

## 🔍 Example: Approving a Change Request

### Via Web Admin
1. Navigate to http://localhost:8000/admin/change_management/changemanager/
2. Select change requests to approve
3. Click "Approve selected change requests"
4. Save

### Via REST API
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api-token-auth/ \
  -d "username=admin&password=PASSWORD" | jq -r '.token')

# Approve specific request
curl -X POST http://localhost:8000/api/change-requests/1/approve/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"approval_notes":"Approved for production"}'
```

### Via CLI
```bash
# List pending
python manage.py process_changes --list-pending

# Auto-approve all (with dry-run first)
python manage.py process_changes --approve-all --dry-run
python manage.py process_changes --approve-all
```

---

## 📊 Monitoring & Reporting

### View Statistics
```bash
# CLI
python manage.py process_changes --statistics

# REST API
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/change-requests/statistics/
```

### Filter Change Requests

**API Query Parameters:**
```
?status=PENDING_APPROVAL
?change_type=ACCOUNT_CREATION
?system=HR
?created_after=2026-02-01
?search=username
```

**Example:**
```bash
curl "http://localhost:8000/api/change-requests/?status=PENDING_APPROVAL&system=HR"
```

### Generate Reports
Currently available in admin interface:
- Change requests by status
- Change requests by type
- Change requests by system
- Approval time metrics

---

## 🔐 Authentication

### For REST API

**Method 1: Session Authentication**
- Login via admin interface
- Use session cookies in API requests

**Method 2: Token Authentication**
```bash
# Generate token
python manage.py drf_create_token username

# Use in requests
Authorization: Token YOUR_TOKEN
```

### For Admin Interface
- Standard Django admin username/password
- 2FA supported if configured

---

## ⚙️ Configuration

### Customize Approval Settings

**File:** `change_management/workflow.py`

```python
# Update approval requirements
SYSTEM_OWNER_REQUIRED = True
IT_APPROVAL_REQUIRED = True
AUTO_COMPLETE_DAYS = 30
```

### Customize Notifications

**File:** `change_management/workflow.py`

```python
# Update notification settings
NOTIFY_ON_APPROVAL = True
NOTIFY_ON_REJECTION = True
NOTIFICATION_EMAIL = 'approver@example.com'
```

### Change Request Types

**File:** `change_management/models.py`

```python
CHANGE_TYPE_CHOICES = [
    ('ACCOUNT_CREATION', 'Account Creation'),
    ('ACCOUNT_TERMINATION', 'Account Termination'),
    ('SERVICE_ACCOUNT_CREATION', 'Service Account Creation'),
    # Add custom types here
]
```

---

## 🐛 Troubleshooting

### API Returning 401 Unauthorized
- Solution: Include authentication header or login first
- Check token hasn't expired
- Verify user has API permissions

### Change Requests Not Auto-Creating
- Check server is running: `python manage.py check`
- Verify signals registered: Look for "signals registered" in logs
- Restart server if signals added recently

### Audit Trail Missing
- Ensure users are authenticated when making changes
- Check `ChangeAuditLog` table has data
- Verify user in request context

### Slow API Responses
- Check pagination (default 50 items per page)
- Use filters to narrow results
- Review database indexes

---

## 📚 Additional Resources

- **Admin Interface:** http://localhost:8000/admin/
- **API Documentation:** (Browsable API at each endpoint in browser)
- **Django Docs:** https://docs.djangoproject.com/
- **Django REST Framework:** https://www.django-rest-framework.org/

---

## 🎯 Common Tasks

### Task: Create Change Request Programmatically
```python
from change_management.workflow import ChangeRequestWorkflow
from accounts.models import CustomUser

workflow = ChangeRequestWorkflow()
user = CustomUser.objects.get(username='john')
request = workflow.create_account_change(
    user=user,
    change_type='ACCOUNT_CREATION',
    system='HR System',
    business_justification='New employee onboarding'
)
print(f"Created change request: {request.id}")
```

### Task: Query Recent Changes
```python
from change_management.models import AccountChangeRequest
from datetime import datetime, timedelta

# Last 7 days
week_ago = datetime.now() - timedelta(days=7)
recent = AccountChangeRequest.objects.filter(created_at__gte=week_ago)
print(f"Changes in last 7 days: {recent.count()}")
```

### Task: Export Change Log
```bash
# Via management command (add --export-csv to workflow)
python manage.py process_changes --export-csv export.csv

# Via API with curl
curl -H "Authorization: Token TOKEN" \
  "http://localhost:8000/api/change-requests/?format=csv" > changes.csv
```

---

## ✅ Status Check

Run to verify system health:

```bash
# System check
python manage.py check

# Database migrations
python manage.py showmigrations change_management

# Count records
python manage.py shell -c "from change_management.models import AccountChangeRequest; print(f'Total changes: {AccountChangeRequest.objects.count()}')"
```

---

**System Status:** ✅ **OPERATIONAL**  
**Last Updated:** February 6, 2026  
**Server:** Running on http://localhost:8000/

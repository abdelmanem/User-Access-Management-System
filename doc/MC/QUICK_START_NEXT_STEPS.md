# Quick Start: Next Steps to Complete IAM Governance Implementation

**Status:** Implementation Complete ✅  
**Last Updated:** January 31, 2026

---

## 🎯 Immediate Action Items (Do These First)

### Step 1: Generate Signing Keys (5 minutes)
Run this command in your virtual environment to generate the cryptographic keys needed for immutable audit logs and attestations:

```powershell
# Activate venv first
& "C:\Trae\User-Access-Management-System\venv\Scripts\Activate.ps1"

# Generate signing keys
python manage.py generate_signing_keys
```

**Expected Output:**
```
Generated AUDIT_LOG_SIGNING_KEY: [256-bit hex key]
Generated ATTESTATION_SIGNING_KEY: [256-bit hex key]

Keys saved to: .env.production

Add these to your environment variables or .env file:
AUDIT_LOG_SIGNING_KEY=[value]
ATTESTATION_SIGNING_KEY=[value]
```

✅ **Verification:** Check that keys appear in your `.env.production` or environment

---

### Step 2: Initialize Audit Chain (2 minutes)
Create the anchor event that starts the hash chain for immutable auditing:

```powershell
python manage.py initialize_audit_chain
```

**Expected Output:**
```
Audit chain initialized successfully.
Anchor event ID: [some_id]
```

✅ **Verification:** Check AuditEventLog table for anchor event
```python
from access_management.models import AuditEventLog
anchor = AuditEventLog.objects.filter(event_type='AuditChainInitialized').first()
print(f"Anchor created: {anchor.created_at}")
```

---

### Step 3: Verify Audit Chain Integrity (2 minutes)
Test the immutability verification:

```powershell
python manage.py verify_audit_chain
```

**Expected Output:**
```
✓ Verifying audit chain integrity...
✓ 1 events verified successfully
✓ Hash chain is valid and unbroken
```

✅ **Verification:** All events should pass verification

---

## 🔄 Next: Configure Services

### Step 4: Install Celery & Redis Dependencies (5 minutes)

```powershell
pip install celery redis
```

### Step 5: Start Redis (Background)
You need Redis for Celery task queue. Choose one:

**Option A: Using Windows Subsystem for Linux (WSL)**
```powershell
# In WSL terminal
redis-server
```

**Option B: Using Docker**
```powershell
docker run -d -p 6379:6379 redis:latest
```

**Option C: Windows Redis Package**
- Download from: https://github.com/microsoftarchive/redis/releases
- Run: `redis-server.exe`

✅ **Verification:** 
```powershell
# Test Redis connection
redis-cli ping
# Should output: PONG
```

---

### Step 6: Start Celery Worker (Background Terminal 1)

```powershell
# Activate venv
& "C:\Trae\User-Access-Management-System\venv\Scripts\Activate.ps1"

# Start worker
celery -A user_access_management worker --loglevel=info
```

**Expected Output:**
```
 ---------- celery@COMPUTERNAME v5.x.x
 ---- **** -----
 --- * ***- **** -- [config]
 -- * - **** --- 'CELERY_BROKER_URL': 'redis://localhost:6379/0'
 - ** ---------- [tasks]
    . access_management.tasks.check_review_schedules
    . access_management.tasks.verify_audit_chain
    . access_management.tasks.auto_revoke_overdue_reviews
    . access_management.tasks.escalate_pending_approvals
    . access_management.tasks.check_retention_policies

[2026-01-31 10:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
[2026-01-31 10:00:00,000: INFO/MainProcess] mingle: Trying to create pool with max concurrency of 4...
```

✅ **Verification:** You should see "Connected to redis://..." message

---

### Step 7: Start Celery Beat Scheduler (Background Terminal 2)

```powershell
# Activate venv in NEW terminal
& "C:\Trae\User-Access-Management-System\venv\Scripts\Activate.ps1"

# Start beat scheduler
celery -A user_access_management beat --loglevel=info
```

**Expected Output:**
```
 ---------- celery.beat.EventDispatcher
 ---------- celery.beat.SchedulingError
 -- * ---------- Scheduler: ...
    . check_review_schedules: <crontab: 0 * * * * (run every hour at :00 minutes)>
    . verify_audit_chain: <crontab: 30 0 * * * (run daily at 00:30)>
    . auto_revoke_overdue_reviews: <crontab: 0 1 * * * (run daily at 01:00)>
    . escalate_pending_approvals: <crontab: 0 * * * * (run every hour at :00 minutes)>
    . check_retention_policies: <crontab: 0 2 * 0 (run weekly on Sunday at 02:00)>
```

✅ **Verification:** All 5 tasks should be registered

---

## 🧪 Testing the Implementation

### Test 1: Create a Test Access Request

```python
from accounts.models import CustomUser
from systems.models import System
from access_management.models import UserSystemAccess

# Get test user and system
user = CustomUser.objects.filter(is_staff=False).first()
system = System.objects.first()

# Create access request
access = UserSystemAccess.objects.create(
    user=user,
    system=system,
    access_type='Read Only',
    status='Pending',
    justification='Testing the approval workflow',
    priority='Medium'
)
print(f"Created access ID: {access.id}")
```

### Test 2: Verify Audit Log Created

```python
from access_management.models import AuditEventLog

# Check audit logs for this access
logs = AuditEventLog.objects.filter(
    event_data__contains={'user_system_access_id': access.id}
)
print(f"Audit logs created: {logs.count()}")
for log in logs:
    print(f"  - {log.event_type} at {log.created_at}")
```

### Test 3: Check Risk Score

```python
from access_management.risk import RiskScorer

scorer = RiskScorer()
risk = scorer.calculate_risk_score(
    access_type='Admin',
    system_sensitivity='High',
    user_tenure_days=30,
    is_admin_access=True,
    justification_quality=7
)
print(f"Risk Score: {risk}/100")
# Admin access + new user + high sensitivity = HIGH/CRITICAL risk
```

### Test 4: Upload Evidence

Go to: `http://localhost:8000/access/assignments/[access_id]/evidence/upload/`

1. Upload a screenshot or document
2. File hash should auto-compute
3. Check browser console for "File integrity verified"

### Test 5: Approve Request

Go to: `http://localhost:8000/access/approvals/`

1. If there are pending approvals, click one
2. Select Approve/Reject with comments
3. Submit
4. Check AuditEventLog for approval entry with signature

---

## 🔐 Security Configuration

### Add Signing Keys to Settings
Edit `user_access_management/settings.py`:

```python
# Audit & Attestation Signing Keys (from generate_signing_keys management command)
AUDIT_LOG_SIGNING_KEY = os.environ.get('AUDIT_LOG_SIGNING_KEY', 'dev-key-change-in-production')
ATTESTATION_SIGNING_KEY = os.environ.get('ATTESTATION_SIGNING_KEY', 'dev-key-change-in-production')

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_SERIALIZER = 'json'

# Soft Delete Retention Policy (days)
SOFT_DELETE_RETENTION_DAYS = 90

# Access Review Schedule Defaults
DEFAULT_ACCESS_REVIEW_FREQUENCY_DAYS = 90
OVERDUE_REVIEW_ESCALATION_DAYS = 180
```

### Configure Email (Optional but Recommended)

```python
# Email Configuration for Notifications
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# Approval escalation recipients
APPROVAL_ESCALATION_EMAIL = 'security-team@company.com'
SECURITY_TEAM_EMAIL = 'security-team@company.com'
```

---

## 🎯 Verify Complete Implementation

### Checklist: All 10 Gaps Remediated ✅

- [ ] **Gap 1 (FSM):** Lifecycle transitions tracked in lifecycle_timeline JSON
  - Verify: UserSystemAccess.objects.first().lifecycle_timeline shows transitions

- [ ] **Gap 2 (Immutable Audit):** AuditEventLog with hash chaining
  - Verify: AuditEventLog.objects.count() > 0

- [ ] **Gap 3 (Historical):** AccessInstance tracks multiple accesses per user-system
  - Verify: AccessInstance.objects.filter(instance_number__gt=1).exists()

- [ ] **Gap 4 (Versioning):** AccessVersion tracks permission changes
  - Verify: AccessVersion.objects.count() > 0

- [ ] **Gap 5 (Soft Delete):** Records soft-deleted, not hard-deleted
  - Verify: UserSystemAccess.objects.filter(is_deleted=True).count()

- [ ] **Gap 6 (Evidence):** EvidenceArtifact centralized repository
  - Verify: EvidenceArtifact.objects.count() > 0 after upload test

- [ ] **Gap 7 (SOD):** ApprovalWorkflow enforces segregation of duties
  - Verify: ApprovalWorkflow.objects.count() > 0

- [ ] **Gap 8 (Automation):** AccessReviewSchedule with Celery tasks
  - Verify: Celery beat shows 5 registered tasks

- [ ] **Gap 9 (Risk):** RiskScorer drives approval routing
  - Verify: RiskScorer().calculate_risk_score() returns 0-100

- [ ] **Gap 10 (Attestation):** Formal attestations with digital signatures
  - Verify: Attestation.objects.count() > 0 after formal attestation

---

## 📊 Monitoring Checklist

### Daily Tasks
- [ ] Monitor Celery tasks via logs for errors
- [ ] Verify Redis connection stable
- [ ] Check AuditEventLog integrity (daily task runs at 00:30)

### Weekly Tasks
- [ ] Review escalated approvals
- [ ] Check soft-deleted retention (runs Sunday 02:00)
- [ ] Verify audit chain integrity

### Monthly Tasks
- [ ] Generate compliance report
- [ ] Review access attestations
- [ ] Audit approval decisions for SOD violations

---

## 🆘 Troubleshooting

### Issue: "ConnectionError: Error -2 connecting to localhost:6379"
**Solution:** Redis is not running. Start Redis (see Step 5 above)

### Issue: "celery.exceptions.ImproperlyConfigured: CELERY_BROKER_URL is not set"
**Solution:** Add to settings.py:
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
```

### Issue: Audit chain verification fails
**Solution:** Re-initialize:
```powershell
python manage.py initialize_audit_chain --force
```

### Issue: Keys not found in environment
**Solution:** Check .env.production was created:
```powershell
Get-Content .env.production | Select-String "AUDIT_LOG_SIGNING_KEY"
```

---

## 📞 Quick Reference

| Task | Command | Time |
|------|---------|------|
| Generate Keys | `python manage.py generate_signing_keys` | 1 min |
| Initialize Chain | `python manage.py initialize_audit_chain` | 1 min |
| Verify Integrity | `python manage.py verify_audit_chain` | 1 min |
| Start Worker | `celery -A user_access_management worker --loglevel=info` | 30 sec |
| Start Beat | `celery -A user_access_management beat --loglevel=info` | 30 sec |
| Run Tests | `python manage.py test access_management` | 5-10 min |
| Run Full QA | Full test suite + staging validation | 1-2 hours |

---

## ✅ Success Indicators

**Implementation is complete when you see:**

✅ All 5 Celery tasks registered in beat scheduler  
✅ Audit chain verification passes  
✅ AuditEventLog entries have valid hash chains  
✅ Risk scores calculated and returned 0-100  
✅ Evidence files verified with SHA-256  
✅ Approval workflows route to appropriate approvers  
✅ Attestations immutable after finalization  
✅ Soft-deleted records retained 90+ days  

---

**Next: See `IAM_GOVERNANCE_IMPLEMENTATION.md` for comprehensive documentation**

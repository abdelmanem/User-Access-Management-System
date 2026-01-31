# IAM Governance Architecture Reference
**Quick Implementation Guide & Database Schema Design**

---

## Quick Reference: Model Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER SYSTEM ACCESS LIFECYCLE                │
└─────────────────────────────────────────────────────────────────┘

CustomUser ─1──→ UserSystemAccess ←─1── System
                       │
                       ├─→ AccessInstance (multiple grants)
                       │         │
                       │         └─→ AccessVersion (privilege history)
                       │                    │
                       │                    └─→ EvidenceArtifact
                       │
                       ├─→ AuditEventLog (immutable trail)
                       │         │
                       │         └─→ EvidenceArtifact
                       │
                       ├─→ ApprovalWorkflow
                       │         │
                       │         └─→ Approval (multi-step)
                       │
                       ├─→ QuarterlyAccessReview
                       │         │
                       │         ├─→ Attestation
                       │         └─→ EvidenceArtifact
                       │
                       ├─→ Attestation (legal record)
                       │
                       ├─→ AccessReviewSchedule
                       │
                       └─→ EvidenceArtifact (comprehensive)

┌─────────────────────────────────────────────────────────────────┐
│                       AUDIT & COMPLIANCE                        │
└─────────────────────────────────────────────────────────────────┘

AuditEventLog ─→ (immutable, hash-chained, signed)
    ├─ Event ID (deduplication)
    ├─ Actor (user + IP + session)
    ├─ Target (what changed)
    ├─ Hash Chain (integrity)
    ├─ Signature (authenticity)
    └─ Retention (legal hold)

EvidenceArtifact ─→ (immutable, verified, classified)
    ├─ File hash verification
    ├─ Digital signature
    ├─ Access controls
    ├─ Retention policy
    └─ Legal hold support
```

---

## Database Schema Design

### Core Access Lifecycle

```sql
-- UserSystemAccess: Current active access state
CREATE TABLE access_management_usersystemaccess (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    system_id BIGINT NOT NULL,
    
    -- Status (FSM controlled)
    status VARCHAR(20) NOT NULL DEFAULT 'Pending',
    status_changed_at DATETIME,
    status_changed_by_id BIGINT,
    status_change_reason TEXT,
    lifecycle_timeline JSONB,  -- Complete state history
    
    -- Risk assessment
    risk_score INTEGER DEFAULT 0,
    risk_level VARCHAR(20) DEFAULT 'MEDIUM',
    risk_factors JSONB,
    
    -- Dates
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    access_start_date DATETIME,
    access_end_date DATETIME,
    request_date DATETIME,
    approval_date DATETIME,
    
    -- Soft delete
    is_deleted BOOLEAN DEFAULT FALSE INDEX,
    deleted_date DATETIME,
    deleted_by_id BIGINT,
    
    -- Legal hold
    legal_hold_active BOOLEAN DEFAULT FALSE,
    legal_hold_reason TEXT,
    
    UNIQUE KEY (user_id, system_id),
    INDEX (status),
    INDEX (risk_level),
    INDEX (is_deleted),
    INDEX (legal_hold_active),
    FOREIGN KEY (user_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (system_id) REFERENCES systems_system(id),
    FOREIGN KEY (status_changed_by_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (deleted_by_id) REFERENCES accounts_customuser(id)
);

-- AccessInstance: Historical grants (multiple per user-system)
CREATE TABLE access_management_accessinstance (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    system_id BIGINT NOT NULL,
    instance_number INTEGER NOT NULL,
    
    -- Lifecycle dates
    granted_date DATETIME NOT NULL,
    requested_date DATETIME NOT NULL,
    approved_date DATETIME,
    activated_date DATETIME,
    revoked_date DATETIME,
    revocation_reason TEXT,
    
    -- Access details
    access_type VARCHAR(50) NOT NULL,
    access_level VARCHAR(100),
    
    -- Approvals
    approved_by_id BIGINT,
    revoked_by_id BIGINT,
    
    -- Status
    status VARCHAR(20) DEFAULT 'Active',
    is_deleted BOOLEAN DEFAULT FALSE INDEX,
    
    UNIQUE KEY (user_id, system_id, instance_number),
    INDEX (user_id, system_id, granted_date),
    INDEX (status),
    FOREIGN KEY (user_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (system_id) REFERENCES systems_system(id),
    FOREIGN KEY (approved_by_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (revoked_by_id) REFERENCES accounts_customuser(id)
);

-- AccessVersion: Privilege changes within instance
CREATE TABLE access_management_accessversion (
    id BIGINT PRIMARY KEY,
    access_instance_id BIGINT NOT NULL,
    version_number INTEGER NOT NULL,
    is_current BOOLEAN DEFAULT TRUE INDEX,
    
    -- Privilege details
    access_type VARCHAR(50) NOT NULL,
    access_level VARCHAR(100),
    granted_permissions JSONB,
    
    -- Change tracking
    version_changed_date DATETIME NOT NULL,
    version_changed_by_id BIGINT,
    change_type VARCHAR(50),  -- INITIAL, ESCALATION, DOWNGRADE, LATERAL
    change_reason TEXT,
    
    -- Approval
    change_approved_by_id BIGINT,
    change_approved_date DATETIME,
    
    -- Escalation detection
    is_privilege_escalation BOOLEAN DEFAULT FALSE INDEX,
    escalation_requires_approval BOOLEAN DEFAULT TRUE,
    
    -- Comparison
    previous_version_id BIGINT,
    permissions_added JSONB,
    permissions_removed JSONB,
    
    UNIQUE KEY (access_instance_id, version_number),
    INDEX (is_privilege_escalation),
    FOREIGN KEY (access_instance_id) REFERENCES access_management_accessinstance(id),
    FOREIGN KEY (version_changed_by_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (change_approved_by_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (previous_version_id) REFERENCES access_management_accessversion(id)
);
```

### Audit & Compliance

```sql
-- AuditEventLog: Immutable event trail
CREATE TABLE access_management_auditeventlog (
    id BIGINT PRIMARY KEY,
    event_id VARCHAR(64) UNIQUE NOT NULL INDEX,
    event_type VARCHAR(50) NOT NULL INDEX,
    
    -- Actor (WHO)
    actor_user_id BIGINT NOT NULL,
    actor_username VARCHAR(255) NOT NULL,
    actor_ip_address VARCHAR(45) NOT NULL,
    actor_session_id VARCHAR(255),
    
    -- Target (WHAT)
    target_type VARCHAR(50) NOT NULL,
    target_id INTEGER NOT NULL,
    target_data JSONB NOT NULL,
    
    -- Temporal (WHEN)
    event_timestamp DATETIME NOT NULL INDEX,
    event_timestamp_client DATETIME,
    created_at DATETIME NOT NULL INDEX,
    
    -- Context (WHY)
    context JSONB,
    
    -- Integrity
    event_hash VARCHAR(256) NOT NULL INDEX,
    previous_event_hash VARCHAR(256),
    hash_chain_valid BOOLEAN DEFAULT TRUE INDEX,
    signature VARCHAR(512) NOT NULL,
    signature_algorithm VARCHAR(50) DEFAULT 'HMAC-SHA256',
    
    -- Compliance
    compliance_relevant BOOLEAN DEFAULT TRUE,
    legal_hold BOOLEAN DEFAULT FALSE,
    legal_hold_reason TEXT,
    retention_until DATE NOT NULL,
    is_finalized BOOLEAN DEFAULT FALSE,
    finalized_at DATETIME,
    
    INDEX (event_type, event_timestamp),
    INDEX (target_type, target_id),
    INDEX (actor_user_id, event_timestamp),
    INDEX (legal_hold),
    FOREIGN KEY (actor_user_id) REFERENCES accounts_customuser(id)
);

-- EvidenceArtifact: Centralized evidence repository
CREATE TABLE access_management_evidenceartifact (
    id BIGINT PRIMARY KEY,
    artifact_id VARCHAR(64) UNIQUE NOT NULL INDEX,
    artifact_type VARCHAR(50) NOT NULL INDEX,
    classification VARCHAR(50) DEFAULT 'INTERNAL',
    
    -- Content
    title VARCHAR(255) NOT NULL,
    description TEXT,
    file_artifact VARCHAR(255),
    file_size_bytes BIGINT,
    file_hash VARCHAR(64),
    file_format VARCHAR(50),
    
    -- External reference
    external_reference_url VARCHAR(2048),
    external_reference_id VARCHAR(255),
    external_system VARCHAR(50),
    
    -- Relationships (can link to multiple)
    access_record_id BIGINT,
    access_instance_id BIGINT,
    access_version_id BIGINT,
    review_record_id BIGINT,
    audit_event_id BIGINT,
    
    -- Temporal
    artifact_date DATETIME NOT NULL,
    submitted_date DATETIME NOT NULL INDEX,
    submitted_by_id BIGINT,
    
    -- Verification
    verified BOOLEAN DEFAULT FALSE INDEX,
    verified_by_id BIGINT,
    verified_date DATETIME,
    verification_notes TEXT,
    
    -- Digital signature
    signature VARCHAR(512),
    signature_algorithm VARCHAR(50) DEFAULT 'HMAC-SHA256',
    signed_by_id BIGINT,
    signed_date DATETIME,
    
    -- Retention
    retention_until DATE NOT NULL,
    legal_hold BOOLEAN DEFAULT FALSE,
    is_finalized BOOLEAN DEFAULT FALSE,
    
    -- Access control
    access_level VARCHAR(50) DEFAULT 'INTERNAL',
    
    INDEX (artifact_type, artifact_date),
    INDEX (access_record_id, artifact_date),
    INDEX (verified),
    INDEX (legal_hold),
    FOREIGN KEY (access_record_id) REFERENCES access_management_usersystemaccess(id),
    FOREIGN KEY (access_instance_id) REFERENCES access_management_accessinstance(id),
    FOREIGN KEY (access_version_id) REFERENCES access_management_accessversion(id),
    FOREIGN KEY (submitted_by_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (verified_by_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (signed_by_id) REFERENCES accounts_customuser(id)
);
```

### Approvals & Attestation

```sql
-- ApprovalWorkflow: Multi-step approval process
CREATE TABLE access_management_approvalworkflow (
    id BIGINT PRIMARY KEY,
    workflow_id VARCHAR(100) UNIQUE NOT NULL,
    access_record_id BIGINT UNIQUE NOT NULL,
    approval_rule_id BIGINT,
    
    status VARCHAR(50) DEFAULT 'PENDING' INDEX,
    is_active BOOLEAN DEFAULT TRUE INDEX,
    created_date DATETIME NOT NULL,
    
    FOREIGN KEY (access_record_id) REFERENCES access_management_usersystemaccess(id),
    FOREIGN KEY (approval_rule_id) REFERENCES access_management_approvalrule(id)
);

-- Approval: Individual approval step
CREATE TABLE access_management_approval (
    id BIGINT PRIMARY KEY,
    workflow_id BIGINT NOT NULL,
    step_number INTEGER NOT NULL,
    
    required_role_id BIGINT,
    assigned_to_id BIGINT,
    
    status VARCHAR(50) DEFAULT 'PENDING' INDEX,
    approved_by_id BIGINT,
    approved_date DATETIME,
    approval_comments TEXT,
    rejection_reason TEXT,
    
    -- SOD validation
    sod_conflict_detected BOOLEAN DEFAULT FALSE,
    sod_conflict_reason TEXT,
    
    UNIQUE KEY (workflow_id, step_number),
    FOREIGN KEY (workflow_id) REFERENCES access_management_approvalworkflow(id),
    FOREIGN KEY (assigned_to_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (approved_by_id) REFERENCES accounts_customuser(id)
);

-- Attestation: Legal record
CREATE TABLE access_management_attestation (
    id BIGINT PRIMARY KEY,
    attestation_id VARCHAR(100) UNIQUE NOT NULL,
    attestation_type VARCHAR(50) NOT NULL,
    
    -- Links
    access_record_id BIGINT,
    review_record_id BIGINT,
    
    -- Attestor
    attested_by_id BIGINT NOT NULL REFERENCES accounts_customuser(id),
    attested_by_title VARCHAR(255),
    attested_by_email VARCHAR(254),
    
    -- Statement & signature
    statement TEXT NOT NULL,
    attestation_date DATETIME NOT NULL,
    signature VARCHAR(512),
    signature_method VARCHAR(50),
    signature_verified BOOLEAN DEFAULT FALSE,
    signature_verified_by_id BIGINT,
    signature_verified_date DATETIME,
    
    -- Audit
    ip_address VARCHAR(45),
    user_agent TEXT,
    session_identifier VARCHAR(255),
    
    -- Compliance
    legal_hold BOOLEAN DEFAULT TRUE,
    retention_until DATE NOT NULL,
    is_finalized BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (attested_by_id) REFERENCES accounts_customuser(id),
    FOREIGN KEY (signature_verified_by_id) REFERENCES accounts_customuser(id)
);
```

---

## Implementation Priority Matrix

```
IMPACT vs EFFORT

         HIGH EFFORT
              ▲
              │
              │    [4] Evidence Repo
              │    [10] Attestation
              │
  HIGH IMPACT │────[1] FSM ────────[8] Review Auto
              │    [2] Audit
              │         │
              │    [7] SOD
              │    [9] Risk-Based
              │         │
              │    [3] Historical
              │    [5] Soft Delete
              │    [6] Versioning
              │
              └────────────────────────────► LOW EFFORT
            LOW IMPACT

IMPLEMENTATION SEQUENCE:
Phase 1 (Weeks 1-4):    [1] FSM → [2] Audit Logs
Phase 2 (Weeks 5-8):    [7] SOD → [9] Risk-Based → [3] Historical
Phase 3 (Weeks 9-12):   [4] Evidence → [10] Attestation
Phase 4 (Weeks 13-16):  [8] Review Auto → [6] Versioning → [5] Soft Delete
```

---

## Testing Checklist

### Unit Tests
- [ ] FSM transition validation
- [ ] Risk score calculation
- [ ] Hash chain integrity
- [ ] SOD conflict detection
- [ ] Access versioning logic

### Integration Tests
- [ ] End-to-end approval workflow
- [ ] Multi-step approval with escalation
- [ ] Evidence artifact linking
- [ ] Audit event generation
- [ ] Soft deletion and restoration

### Compliance Tests
- [ ] AUDIT_CHAIN_INTEGRITY verification
- [ ] EVIDENCE_RETENTION policy enforcement
- [ ] LEGAL_HOLD immutability
- [ ] SOD rule enforcement
- [ ] Risk-based routing

### Performance Tests
- [ ] Query: Find all access for user (< 100ms)
- [ ] Query: Recent audit events (< 200ms)
- [ ] Query: Escalated reviews (< 150ms)
- [ ] Audit chain verification (< 5s for 1M events)
- [ ] Hash chain integrity check (< 10s for 1M events)

---

## Deployment Runbook

### Pre-Deployment
```bash
# 1. Backup database
mysqldump -u root -p uams_db > backup_$(date +%Y%m%d).sql

# 2. Test migrations on staging
python manage.py migrate --plan
python manage.py migrate access_management

# 3. Verify audit logging
python manage.py test access_management.tests.AuditTests

# 4. Generate signing keys
python manage.py generate_audit_keys
python manage.py generate_attestation_keys
```

### Deployment
```bash
# 1. Enable maintenance mode
touch maintenance.lock

# 2. Run migrations
python manage.py migrate

# 3. Initialize audit log chain
python manage.py initialize_audit_chain

# 4. Disable maintenance mode
rm maintenance.lock

# 5. Verify
python manage.py verify_audit_chain
python manage.py test access_management
```

### Post-Deployment
```bash
# 1. Check audit logs
SELECT COUNT(*) FROM access_management_auditeventlog;

# 2. Verify FSM transitions
python manage.py shell
>>> from access_management.models import UserSystemAccess
>>> access = UserSystemAccess.objects.first()
>>> print(access.get_all_transitions())

# 3. Monitor for errors
tail -f logs/django.log | grep -i error

# 4. Verify retention policy
python manage.py check_retention_policies
```

---

## Performance Optimization

### Database Indexing
```sql
-- High-frequency queries
CREATE INDEX idx_audit_actor_time ON access_management_auditeventlog(actor_user_id, event_timestamp DESC);
CREATE INDEX idx_audit_type_time ON access_management_auditeventlog(event_type, event_timestamp DESC);
CREATE INDEX idx_access_status ON access_management_usersystemaccess(status) WHERE is_deleted = FALSE;
CREATE INDEX idx_approval_status ON access_management_approval(status, assigned_to_id);

-- Hash chain verification
CREATE INDEX idx_audit_hash_chain ON access_management_auditeventlog(event_timestamp, event_hash);

-- Retention policy enforcement
CREATE INDEX idx_audit_retention ON access_management_auditeventlog(retention_until);
CREATE INDEX idx_evidence_retention ON access_management_evidenceartifact(retention_until);
```

### Caching Strategy
```python
# Cache approval rules
CACHES = {
    'approval_rules': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 3600,  # 1 hour
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# Cache risk scores (short-lived)
@cache.cached(timeout=300)
def get_user_access_risk_level(user_id):
    return UserSystemAccess.objects.filter(
        user_id=user_id
    ).aggregate(max_risk=Max('risk_score'))['max_risk']
```

### Query Optimization
```python
# Use select_related for foreign keys
access = UserSystemAccess.objects.select_related(
    'user',
    'system',
    'approved_by',
    'status_changed_by'
).get(pk=pk)

# Use prefetch_related for reverse FK
users = CustomUser.objects.prefetch_related(
    'usersystemaccess_set'
).filter(department_id=dept_id)

# Bulk operations
AuditEventLog.objects.bulk_create(events, batch_size=1000)
```

---

## Monitoring & Alerting

### Key Metrics
```python
# Approval backlog
SELECT COUNT(*) FROM access_management_approval
WHERE status = 'PENDING' AND assigned_to_id IS NOT NULL;

# Escalated reviews
SELECT COUNT(*) FROM access_management_accessreviewschedule
WHERE is_escalated = TRUE;

# Overdue reviews
SELECT COUNT(*) FROM access_management_accessreviewschedule
WHERE review_status = 'OVERDUE';

# Audit chain breaks
SELECT COUNT(*) FROM access_management_auditeventlog
WHERE hash_chain_valid = FALSE;

# Access approaching expiration
SELECT COUNT(*) FROM access_management_usersystemaccess
WHERE status = 'Active' 
  AND access_end_date BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 30 DAY);
```

### Alert Rules
```yaml
# Critical
- name: audit_chain_broken
  condition: hash_chain_valid = FALSE
  severity: CRITICAL
  action: page_security_team

- name: unreconciled_approval
  condition: approval_workflow.status = 'IN_PROGRESS' for > 48 hours
  severity: HIGH
  action: email_it_manager

# Warning
- name: escalated_review_count
  condition: escalated_reviews > 10
  severity: MEDIUM
  action: email_compliance

- name: high_risk_access_pending
  condition: usersystemaccess.risk_level = 'CRITICAL' AND status = 'Pending' for > 24 hours
  severity: HIGH
  action: email_ciso
```

---

## Migration Examples

### Adding New Approval Rule
```python
from access_management.models import ApprovalRule
from accounts.models import Role

rule = ApprovalRule.objects.create(
    rule_id='FINANCIAL_ADMIN',
    access_type='Admin',
    system_id=5,  # Financial System
    approvers_required=2,
    additional_rules={
        'require_system_owner': True,
        'require_security': True,
    },
    conflict_of_interest_rules={
        'cannot_approve_self': True,
        'cannot_approve_team_member': True,
    }
)

rule.approver_roles.add(
    Role.objects.get(name='IT_DIRECTOR'),
    Role.objects.get(name='CFO')
)
```

### Creating Access Instance After Revocation
```python
from access_management.models import AccessInstance
from django.utils import timezone

# Previous instance
old_instance = AccessInstance.objects.filter(
    user=user,
    system=system
).order_by('-instance_number').first()

# Grant access again
new_instance = AccessInstance.create_next_instance(
    user=user,
    system=system,
    requested_date=timezone.now(),
    access_type='Read/Write',
    access_level='Developer',
    approved_by=approver,
    approved_date=timezone.now(),
)

# New version in new instance
AccessVersion.create_version(
    access_instance=new_instance,
    access_type='Read/Write',
    access_level='Developer',
    change_type='INITIAL',
    change_reason='Re-grant after previous revocation',
    version_changed_by=approver,
)
```

---

## Troubleshooting Guide

### Audit Chain Broken
```bash
# Check integrity
python manage.py verify_audit_chain

# Find break point
SELECT * FROM access_management_auditeventlog 
WHERE hash_chain_valid = FALSE 
ORDER BY event_timestamp 
LIMIT 1;

# Investigate event
SELECT * FROM access_management_auditeventlog 
WHERE id = [broken_id];

# Escalate to security team immediately
```

### Approval Stuck
```bash
# Find stuck approval
SELECT * FROM access_management_approval
WHERE status = 'PENDING' AND assigned_to_id IS NULL;

# Resolve by reassigning
UPDATE access_management_approval
SET assigned_to_id = [new_approver_id]
WHERE id = [approval_id];
```

### Access Soft-Delete Recovery
```bash
# Find deleted access
SELECT * FROM access_management_usersystemaccess
WHERE is_deleted = TRUE 
  AND deleted_date > DATE_SUB(NOW(), INTERVAL 30 DAY);

# Restore
access = UserSystemAccess.all_objects.get(pk=pk)
access.restore(user=current_user, reason="Mistaken deletion")
```

---

This reference guide provides the complete technical foundation for implementing the 10-gap remediation design.

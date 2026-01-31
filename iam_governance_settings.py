"""
IAM Governance Settings Configuration
Add these to your Django settings.py for full gap remediation support
"""

# ============================================================================
# 1. FSM (Finite State Machine) Configuration - Gap 1
# ============================================================================
# Required: pip install django-fsm
FSM_STATE_FIELD = 'status'
FSM_SAVE_TRANSITIONS = True  # Log transitions to database

# ============================================================================
# 2. Audit Logging Configuration - Gap 2
# ============================================================================
# Generate 256-bit signing keys: python manage.py generate_signing_keys
AUDIT_LOG_SIGNING_KEY = os.environ.get('AUDIT_LOG_SIGNING_KEY', '')  # Set via .env
AUDIT_SIGNATURE_ALGORITHM = 'HMAC-SHA256'

# Enable audit logging for all access model changes
AUDIT_LOG_MODELS = [
    'access_management.UserSystemAccess',
    'access_management.ApprovalWorkflow',
    'access_management.Attestation',
]

# ============================================================================
# 3. Soft Delete Configuration - Gap 5
# ============================================================================
# Retention period in days before hard deletion of soft-deleted records
SOFT_DELETE_RETENTION_DAYS = 90
SOFT_DELETE_HARD_DELETE_ENABLED = False  # Prevent accidental hard deletes

# ============================================================================
# 4. Approval Workflow Configuration - Gap 7
# ============================================================================
# Email recipients for approval escalations
APPROVAL_ESCALATION_EMAIL = os.environ.get('APPROVAL_ESCALATION_EMAIL', 'approvals@company.com')
APPROVAL_ESCALATION_HOURS = 24  # Escalate if pending > 24 hours
SECURITY_TEAM_EMAIL = os.environ.get('SECURITY_TEAM_EMAIL', 'security@company.com')

# Segregation of Duties (SOD) enforcement
SOD_CANNOT_APPROVE_SELF = True
SOD_CANNOT_APPROVE_REPORTS = True  # Prevent managers from approving their own reports

# ============================================================================
# 5. Access Review Configuration - Gap 8
# ============================================================================
# Default review frequency in days
DEFAULT_REVIEW_FREQUENCY_DAYS = 90
REVIEW_ESCALATION_DAYS = 180  # Auto-escalate if overdue

# Review schedule Celery beat tasks
CELERY_BEAT_SCHEDULE = {
    'check-access-reviews': {
        'task': 'access_management.check_review_schedules',
        'schedule': crontab(minute=0),  # Every hour
    },
    'verify-audit-chain': {
        'task': 'access_management.verify_audit_chain',
        'schedule': crontab(hour=0, minute=0),  # Daily at midnight
    },
    'auto-revoke-overdue-access': {
        'task': 'access_management.auto_revoke_overdue_reviews',
        'schedule': crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    'escalate-pending-approvals': {
        'task': 'access_management.escalate_pending_approvals',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
    'check-retention-policies': {
        'task': 'access_management.check_retention_policies',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Weekly Sunday 2 AM
    },
}

# ============================================================================
# 6. Risk Scoring Configuration - Gap 9
# ============================================================================
RISK_SCORING_ENABLED = True
RISK_SCORING_WEIGHTS = {
    'access_type': 40,           # Admin/Super Admin = high risk
    'system_sensitivity': 30,    # Based on data classification
    'user_tenure': 10,           # New users = higher risk
    'is_admin_access': 15,       # Admin flag = high risk
    'justification_quality': 5,  # Detailed justification = lower risk
}

# Risk-based approval routing
RISK_BASED_APPROVAL_ROUTING = {
    'critical': {  # Score >= 75
        'approvers_required': 2,
        'approver_roles': ['ciso', 'system_owner', 'manager'],
        'requires_evidence': True,
        'requires_attestation': True,
    },
    'high': {  # Score >= 50
        'approvers_required': 2,
        'approver_roles': ['system_owner', 'manager'],
        'requires_evidence': True,
        'requires_attestation': False,
    },
    'medium': {  # Score >= 25
        'approvers_required': 1,
        'approver_roles': ['manager', 'system_owner'],
        'requires_evidence': False,
        'requires_attestation': False,
    },
    'low': {  # Score < 25
        'approvers_required': 1,
        'approver_roles': ['manager'],
        'requires_evidence': False,
        'requires_attestation': False,
    },
}

# ============================================================================
# 7. Attestation Configuration - Gap 10
# ============================================================================
ATTESTATION_SIGNING_KEY = os.environ.get('ATTESTATION_SIGNING_KEY', '')  # Set via .env
ATTESTATION_SIGNATURE_METHOD = 'hmac'  # 'digital_certificate', 'electronic_signature', 'hmac', 'session'
ATTESTATION_REQUIRES_APPROVAL = True

# Standard attestation statement template
ATTESTATION_STATEMENT_TEMPLATE = """
I hereby attest that:
1. I have received the requested access as documented.
2. The access is necessary for my business role and responsibilities.
3. I have read and understand the security requirements and compliance obligations.
4. I will use this access responsibly and only for authorized business purposes.
5. I understand that unauthorized use may result in disciplinary action.
"""

# ============================================================================
# 8. Evidence Repository Configuration - Gap 6
# ============================================================================
EVIDENCE_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
EVIDENCE_ALLOWED_FORMATS = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx']
EVIDENCE_UPLOAD_PATH = 'evidence_artifacts/'

# ============================================================================
# 9. Email Configuration
# ============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.company.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@company.com')

# ============================================================================
# 10. Logging Configuration for IAM
# ============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'audit_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/audit.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'access_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/access.log',
            'maxBytes': 10485760,
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'access_management': {
            'handlers': ['access_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'audit': {
            'handlers': ['audit_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# 11. Celery Configuration
# ============================================================================
# Required: pip install celery redis
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# ============================================================================
# 12. Compliance & Security Settings
# ============================================================================
COMPLIANCE_FRAMEWORKS = ['ISO27001', 'SOC2', 'NIST800-53', 'HIPAA']

# Custom permissions for IAM
IAM_CUSTOM_PERMISSIONS = [
    ('can_approve_access', 'Can approve access requests'),
    ('can_reject_access', 'Can reject access requests'),
    ('can_upload_evidence', 'Can upload evidence artifacts'),
    ('can_attest_access', 'Can attest to access assignments'),
    ('can_review_access', 'Can conduct access reviews'),
    ('can_revoke_access', 'Can revoke access'),
    ('can_view_audit_logs', 'Can view immutable audit logs'),
    ('can_verify_audit_chain', 'Can verify audit chain integrity'),
]

# ============================================================================
# 13. Feature Flags
# ============================================================================
FEATURE_FLAGS = {
    'FSM_ENABLED': True,
    'IMMUTABLE_AUDIT_LOGS_ENABLED': True,
    'SOFT_DELETE_ENABLED': True,
    'ACCESS_VERSIONING_ENABLED': True,
    'APPROVAL_WORKFLOWS_ENABLED': True,
    'RISK_SCORING_ENABLED': True,
    'ATTESTATION_ENABLED': True,
    'AUTO_REVIEW_SCHEDULING_ENABLED': True,
    'EVIDENCE_REPOSITORY_ENABLED': True,
}

print("✓ IAM Governance configuration loaded")

import json
import hashlib
import hmac
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models.deletion import ProtectedError

# django-fsm is optional in environment; import if available
try:
    from django_fsm import FSMField, transition
except Exception:
    FSMField = None
    def transition(*args, **kwargs):
        def _decorator(func):
            return func
        return _decorator


class ActiveAccessManager(models.Manager):
    """Manager that excludes soft-deleted records by default."""
    
    def get_queryset(self):
        """Return queryset excluding soft-deleted records."""
        return super().get_queryset().filter(is_deleted=False)


class UserSystemAccess(models.Model):
    """
    UserSystemAccess model for managing user access to systems
    Tracks access requests, approvals, and status
    """
    
    ACCESS_TYPE_CHOICES = [
        ('Full Access', 'Full Access'),
        ('Read Only', 'Read Only'),
        ('Read/Write', 'Read/Write'),
        ('Admin', 'Administrator'),
        ('Super Admin', 'Super Administrator'),
        ('Limited', 'Limited Access'),
        ('Custom', 'Custom Access'),
        ('Temporary', 'Temporary Access'),
    ]
    
    STATUS_CHOICES = [
        ('Pending', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Active', 'Active'),
        ('Suspended', 'Suspended'),
        ('Revoked', 'Revoked'),
        ('Expired', 'Expired'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    ]
    
    REQUEST_TYPE_CHOICES = [
        ('New Access', 'New Access Request'),
        ('Access Renewal', 'Access Renewal'),
        ('Access Upgrade', 'Access Upgrade'),
        ('Access Downgrade', 'Access Downgrade'),
        ('Emergency Access', 'Emergency Access'),
    ]
    
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='system_accesses',
        help_text="User requesting/receiving access"
    )
    
    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='user_accesses',
        help_text="System being accessed"
    )
    
    access_type = models.CharField(
        max_length=20,
        choices=ACCESS_TYPE_CHOICES,
        default='Read Only',
        help_text="Type of access being granted"
    )
    
    # lifecycle state: prefer FSMField if available, otherwise keep CharField
    if FSMField:
        status = FSMField(
            max_length=20,
            choices=STATUS_CHOICES,
            default='Pending',
            protected=True,
            help_text="Current status of the access request"
        )
    else:
        status = models.CharField(
            max_length=20,
            choices=STATUS_CHOICES,
            default='Pending',
            help_text="Current status of the access request"
        )

    # FSM lifecycle timeline: list of transition records
    lifecycle_timeline = models.JSONField(default=list, blank=True)

    status_changed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_changed_by_users',
        help_text="Last user who changed status"
    )

    status_changed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Timestamp of the last status change"
    )
    
    request_type = models.CharField(
        max_length=20,
        choices=REQUEST_TYPE_CHOICES,
        default='New Access',
        help_text="Type of access request"
    )
    
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='Medium',
        help_text="Request priority level"
    )
    
    requested_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_requests_made',
        help_text="User who made the request (for requests made by managers)"
    )
    
    request_date = models.DateTimeField(
        auto_now_add=True,
        help_text="Date when access was requested"
    )
    
    requested_access_duration = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Requested access duration in days (optional)"
    )
    
    business_justification = models.TextField(
        help_text="Business justification for access request"
    )
    
    technical_requirements = models.TextField(
        blank=True,
        null=True,
        help_text="Technical requirements or specifications"
    )
    
    # Approval details
    approved_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_approvals',
        help_text="User who approved the access"
    )
    
    approval_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date when access was approved"
    )
    
    approval_comments = models.TextField(
        blank=True,
        null=True,
        help_text="Comments from approver"
    )
    
    rejection_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for rejection (if rejected)"
    )

    # Link to change management workflow for unified approval (RHG 4.4)
    change_request = models.ForeignKey(
        'change_management.AccountChangeRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_assignments',
        help_text="Associated change request in change management workflow"
    )

    # System Owner authorization (RHG 4.4)
    system_owner_approved = models.BooleanField(
        default=False,
        help_text="System Owner has authorized this access in the external system",
    )

    system_owner_approval_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the System Owner approved this access",
    )

    system_owner_approver = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='system_owner_access_approvals',
        help_text="System Owner who authorized this access",
    )
    
    # Access details
    granted_access_level = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Specific access level or role granted"
    )

    legitimate_business_need = models.TextField(
        blank=True,
        null=True,
        help_text="Legitimate business need for this access (as agreed with the System Owner)",
    )

    # Administrator-equivalent access tracking (RHG 4.3)
    is_admin_access = models.BooleanField(
        default=False,
        help_text="This access grants administrator or equivalent privileges in the external system",
    )

    has_separate_admin_account = models.BooleanField(
        default=False,
        help_text="User has separate admin account (e.g., John.Doe_Admin) in the external system",
    )

    admin_account_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Separate admin account username in the external system (e.g., 'John.Doe_Admin')",
    )

    regular_account_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Regular non-admin account username in the external system (e.g., 'John.Doe')",
    )

    is_workstation_login = models.BooleanField(
        default=False,
        help_text="Account used for workstation login (should NOT have domain admin in AD)",
    )

    has_domain_admin = models.BooleanField(
        default=False,
        help_text="Account has domain admin / equivalent rights (should be False for workstation logins)",
    )

    admin_password_storage_location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Where administrator credentials are stored (e.g., 'Financial Controller safe', 'Password vault ref')",
    )

    admin_password_stored_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When administrator credentials were last placed/verified in the secure storage location",
    )

    admin_password_stored_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='admin_password_storage_actions',
        help_text="Who documented storage of administrator credentials",
    )
    
    access_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Username or account name in the system (deprecated - use system_username)"
    )
    
    # System-specific username tracking (for compliance tracking)
    system_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Actual username in the external system (e.g., 'john.doe' in AD, 'jdoe' in Opera Cloud)"
    )

    # Username uniqueness verification metadata
    username_verified_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='username_verifications_performed',
        help_text="User who verified that this external username is unique to the employee"
    )

    username_verified_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date when the username uniqueness was last verified"
    )

    username_verification_artifact = models.FileField(
        upload_to='username_verification_artifacts/',
        blank=True,
        null=True,
        help_text="Attachment (screenshot, export, etc.) showing proof of username uniqueness"
    )

    username_verification_artifact_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link to external evidence (ticket, document, etc.) for username uniqueness verification"
    )
    license_category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="License category/SKU for email subscription mapping (e.g., E1, E3)"
    )
    
    # Generic account detection and documentation
    is_generic_account = models.BooleanField(
        default=False,
        help_text="Flag if this account in the external system is generic (admin, guest, etc.)"
    )
    
    generic_account_remediated = models.BooleanField(
        default=False,
        help_text="Whether generic account has been replaced with unique account in external system"
    )
    
    remediation_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date when generic account was remediated in external system"
    )
    
    remediation_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes on how the generic account was remediated"
    )
    
    remediated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='generic_account_remediations',
        help_text="User who documented the remediation"
    )
    
    temporary_password = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Temporary password (encrypted)"
    )
    
    access_url = models.URLField(
        blank=True,
        null=True,
        help_text="Direct URL for system access"
    )
    
    # Time-based access
    access_start_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When access becomes active (NULL for immediate)"
    )
    
    access_end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When access expires (NULL for no expiration)"
    )
    
    # Review and audit
    last_review_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last access review date"
    )
    
    next_review_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Next scheduled review date"
    )
    
    review_frequency_days = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text="Review frequency in days"
    )
    
    # Security and compliance
    security_clearance_required = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Security clearance level required"
    )
    
    data_access_level = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Data classification level accessed"
    )
    
    compliance_requirements = models.TextField(
        blank=True,
        null=True,
        help_text="Compliance requirements met"
    )
    
    risk_assessment_score = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Risk assessment score (1-10)"
    )
    
    # Notifications and alerts
    notify_user_on_access = models.BooleanField(
        default=True,
        help_text="Send notification to user when access is granted"
    )
    
    notify_manager_on_access = models.BooleanField(
        default=True,
        help_text="Send notification to user's manager when access is granted"
    )
    
    # Additional details
    special_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Special instructions for access"
    )
    
    attachments = models.FileField(
        upload_to='access_requests/',
        blank=True,
        null=True,
        help_text="Supporting documents or screenshots"
    )

    # Soft delete / retention
    is_deleted = models.BooleanField(
        default=False,
        help_text="Record is soft-deleted and should not appear in active queries"
    )

    deleted_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the record was soft-deleted"
    )

    deleted_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_system_accesses_deleted',
        help_text="Who performed the soft-delete"
    )

    deletion_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Reason for soft deletion"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_system_accesses_created'
    )
    updated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_system_accesses_updated'
    )
    
    # Custom manager that excludes soft-deleted records by default
    objects = ActiveAccessManager()
    all_objects = models.Manager()  # For accessing deleted records if needed
    
    class Meta:
        verbose_name = 'User System Access'
        verbose_name_plural = 'User System Accesses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name} → {self.system.name} ({self.status})"
    
    @property
    def is_active_access(self):
        """Check if access is currently active"""
        return self.status == 'Active'
    
    @property
    def is_pending_approval(self):
        """Check if access is pending approval"""
        return self.status == 'Pending'
    
    @property
    def is_expired(self):
        """Check if access has expired"""
        if self.access_end_date:
            return timezone.now() > self.access_end_date
        return False
    
    @property
    def is_accessible_now(self):
        """Check if access is available right now"""
        if not self.is_active_access:
            return False
        
        now = timezone.now()
        
        # Check if access has started
        if self.access_start_date and now < self.access_start_date:
            return False
        
        # Check if access has expired
        if self.access_end_date and now > self.access_end_date:
            return False
        
        return True
    
    @property
    def days_until_expiration(self):
        """Get number of days until access expires"""
        if not self.access_end_date:
            return None
        
        days = (self.access_end_date - timezone.now()).days
        return max(0, days) if days >= 0 else None
    
    @property
    def is_due_for_review(self):
        """Check if access is due for review"""
        if not self.next_review_date:
            return False
        return timezone.now() >= self.next_review_date
    
    @transition(field='status', source='Pending', target='Approved')
    def approve_access(self, approver, comments=None):
        """Approve the access request"""
        if self.status != 'Pending':
            raise ValueError("Only pending requests can be approved")
        # transition handled by FSM decorator if available
        self.status = 'Approved'  # Set status to Approved
        self.approved_by = approver
        self.approval_date = timezone.now()
        if comments:
            self.approval_comments = comments
        self.status_changed_by = approver
        self.status_changed_at = timezone.now()
        # append lifecycle event
        self.lifecycle_timeline = (self.lifecycle_timeline or []) + [{
            'from': 'Pending', 'to': 'Approved', 'by': approver.pk if approver else None,
            'at': timezone.now().isoformat(), 'comments': comments or ''
        }]
        self.save()
        # record immutable audit event
        try:
            AuditEventLog.objects.create(
                event_type='AccessApproved',
                event_data={'access_id': self.pk, 'approved_by': approver.pk if approver else None, 'comments': comments},
                created_by=approver
            )
        except Exception:
            pass
    
    @transition(field='status', source='Pending', target='Rejected')
    def reject_access(self, rejecter, reason):
        """Reject the access request"""
        if self.status != 'Pending':
            raise ValueError("Only pending requests can be rejected")
        self.rejection_reason = reason
        self.status_changed_by = rejecter
        self.status_changed_at = timezone.now()
        self.lifecycle_timeline = (self.lifecycle_timeline or []) + [{
            'from': 'Pending', 'to': 'Rejected', 'by': rejecter.pk if rejecter else None,
            'at': timezone.now().isoformat(), 'reason': reason
        }]
        self.save()
        try:
            AuditEventLog.objects.create(
                event_type='AccessRejected',
                event_data={'access_id': self.pk, 'rejected_by': rejecter.pk if rejecter else None, 'reason': reason},
                created_by=rejecter
            )
        except Exception:
            pass
    
    @transition(field='status', source='Approved', target='Active')
    def activate_access(self):
        """Activate the approved access"""
        if self.status != 'Approved':
            raise ValueError("Only approved access can be activated")
        if not self.access_start_date:
            self.access_start_date = timezone.now()
        self.status_changed_at = timezone.now()
        self.lifecycle_timeline = (self.lifecycle_timeline or []) + [{
            'from': 'Approved', 'to': 'Active', 'at': timezone.now().isoformat()
        }]
        self.save()
        try:
            AuditEventLog.objects.create(
                event_type='AccessActivated',
                event_data={'access_id': self.pk},
                created_by=self.approved_by
            )
        except Exception:
            pass
    
    @transition(field='status', source='Active', target='Suspended')
    def suspend_access(self, reason=None):
        """Suspend active access"""
        if self.status != 'Active':
            raise ValueError("Only active access can be suspended")
        if reason:
            self.approval_comments = f"Suspended: {reason}"
        self.status_changed_at = timezone.now()
        self.lifecycle_timeline = (self.lifecycle_timeline or []) + [{
            'from': 'Active', 'to': 'Suspended', 'at': timezone.now().isoformat(), 'reason': reason
        }]
        self.save()
        try:
            AuditEventLog.objects.create(
                event_type='AccessSuspended',
                event_data={'access_id': self.pk, 'reason': reason},
                created_by=self.approved_by
            )
        except Exception:
            pass
    
    @transition(field='status', source=['Active','Suspended','Approved'], target='Revoked')
    @transition(field='status', source=['Active', 'Suspended', 'Approved'], target='Revoked')
    def revoke_access(self, reason=None):
        """Revoke access"""
        if self.status not in ['Active', 'Suspended', 'Approved']:
            raise ValueError("Cannot revoke access in current status")
        original_status = self.status
        if reason:
            self.approval_comments = f"Revoked: {reason}"
        self.status = 'Revoked'  # Manually set status since django-fsm may not be available
        self.status_changed_at = timezone.now()
        self.lifecycle_timeline = (self.lifecycle_timeline or []) + [{
            'from': original_status, 'to': 'Revoked', 'at': timezone.now().isoformat(), 'reason': reason
        }]
        self.save()
    
    @transition(field='status', source='Active', target='Expired')
    def expire_access(self):
        """Mark access as expired"""
        if self.status != 'Active':
            raise ValueError("Only active access can be expired")
        self.status_changed_at = timezone.now()
        self.lifecycle_timeline = (self.lifecycle_timeline or []) + [{
            'from': 'Active', 'to': 'Expired', 'at': timezone.now().isoformat()
        }]
        self.save()
        try:
            AuditEventLog.objects.create(
                event_type='AccessExpired',
                event_data={'access_id': self.pk},
                created_by=self.approved_by
            )
        except Exception:
            pass
    
    def schedule_review(self, review_date=None, frequency_days=None):
        """Schedule next review"""
        if review_date:
            self.next_review_date = review_date
        if frequency_days:
            self.review_frequency_days = frequency_days
        self.save()
    
    def get_user_full_name(self):
        """Get user's full name"""
        return self.user.full_name if self.user else "Unknown User"
    
    def get_system_name(self):
        """Get system name"""
        return self.system.name if self.system else "Unknown System"
    
    def get_approver_name(self):
        """Get approver's name"""
        return self.approved_by.full_name if self.approved_by else None
    
    def get_requester_name(self):
        """Get requester's name"""
        return self.requested_by.full_name if self.requested_by else None
    
    def can_be_modified(self):
        """Check if access can be modified"""
        return self.status in ['Pending', 'Active', 'Suspended']
    
    def can_be_deleted(self):
        """Check if access record can be deleted"""
        return self.status in ['Pending', 'Rejected', 'Cancelled', 'Expired']
    
    def get_status_color(self):
        """Get Bootstrap color class for status"""
        colors = {
            'Pending': 'warning',
            'Approved': 'info',
            'Active': 'success',
            'Suspended': 'secondary',
            'Revoked': 'danger',
            'Expired': 'dark',
            'Rejected': 'danger',
            'Cancelled': 'secondary'
        }
        return colors.get(self.status, 'secondary')
    
    def get_priority_color(self):
        """Get Bootstrap color class for priority"""
        colors = {
            'Low': 'secondary',
            'Medium': 'primary',
            'High': 'warning',
            'Critical': 'danger'
        }
        return colors.get(self.priority, 'secondary')
    
    @property
    def effective_username(self):
        """Get the effective username (system_username if available, else access_username)"""
        return self.system_username or self.access_username or ''

    @property
    def has_username_verification(self):
        """Return True if any username verification evidence exists"""
        return any([
            self.username_verified_by,
            self.username_verified_date,
            self.username_verification_artifact,
            self.username_verification_artifact_url
        ])

    def get_username_verification_artifact_url(self):
        """Return the best available URL for verification evidence"""
        if self.username_verification_artifact:
            try:
                return self.username_verification_artifact.url
            except ValueError:
                return ''
        return self.username_verification_artifact_url or ''
    
    def check_if_generic_account(self):
        """Check if the system_username is a generic account"""
        if not self.system_username:
            return False
        from .utils import is_generic_username
        return is_generic_username(self.system_username)
    
    def mark_as_generic_if_needed(self):
        """Automatically mark as generic if username matches generic patterns"""
        if self.system_username:
            self.is_generic_account = self.check_if_generic_account()
    
    def clean(self):
        """Validate the model instance"""
        super().clean()
        # Validate system_username is not generic (warning only, not blocking)
        if self.system_username:
            from .utils import is_generic_username
            if is_generic_username(self.system_username) and not self.is_generic_account:
                # Auto-detect and mark as generic
                self.is_generic_account = True
    
    def save(self, *args, **kwargs):
        """Override save to auto-detect generic accounts"""
        # Auto-detect generic accounts before saving
        self.mark_as_generic_if_needed()
        # update status_changed_at if status attribute changed
        try:
            orig = None
            if self.pk:
                orig = UserSystemAccess.objects.filter(pk=self.pk).values('status').first()
            if orig and orig.get('status') != self.status:
                self.status_changed_at = timezone.now()
        except Exception:
            # ignore DB lookup errors at save time
            pass
        super().save(*args, **kwargs)

    def soft_delete(self, deleted_by=None, reason=None):
        """Soft-delete the access record instead of hard delete."""
        self.is_deleted = True
        self.deleted_date = timezone.now()
        if deleted_by:
            self.deleted_by = deleted_by
        if hasattr(self, 'deletion_reason') and reason:
            self.deletion_reason = reason
        self.save()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_date = None
        self.deleted_by = None
        self.save()


class AccessHistory(models.Model):
    """
    AccessHistory model for tracking all access events and audit trails
    """
    
    ACTION_CHOICES = [
        ('Requested', 'Access Requested'),
        ('Approved', 'Access Approved'),
        ('Rejected', 'Access Rejected'),
        ('Activated', 'Access Activated'),
        ('Suspended', 'Access Suspended'),
        ('Revoked', 'Access Revoked'),
        ('Expired', 'Access Expired'),
        ('Reviewed', 'Access Reviewed'),
        ('Modified', 'Access Modified'),
        ('Password Reset', 'Password Reset'),
        ('Login', 'User Login'),
        ('Logout', 'User Logout'),
        ('Failed Login', 'Failed Login Attempt'),
        ('Access Denied', 'Access Denied'),
    ]
    
    user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='access_history',
        help_text="User involved in the access event"
    )
    
    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='access_history',
        help_text="System involved in the access event"
    )
    
    user_system_access = models.ForeignKey(
        'UserSystemAccess',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='history',
        help_text="Related access record (if applicable)"
    )
    
    action = models.CharField(
        max_length=30,
        choices=ACTION_CHOICES,
        help_text="Type of access action"
    )
    
    action_description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the action"
    )
    
    accessed_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the access event occurred"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="IP address from which access was attempted"
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="User agent string from the browser/client"
    )
    
    success = models.BooleanField(
        default=True,
        help_text="Whether the access attempt was successful"
    )
    
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if access failed"
    )
    
    # Additional details
    access_level = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Access level at the time of the event"
    )
    
    session_duration = models.IntegerField(
        blank=True,
        null=True,
        help_text="Session duration in minutes (for login events)"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_history_created'
    )
    
    class Meta:
        verbose_name = 'Access History'
        verbose_name_plural = 'Access History'
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.user.full_name} → {self.system.name} ({self.action})"
    
    @property
    def is_successful(self):
        """Check if the access event was successful"""
        return self.success
    
    @property
    def is_failed(self):
        """Check if the access event failed"""
        return not self.success
    
    def get_user_full_name(self):
        """Get user's full name"""
        return self.user.full_name if self.user else "Unknown User"
    
    def get_system_name(self):
        """Get system name"""
        return self.system.name if self.system else "Unknown System"
    
    def get_action_color(self):
        """Get Bootstrap color class for action"""
        colors = {
            'Requested': 'info',
            'Approved': 'success',
            'Rejected': 'danger',
            'Activated': 'success',
            'Suspended': 'warning',
            'Revoked': 'danger',
            'Expired': 'secondary',
            'Reviewed': 'primary',
            'Modified': 'primary',
            'Password Reset': 'warning',
            'Login': 'success',
            'Logout': 'secondary',
            'Failed Login': 'danger',
            'Access Denied': 'danger'
        }
        return colors.get(self.action, 'secondary')


class AuditEventLog(models.Model):
    """
    Immutable audit event log with hash chaining and optional HMAC signature.
    """

    event_type = models.CharField(max_length=100, help_text="Type of audit event")
    event_data = models.JSONField(default=dict, blank=True, help_text="Event payload")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_events_created')

    previous_event_hash = models.CharField(max_length=128, blank=True, null=True)
    event_hash = models.CharField(max_length=128, blank=True, null=True, editable=False)
    signature = models.CharField(max_length=256, blank=True, null=True, editable=False)
    signature_algorithm = models.CharField(max_length=50, default='HMAC-SHA256')
    is_finalized = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Audit Event Log'
        verbose_name_plural = 'Audit Event Logs'

    def __str__(self):
        return f"{self.event_type} @ {self.created_at.isoformat()}"

    def save(self, *args, **kwargs):
        # prevent modification once finalized
        if self.pk:
            orig = AuditEventLog.objects.filter(pk=self.pk).values('is_finalized').first()
            if orig and orig.get('is_finalized'):
                raise ProtectedError('Cannot modify finalized audit event', self)

        # compute event_hash based on previous_event_hash + event_data + timestamp
        payload = json.dumps(self.event_data, sort_keys=True, default=str)
        seed = (self.previous_event_hash or '') + payload + (self.created_at.isoformat() if self.created_at else '')
        h = hashlib.sha256(seed.encode('utf-8')).hexdigest()
        self.event_hash = h

        # compute optional HMAC signature using settings.AUDIT_LOG_SIGNING_KEY
        key = getattr(settings, 'AUDIT_LOG_SIGNING_KEY', None)
        if key:
            try:
                sig = hmac.new(key.encode('utf-8'), h.encode('utf-8'), hashlib.sha256).hexdigest()
                self.signature = sig
            except Exception:
                self.signature = None

        super().save(*args, **kwargs)

    def verify_integrity(self):
        """Verify this event's hash and signature."""
        payload = json.dumps(self.event_data, sort_keys=True, default=str)
        seed = (self.previous_event_hash or '') + payload + (self.created_at.isoformat() if self.created_at else '')
        expected_hash = hashlib.sha256(seed.encode('utf-8')).hexdigest()
        if expected_hash != self.event_hash:
            return False
        key = getattr(settings, 'AUDIT_LOG_SIGNING_KEY', None)
        if key and self.signature:
            expected_sig = hmac.new(key.encode('utf-8'), expected_hash.encode('utf-8'), hashlib.sha256).hexdigest()
            return hmac.compare_digest(expected_sig, self.signature)
        return True


class QuarterlyAccessReview(models.Model):
    """
    Documents quarterly permission reviews per user/system pairing (RHG 4.5).
    """

    review_quarter = models.CharField(
        max_length=10,
        help_text="Quarter being reviewed (e.g., '2025-Q1')",
    )

    reviewed_user = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.CASCADE,
        related_name='quarterly_access_reviews',
        help_text="Employee whose access was reviewed",
    )

    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='quarterly_access_reviews',
        help_text="External system that was reviewed",
    )

    user_system_access = models.ForeignKey(
        'UserSystemAccess',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quarterly_reviews',
        help_text="Link to the access assignment that was reviewed (optional)",
    )

    reviewed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='quarterly_reviews_conducted',
        help_text="IT reviewer who conducted the quarterly review",
    )

    review_date = models.DateTimeField(
        help_text="Date and time the quarterly review was conducted",
    )

    approved_permissions = models.TextField(
        help_text="Approved permissions/roles on record in this system",
    )

    actual_permissions_in_external_system = models.TextField(
        help_text="Permissions observed in the external system during the review",
    )

    matches_approved = models.BooleanField(
        default=False,
        help_text="Do the actual external-system permissions match the approved permissions?",
    )

    discrepancies = models.TextField(
        blank=True,
        null=True,
        help_text="Describe any mismatches or required remediation actions",
    )

    system_owner = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quarterly_reviews_confirmed',
        help_text="System Owner who confirms the review results",
    )

    system_owner_confirmed = models.BooleanField(
        default=False,
        help_text="System Owner has confirmed the quarterly review outcome",
    )

    system_owner_confirmed_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date/time the System Owner confirmed the review",
    )

    system_owner_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes or confirmation evidence from the System Owner",
    )

    review_completed = models.BooleanField(
        default=False,
        help_text="Check when review tasks and follow-ups have been completed",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-review_date']
        verbose_name = "Quarterly Access Review"
        verbose_name_plural = "Quarterly Access Reviews"
        indexes = [
            models.Index(fields=['review_quarter']),
            models.Index(fields=['system']),
            models.Index(fields=['reviewed_user']),
        ]

    def __str__(self):
        return f"{self.review_quarter} – {self.reviewed_user.full_name} @ {self.system.name}"

    @property
    def quarter_label(self):
        return self.review_quarter


class PermissionChangeDocumentation(models.Model):
    """
    Captures evidence that permission changes were reviewed and approved (RHG 4.5).
    """

    user_system_access = models.ForeignKey(
        'UserSystemAccess',
        on_delete=models.CASCADE,
        related_name='permission_change_logs',
        help_text="Access assignment that was modified in the external system",
    )

    old_permissions = models.TextField(
        help_text="Documented permissions before the change",
    )

    new_permissions = models.TextField(
        help_text="Actual permissions applied in the external system after the change",
    )

    changed_in_external_system_date = models.DateTimeField(
        help_text="When the change occurred in the external system",
    )

    documented_in_this_system_date = models.DateTimeField(
        auto_now_add=True,
        help_text="When this change was logged for audit evidence",
    )

    has_approval = models.BooleanField(
        default=False,
        help_text="Was the change approved through change management?",
    )

    approval_reference = models.ForeignKey(
        'change_management.AccountChangeRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='permission_change_records',
        help_text="Reference to the associated change request (if applicable)",
    )

    documented_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='permission_changes_documented',
        help_text="Person who documented this permission change",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional context, evidence links, or remediation notes",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_in_external_system_date', '-created_at']
        verbose_name = "Permission Change Documentation"
        verbose_name_plural = "Permission Change Documentation"
        indexes = [
            models.Index(fields=['changed_in_external_system_date']),
        ]

    def __str__(self):
        access = self.user_system_access
        user_label = access.user.full_name if access and access.user else "Unknown user"
        system_label = access.system.name if access and access.system else "Unknown system"
        return f"{user_label} – {system_label} permissions updated"


class AccessInstance(models.Model):
    """Allows multiple access instances per user-system pair for historical tracking."""

    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='access_instances')
    system = models.ForeignKey('systems.System', on_delete=models.CASCADE, related_name='access_instances')
    instance_number = models.IntegerField(help_text='Incremental instance number per user-system pair')
    user_system_access = models.ForeignKey('UserSystemAccess', on_delete=models.CASCADE, related_name='instances', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='access_instances_created')
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Access Instance'
        verbose_name_plural = 'Access Instances'
        indexes = [models.Index(fields=['user', 'system', 'instance_number'])]

    def __str__(self):
        return f"Instance {self.instance_number} for {self.user.full_name} @ {self.system.name}"


class AccessVersion(models.Model):
    """Versioned record of privilege/permission sets for an AccessInstance."""

    access_instance = models.ForeignKey('AccessInstance', on_delete=models.CASCADE, related_name='versions')
    version_number = models.IntegerField(help_text='Sequential version number')
    access_type = models.CharField(max_length=50, blank=True, null=True)
    granted_access_level = models.CharField(max_length=200, blank=True, null=True)
    permissions_added = models.JSONField(default=list, blank=True)
    permissions_removed = models.JSONField(default=list, blank=True)
    is_privilege_escalation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='access_versions_created')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Access Version'
        verbose_name_plural = 'Access Versions'
        indexes = [models.Index(fields=['access_instance', 'version_number'])]

    def __str__(self):
        return f"v{self.version_number} for {self.access_instance}"

    def detect_escalation(self, previous_version=None):
        """Simple escalation detection comparing added permissions or access level changes."""
        if not previous_version:
            self.is_privilege_escalation = False
            return
        # basic heuristic: if new access_type is more privileged or permissions_added not empty
        if self.access_type != previous_version.access_type:
            self.is_privilege_escalation = True
        elif self.permissions_added:
            self.is_privilege_escalation = True
        else:
            self.is_privilege_escalation = False
        self.save()


class EvidenceArtifact(models.Model):
    """Centralized evidence repository for proofs, screenshots, tickets, attestations."""

    ARTIFACT_TYPE_CHOICES = [
        ('screenshot', 'Screenshot'),
        ('email', 'Email'),
        ('ticket', 'Ticket'),
        ('document', 'Document'),
        ('attestation', 'Attestation'),
        ('other', 'Other'),
    ]

    artifact_type = models.CharField(max_length=30, choices=ARTIFACT_TYPE_CHOICES, default='other')
    file_artifact = models.FileField(upload_to='evidence_artifacts/', blank=True, null=True)
    file_hash = models.CharField(max_length=128, blank=True, null=True, help_text='SHA256 of file')
    file_size_bytes = models.BigIntegerField(blank=True, null=True)
    file_format = models.CharField(max_length=50, blank=True, null=True)

    user_system_access = models.ForeignKey('UserSystemAccess', on_delete=models.CASCADE, related_name='evidence_artifacts', null=True, blank=True)
    access_instance = models.ForeignKey('AccessInstance', on_delete=models.CASCADE, related_name='evidence_artifacts', null=True, blank=True)
    access_version = models.ForeignKey('AccessVersion', on_delete=models.CASCADE, related_name='evidence_artifacts', null=True, blank=True)
    audit_event = models.ForeignKey('AuditEventLog', on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence_artifacts')

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='evidence_artifacts_created')
    is_finalized = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Evidence Artifact'
        verbose_name_plural = 'Evidence Artifacts'

    def __str__(self):
        return f"{self.artifact_type} ({self.pk})"

    def save(self, *args, **kwargs):
        # compute file hash if file present and not yet set
        if self.file_artifact and not self.file_hash:
            try:
                hasher = hashlib.sha256()
                for chunk in self.file_artifact.chunks():
                    hasher.update(chunk)
                self.file_hash = hasher.hexdigest()
                try:
                    self.file_size_bytes = self.file_artifact.size
                except Exception:
                    self.file_size_bytes = None
            except Exception:
                pass
        if self.pk:
            orig = EvidenceArtifact.objects.filter(pk=self.pk).values('is_finalized').first()
            if orig and orig.get('is_finalized'):
                raise ProtectedError('Cannot modify finalized artifact', self)
        super().save(*args, **kwargs)

    def verify_file_integrity(self):
        if not self.file_artifact or not self.file_hash:
            return False
        try:
            hasher = hashlib.sha256()
            for chunk in self.file_artifact.chunks():
                hasher.update(chunk)
            return hasher.hexdigest() == self.file_hash
        except Exception:
            return False


class ApprovalRule(models.Model):
    """Defines approval requirements and segregation rules per system/access type."""

    system = models.ForeignKey('systems.System', on_delete=models.CASCADE, related_name='approval_rules')
    access_type = models.CharField(max_length=50, blank=True, null=True)
    approvers_required = models.IntegerField(default=1)
    approver_roles = models.JSONField(default=list, blank=True, help_text='Roles eligible to approve')
    conflict_of_interest_rules = models.JSONField(default=dict, blank=True, help_text='COI rules like cannot_approve_self')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Approval Rule'
        verbose_name_plural = 'Approval Rules'

    def __str__(self):
        return f"Rule for {self.system.name} ({self.access_type or 'any'})"


class ApprovalWorkflow(models.Model):
    """Tracks approval workflows for a UserSystemAccess."""

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Escalated', 'Escalated'),
        ('Rejected', 'Rejected'),
    ]

    user_system_access = models.ForeignKey('UserSystemAccess', on_delete=models.CASCADE, related_name='approval_workflows')
    rule = models.ForeignKey('ApprovalRule', on_delete=models.SET_NULL, null=True, blank=True, related_name='workflows')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approval_workflows_created')

    class Meta:
        verbose_name = 'Approval Workflow'
        verbose_name_plural = 'Approval Workflows'

    def __str__(self):
        return f"Workflow {self.pk} for access {self.user_system_access.pk}"

    def has_conflict_of_interest(self, candidate_user):
        """Check simple COI rules: cannot_approve_self, cannot_approve_direct_reports"""
        coi = self.rule.conflict_of_interest_rules if self.rule and self.rule.conflict_of_interest_rules else {}
        if coi.get('cannot_approve_self', True) and candidate_user == self.user_system_access.user:
            return True
        # other COI checks would require org hierarchy lookup; return False if unknown
        return False


class ApprovalStep(models.Model):
    workflow = models.ForeignKey('ApprovalWorkflow', on_delete=models.CASCADE, related_name='steps')
    step_number = models.IntegerField()
    role_required = models.CharField(max_length=100, blank=True, null=True)
    approver = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approval_steps')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['step_number']
        verbose_name = 'Approval Step'
        verbose_name_plural = 'Approval Steps'

    def __str__(self):
        return f"Step {self.step_number} for workflow {self.workflow.pk}"


class Approval(models.Model):
    step = models.ForeignKey('ApprovalStep', on_delete=models.CASCADE, related_name='approvals')
    approver = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='approvals_made')
    approved = models.BooleanField(null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Approval'
        verbose_name_plural = 'Approvals'

    def __str__(self):
        return f"Approval by {self.approver} on step {self.step.step_number}"

    def save(self, *args, **kwargs):
        if self.approved and not self.approved_at:
            self.approved_at = timezone.now()
        super().save(*args, **kwargs)


class Attestation(models.Model):
    """Records formal attestations with optional digital signature."""

    SIGNATURE_CHOICES = [
        ('digital_certificate', 'Digital Certificate'),
        ('electronic_signature', 'Electronic Signature'),
        ('hmac', 'HMAC'),
        ('session', 'Authenticated Session')
    ]

    user_system_access = models.ForeignKey('UserSystemAccess', on_delete=models.CASCADE, related_name='attestations')
    attested_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='attestations_made')
    statement = models.TextField(help_text='Attestation statement text')
    attestation_date = models.DateTimeField(auto_now_add=True)
    signature_method = models.CharField(max_length=50, choices=SIGNATURE_CHOICES, default='session')
    signature = models.TextField(blank=True, null=True)
    signature_algorithm = models.CharField(max_length=50, blank=True, null=True)
    is_finalized = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Attestation'
        verbose_name_plural = 'Attestations'

    def __str__(self):
        return f"Attestation {self.pk} by {self.attested_by} on {self.attestation_date}"

    def finalize(self, signing_key=None):
        """Finalize attestation: compute HMAC signature if signing_key provided and mark immutable."""
        if self.is_finalized:
            return
        payload = f"{self.user_system_access_id}|{self.attested_by_id}|{self.attestation_date.isoformat()}|{self.statement}"
        if signing_key and self.signature_method == 'hmac':
            try:
                self.signature = hmac.new(signing_key.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
                self.signature_algorithm = 'HMAC-SHA256'
            except Exception:
                self.signature = None
        self.is_finalized = True
        self.save()

    def save(self, *args, **kwargs):
        if self.pk:
            orig = Attestation.objects.filter(pk=self.pk).values('is_finalized').first()
            if orig and orig.get('is_finalized'):
                raise ProtectedError('Cannot modify finalized attestation', self)
        super().save(*args, **kwargs)


class AccessReviewSchedule(models.Model):
    """Schedules and tracks regular access reviews with escalation logic."""

    user_system_access = models.ForeignKey('UserSystemAccess', on_delete=models.CASCADE, related_name='review_schedules')
    review_frequency_days = models.IntegerField(default=90, help_text='Review interval in days')
    last_review_date = models.DateTimeField(blank=True, null=True)
    next_review_date = models.DateTimeField()
    reviewed_by = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='review_schedules_reviewed')
    review_completed = models.BooleanField(default=False)
    is_escalated = models.BooleanField(default=False)
    escalation_date = models.DateTimeField(blank=True, null=True)
    escalated_to = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['next_review_date']
        verbose_name = 'Access Review Schedule'
        verbose_name_plural = 'Access Review Schedules'

    def __str__(self):
        return f"Review {self.user_system_access} due {self.next_review_date}"


class QuarterlyActiveUserReview(models.Model):
    """
    Documents quarterly verification that external systems only contain approved users.
    """

    review_quarter = models.CharField(
        max_length=10,
        help_text="Quarter reviewed (e.g., '2025-Q1')",
    )

    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='quarterly_active_user_reviews',
    )

    reviewed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='active_user_reviews_conducted',
    )

    review_date = models.DateTimeField()

    total_active_users_in_external_system = models.IntegerField(
        help_text="Total active accounts discovered in the external system.",
    )

    approved_users_count = models.IntegerField(
        help_text="Count of accounts that matched approved access records.",
    )

    unapproved_users_count = models.IntegerField(
        help_text="Count of accounts found without an approved record.",
    )

    unapproved_users_list = models.TextField(
        blank=True,
        null=True,
        help_text="Details of unapproved accounts found (usernames, notes).",
    )

    discrepancies = models.TextField(
        blank=True,
        null=True,
        help_text="Document remediation steps or issues discovered.",
    )

    review_completed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-review_date']
        verbose_name = "Quarterly Active User Review"
        verbose_name_plural = "Quarterly Active User Reviews"
        indexes = [
            models.Index(fields=['review_quarter']),
            models.Index(fields=['system']),
        ]

    def __str__(self):
        return f"{self.review_quarter} – {self.system.name} active user review"


class MonthlyObsoleteAccountReview(models.Model):
    """
    Monthly documentation of obsolete account detection and remediation.
    """

    review_month = models.CharField(
        max_length=10,
        help_text="Month reviewed (e.g., '2025-01')",
    )

    reviewed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='monthly_obsolete_reviews_conducted',
    )

    review_date = models.DateTimeField()

    obsolete_accounts_identified = models.JSONField(
        default=list,
        blank=True,
        help_text="List or dict describing obsolete accounts identified.",
    )

    accounts_deactivated_in_external_systems = models.IntegerField(default=0)

    accounts_pending_deactivation = models.IntegerField(default=0)

    review_completed = models.BooleanField(default=False)

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional context, remediation steps, system owner confirmations.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-review_date']
        verbose_name = "Monthly Obsolete Account Review"
        verbose_name_plural = "Monthly Obsolete Account Reviews"
        indexes = [
            models.Index(fields=['review_month']),
        ]

    def __str__(self):
        return f"{self.review_month} – Obsolete account review"


class AccessRemovalDocumentation(models.Model):
    """
    Evidence that access was removed from external systems when no longer needed.
    """

    user_system_access = models.ForeignKey(
        'UserSystemAccess',
        on_delete=models.CASCADE,
        related_name='removal_documentation',
    )

    removed_from_external_system_date = models.DateTimeField(
        help_text="When the external-system account was deactivated or removed.",
    )

    removed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        related_name='access_removals_performed',
    )

    removal_reason = models.TextField(
        help_text="Reason for removal (termination, role change, etc.)",
    )

    verified_removal = models.BooleanField(
        default=False,
        help_text="Indicates independent verification that removal is complete.",
    )

    verified_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_removals_verified',
    )

    verified_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When verification occurred.",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Supporting evidence links, ticket numbers, screenshots, etc.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-removed_from_external_system_date']
        verbose_name = "Access Removal Documentation"
        verbose_name_plural = "Access Removal Documentation"

    def __str__(self):
        access = self.user_system_access
        user_label = access.user.full_name if access and access.user else "Unknown User"
        system_label = access.system.name if access and access.system else "Unknown System"
        return f"{user_label} – {system_label} removal"
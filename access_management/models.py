from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


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
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Current status of the access request"
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
    
    # Access details
    granted_access_level = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Specific access level or role granted"
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
    
    class Meta:
        verbose_name = 'User System Access'
        verbose_name_plural = 'User System Accesses'
        unique_together = ['user', 'system']
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
    
    def approve_access(self, approver, comments=None):
        """Approve the access request"""
        if self.status != 'Pending':
            raise ValueError("Only pending requests can be approved")
        
        self.status = 'Approved'
        self.approved_by = approver
        self.approval_date = timezone.now()
        if comments:
            self.approval_comments = comments
        self.save()
    
    def reject_access(self, rejecter, reason):
        """Reject the access request"""
        if self.status != 'Pending':
            raise ValueError("Only pending requests can be rejected")
        
        self.status = 'Rejected'
        self.rejection_reason = reason
        self.save()
    
    def activate_access(self):
        """Activate the approved access"""
        if self.status != 'Approved':
            raise ValueError("Only approved access can be activated")
        
        self.status = 'Active'
        if not self.access_start_date:
            self.access_start_date = timezone.now()
        self.save()
    
    def suspend_access(self, reason=None):
        """Suspend active access"""
        if self.status != 'Active':
            raise ValueError("Only active access can be suspended")
        
        self.status = 'Suspended'
        if reason:
            self.approval_comments = f"Suspended: {reason}"
        self.save()
    
    def revoke_access(self, reason=None):
        """Revoke access"""
        if self.status not in ['Active', 'Suspended', 'Approved']:
            raise ValueError("Cannot revoke access in current status")
        
        self.status = 'Revoked'
        if reason:
            self.approval_comments = f"Revoked: {reason}"
        self.save()
    
    def expire_access(self):
        """Mark access as expired"""
        if self.status != 'Active':
            raise ValueError("Only active access can be expired")
        
        self.status = 'Expired'
        self.save()
    
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
        super().save(*args, **kwargs)


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

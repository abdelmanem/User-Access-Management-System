from django.db import models


class AccountChangeRequest(models.Model):
    """
    Documents user account changes in external systems (RHG 4.4).

    This model is used to evidence that:
    - All account creations/modifications/deletions are requested and approved
    - System Owners authorize user-id establishment
    - Legitimate business need is captured for each change
    """

    CHANGE_TYPE_CREATE = "Create"
    CHANGE_TYPE_MODIFY = "Modify"
    CHANGE_TYPE_DELETE = "Delete"
    CHANGE_TYPE_SUSPEND = "Suspend"

    CHANGE_TYPE_CHOICES = [
        (CHANGE_TYPE_CREATE, "Create New Account in External System"),
        (CHANGE_TYPE_MODIFY, "Modify Existing Account in External System"),
        (CHANGE_TYPE_DELETE, "Delete Account in External System"),
        (CHANGE_TYPE_SUSPEND, "Suspend Account in External System"),
    ]

    STATUS_PENDING = "Pending"
    STATUS_APPROVED = "Approved"
    STATUS_REJECTED = "Rejected"
    STATUS_COMPLETED = "Completed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Approval"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_COMPLETED, "Completed in External System"),
    ]

    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPE_CHOICES,
        help_text="Type of account change requested in the external system",
    )

    user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="account_change_requests",
        help_text="Employee whose account is being created/changed/deleted (if known)",
    )

    user_full_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Snapshot of user's full name at time of request creation (for audit trail if user is deleted)",
    )

    user_username = models.CharField(
        max_length=150,
        blank=True,
        default="",
        help_text="Snapshot of user's username at time of request creation (for audit trail if user is deleted)",
    )

    system = models.ForeignKey(
        "systems.System",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="account_change_requests",
        help_text="External system where the account change will occur (AD, PMS, POS, etc.). Null for corporate-level changes like user deletion.",
    )

    requested_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        related_name="account_change_requests_made",
        help_text="Person requesting the account change",
    )

    business_justification = models.TextField(
        help_text="Legitimate business need for this account change (RHG 4.4 requirement)",
    )

    system_owner = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_owner_approvals",
        help_text="System Owner who must authorize the account change",
    )

    system_owner_approved = models.BooleanField(
        default=False,
        help_text="System Owner has approved this change request",
    )

    system_owner_approval_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the System Owner approved this change request",
    )

    system_owner_approval_notes = models.TextField(
        null=True,
        blank=True,
        help_text="Notes from the System Owner regarding this change",
    )

    it_approval = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="it_approved_account_changes",
        help_text="IT approver for this change request (if applicable)",
    )

    it_approval_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When IT approved this change request",
    )

    # Rejection tracking (NEW)
    system_owner_rejected = models.BooleanField(
        default=False,
        help_text="System Owner has rejected this change request",
    )

    system_owner_rejection_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the System Owner rejected this change request",
    )

    system_owner_rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for System Owner rejection",
    )

    system_owner_rejected_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_owner_rejections",
        help_text="User who rejected as System Owner",
    )

    it_rejected = models.BooleanField(
        default=False,
        help_text="IT has rejected this change request",
    )

    it_rejection_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When IT rejected this change request",
    )

    it_rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason for IT rejection",
    )

    it_rejected_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="it_rejections",
        help_text="User who rejected as IT approver",
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text="Workflow status of the change request",
    )

    completed_in_external_system = models.BooleanField(
        default=False,
        help_text="True when the change has been implemented in the external system",
    )

    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the change was completed in the external system",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True, help_text="Last updated timestamp")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Account Change Request"
        verbose_name_plural = "Account Change Requests"
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['system', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self) -> str:
        if self.user:
            user_label = self.user.full_name
        elif self.user_full_name:
            user_label = self.user_full_name
        else:
            user_label = "Unassigned user"
        system_name = self.system.name if self.system else "Corporate"
        return f"{self.change_type} – {user_label} @ {system_name} [{self.status}]"

    def is_rejected(self) -> bool:
        """Check if request has been rejected by anyone."""
        return self.system_owner_rejected or self.it_rejected

    def is_approved(self) -> bool:
        """Check if request has been fully approved by all required approvers."""
        return self.system_owner_approved and (not self.it_approval or self.status == self.STATUS_APPROVED)


class ChangeAuditLog(models.Model):
    """
    Audit log for tracking all changes to AccountChangeRequest records.
    
    Provides full traceability of who made what changes and when.
    """
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('modified', 'Modified'),
        ('viewed', 'Viewed'),
        ('exported', 'Exported'),
    ]
    
    change_request = models.ForeignKey(
        AccountChangeRequest,
        on_delete=models.CASCADE,
        related_name='audit_logs',
        help_text="Reference to the change request"
    )
    
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Action performed"
    )
    
    performed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='change_audit_logs',
        help_text="User who performed the action"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action occurred"
    )
    
    old_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Old field values (for modifications)"
    )
    
    new_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="New field values (for modifications)"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional context or notes"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the client"
    )
    
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        help_text="User-Agent header (for web requests)"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Change Audit Log'
        verbose_name_plural = 'Change Audit Logs'
        indexes = [
            models.Index(fields=['change_request', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.change_request_id} - {self.action} by {self.performed_by}"



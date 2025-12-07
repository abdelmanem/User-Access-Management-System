from django.db import models
from django.utils import timezone


ACCOUNT_TYPE_CHOICES = [
    ('Database', 'Database Default Account'),
    ('Workstation', 'Workstation Image / Local Account'),
    ('Server', 'Server / ILO Default Account'),
    ('Application', 'Application / PMS Default Account'),
    ('Network Device', 'Network Device (Switch/Firewall) Account'),
    ('Printer', 'Printer / Peripheral Default Account'),
    ('Other', 'Other Default Account'),
]

STATUS_CHOICES = [
    ('Pending', 'Pending Reset/Removal'),
    ('Active - Password Changed', 'Active - Password Changed in External System'),
    ('Removed', 'Removed from External System'),
    ('Not Applicable', 'Not Applicable (Hosted / No Access)'),
    ('In Review', 'Under Review / Follow-up Needed'),
]

ACTION_TYPE_CHOICES = [
    ('password_reset', 'Password Reset / Changed in External System'),
    ('removal', 'Removed / Disabled in External System'),
    ('mark_not_applicable', 'Marked Not Applicable'),
    ('installation_checklist', 'Installation Checklist Completed'),
    ('verification', 'Verification / Evidence Capture'),
    ('note', 'Documentation / Notes Update'),
]


class DefaultAccountTemplate(models.Model):
    """
    Defines reusable templates of known default accounts per system.
    Used when new systems are created so that baseline accounts are tracked automatically.
    Templates can be linked to multiple specific systems or set as global (applies to all).
    """

    systems = models.ManyToManyField(
        'systems.System',
        blank=True,
        related_name='default_account_templates',
        help_text="Specific systems this template applies to. Leave empty and enable 'Applies to all' for global templates.",
    )

    account_name = models.CharField(
        max_length=200,
        help_text="Default account name in the external system (e.g., admin, supervisor).",
    )

    account_type = models.CharField(
        max_length=25,
        choices=ACCOUNT_TYPE_CHOICES,
        default='Application',
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text="Context on where this default account is normally seen.",
    )

    removal_required = models.BooleanField(
        default=True,
        help_text="If true, remediation expects removal once system is installed.",
    )

    applies_to_all = models.BooleanField(
        default=False,
        help_text="When enabled this template is instantiated for every new system automatically. Use with no systems selected for global templates.",
    )

    rhg_special_account = models.BooleanField(
        default=False,
        help_text="Flag for RHG-specific accounts (e.g., michael.brandt).",
    )

    default_status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Initial status assigned when this template is applied.",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes/checklist instructions.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Default Account Template"
        verbose_name_plural = "Default Account Templates"
        ordering = ['account_name']
        # Note: unique_together removed since we now use ManyToMany
        # Uniqueness is enforced at the application level if needed

    def __str__(self) -> str:
        system_count = self.systems.count()
        if system_count == 0:
            target = 'All Systems' if self.applies_to_all else 'No Systems'
        elif system_count == 1:
            target = self.systems.first().name
        else:
            target = f"{system_count} Systems"
        return f"{self.account_name} ({target})"


class DefaultAccountQuerySet(models.QuerySet):
    """Custom queryset helpers for dashboard level aggregations."""

    def requiring_attention(self):
        """Default accounts that still need remediation evidence."""
        return self.filter(
            models.Q(status='Pending')
            | models.Q(status='In Review')
            | models.Q(removal_required=True, removed_from_external_system=False)
            | models.Q(
                status='Active - Password Changed',
                password_changed_in_external_system=False,
            )
        )

    def rhg_special(self):
        return self.filter(is_rhg_special_account=True)


class DefaultAccount(models.Model):
    """
    Tracks each default account across external systems (PCI/RHG 4.7 evidence).
    """

    template = models.ForeignKey(
        DefaultAccountTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='instantiated_accounts',
    )

    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='default_accounts',
        help_text="External system this default account belongs to.",
    )

    account_name = models.CharField(
        max_length=200,
        help_text="Default account name (e.g., 'admin', 'supervisor', 'Opera').",
    )

    account_type = models.CharField(
        max_length=25,
        choices=ACCOUNT_TYPE_CHOICES,
        default='Application',
    )

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='Pending',
        help_text="Current remediation status for this default account.",
    )

    password_changed_in_external_system = models.BooleanField(
        default=False,
        help_text="Password was changed in the external system per RHG policy.",
    )

    password_changed_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date password was changed in the external system.",
    )

    password_changed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_account_password_changes',
    )

    password_change_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ticket/screenshot/reference ID for password change evidence.",
    )

    password_change_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes describing how password change was executed.",
    )

    removal_required = models.BooleanField(
        default=True,
        help_text="Whether this default account must ultimately be removed.",
    )

    removed_from_external_system = models.BooleanField(
        default=False,
        help_text="Account was fully removed from the external system.",
    )

    removal_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date removal was completed.",
    )

    removal_confirmed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_account_removal_confirmations',
    )

    removal_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ticket/screenshot reference for removal evidence.",
    )

    remediation_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Narrative on how this default account was handled/remediated.",
    )

    installation_checklist_completed = models.BooleanField(
        default=False,
        help_text="Installation checklist completed for this account/system.",
    )

    installation_checklist_completed_date = models.DateTimeField(
        blank=True,
        null=True,
    )

    installation_documented_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_account_installations',
    )

    installation_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes captured during new system installation.",
    )

    last_verified_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last time evidence was verified.",
    )

    last_verified_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_account_verifications',
    )

    verification_artifact = models.CharField(
        max_length=255,
        blank=True,
        help_text="Link or identifier for verification artifact (screenshot/ticket).",
    )

    hosted_not_applicable_reason = models.CharField(
        max_length=255,
        blank=True,
        help_text="Document why the account is not applicable (e.g., hosted solution).",
    )

    is_rhg_special_account = models.BooleanField(
        default=False,
        help_text="Tracks RHG-specific legacy accounts (e.g., michael.brandt).",
    )

    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_accounts_created',
    )

    updated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_accounts_updated',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = DefaultAccountQuerySet.as_manager()

    class Meta:
        verbose_name = "Default Account"
        verbose_name_plural = "Default Accounts"
        unique_together = [('system', 'account_name')]
        ordering = ['system__name', 'account_name']

    def __str__(self) -> str:
        return f"{self.account_name} ({self.system.name})"

    @property
    def requires_follow_up(self) -> bool:
        """Determine if more documentation is required for this default account."""
        if self.status in ['Pending', 'In Review']:
            return True
        if self.removal_required and not self.removed_from_external_system:
            return True
        if self.status == 'Active - Password Changed' and not self.password_changed_in_external_system:
            return True
        return False

    @property
    def compliance_label(self) -> str:
        """Bootstrap-friendly label type for quick UI badges."""
        mapping = {
            'Pending': 'warning',
            'In Review': 'warning',
            'Active - Password Changed': 'info' if self.password_changed_in_external_system else 'warning',
            'Removed': 'success',
            'Not Applicable': 'secondary',
        }
        return mapping.get(self.status, 'secondary')

    def mark_not_applicable(self, reason: str, user=None):
        """Helper to mark the account as N/A."""
        self.status = 'Not Applicable'
        self.hosted_not_applicable_reason = reason or self.hosted_not_applicable_reason
        self.removal_required = False
        self.updated_by = user or self.updated_by
        self.updated_at = timezone.now()
        self.save(update_fields=[
            'status',
            'hosted_not_applicable_reason',
            'removal_required',
            'updated_by',
            'updated_at',
        ])


class DefaultAccountAction(models.Model):
    """
    Audit log of remediation steps taken against a DefaultAccount instance.
    """

    default_account = models.ForeignKey(
        DefaultAccount,
        on_delete=models.CASCADE,
        related_name='actions',
    )

    action_type = models.CharField(
        max_length=40,
        choices=ACTION_TYPE_CHOICES,
    )

    action_date = models.DateTimeField(
        default=timezone.now,
        help_text="When this action occurred in the external system.",
    )

    performed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='default_account_actions',
    )

    evidence_reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Ticket ID / screenshot file / vendor confirmation reference.",
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Narrative documentation of what was performed.",
    )

    status_applied = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        blank=True,
        help_text="Optional override to set the parent record status directly.",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Default Account Action"
        verbose_name_plural = "Default Account Actions"
        ordering = ['-action_date']

    def __str__(self) -> str:
        return f"{self.default_account.account_name} - {self.get_action_type_display()}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.apply_to_account()

    def apply_to_account(self):
        """Apply action side-effects to parent DefaultAccount."""
        account = self.default_account
        now = timezone.now()
        updates = {'updated_at': now}
        if self.performed_by:
            updates['updated_by'] = self.performed_by

        if self.action_type == 'password_reset':
            account.password_changed_in_external_system = True
            account.password_changed_date = self.action_date
            account.password_changed_by = self.performed_by
            account.password_change_reference = self.evidence_reference or account.password_change_reference
            account.password_change_notes = self.notes or account.password_change_notes
            account.status = self.status_applied or 'Active - Password Changed'
            updates.update({
                'password_changed_in_external_system': True,
                'password_changed_date': account.password_changed_date,
                'password_changed_by': account.password_changed_by,
                'password_change_reference': account.password_change_reference,
                'password_change_notes': account.password_change_notes,
                'status': account.status,
            })
        elif self.action_type == 'removal':
            account.removed_from_external_system = True
            account.removal_date = self.action_date
            account.removal_confirmed_by = self.performed_by
            account.removal_reference = self.evidence_reference or account.removal_reference
            account.status = self.status_applied or 'Removed'
            updates.update({
                'removed_from_external_system': True,
                'removal_date': account.removal_date,
                'removal_confirmed_by': account.removal_confirmed_by,
                'removal_reference': account.removal_reference,
                'status': account.status,
            })
        elif self.action_type == 'mark_not_applicable':
            account.status = 'Not Applicable'
            account.removal_required = False
            account.hosted_not_applicable_reason = self.notes or account.hosted_not_applicable_reason
            updates.update({
                'status': 'Not Applicable',
                'removal_required': False,
                'hosted_not_applicable_reason': account.hosted_not_applicable_reason,
            })
        elif self.action_type == 'installation_checklist':
            account.installation_checklist_completed = True
            account.installation_checklist_completed_date = self.action_date
            account.installation_documented_by = self.performed_by
            account.installation_notes = self.notes or account.installation_notes
            account.status = self.status_applied or account.status
            updates.update({
                'installation_checklist_completed': True,
                'installation_checklist_completed_date': account.installation_checklist_completed_date,
                'installation_documented_by': account.installation_documented_by,
                'installation_notes': account.installation_notes,
                'status': account.status,
            })
        elif self.action_type == 'verification':
            account.last_verified_date = self.action_date
            account.last_verified_by = self.performed_by
            account.verification_artifact = self.evidence_reference or account.verification_artifact
            account.status = self.status_applied or account.status
            updates.update({
                'last_verified_date': account.last_verified_date,
                'last_verified_by': account.last_verified_by,
                'verification_artifact': account.verification_artifact,
                'status': account.status,
            })
        else:
            # Documentation updates only
            if self.notes:
                existing_notes = account.remediation_notes or ""
                account.remediation_notes = f"{existing_notes}\n{self.notes}".strip()
                updates['remediation_notes'] = account.remediation_notes
            if self.status_applied:
                account.status = self.status_applied
                updates['status'] = account.status

        account.updated_at = now
        for field, value in updates.items():
            setattr(account, field, value)
        account.save(update_fields=list(updates.keys()))

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


class ServiceAccount(models.Model):
    """
    Service Account model for tracking service/application accounts in external systems
    Tracks account details, password compliance, and ownership for audit compliance
    """
    
    ACCOUNT_TYPE_CHOICES = [
        ('Service', 'Service/Application Account'),
        ('Interface', 'Interface Account'),
        ('Backup', 'Backup Account'),
        ('Privileged', 'Privileged/Admin Account'),
    ]
    
    account_name = models.CharField(
        max_length=200,
        help_text="Account name in the external system (e.g., 'svc_backup' in AD)"
    )
    
    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='service_accounts',
        help_text="Which external system (AD, Opera Cloud, etc.)"
    )
    
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        default='Service',
        help_text="Type of service account"
    )
    
    purpose = models.TextField(
        help_text="What it's for - documented purpose of the service account"
    )
    
    owner = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_service_accounts',
        help_text="Account owner/manager"
    )
    
    password_last_changed = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Last password change date in the external system"
    )
    
    password_expires_on = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Password expiration date in the external system"
    )
    
    password_complies_with_policy = models.BooleanField(
        default=False,
        help_text="Documented compliance with RHG password policy in external system"
    )
    
    password_policy_verified_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date when password policy compliance was verified"
    )
    
    password_policy_verified_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='password_policy_verifications',
        help_text="User who verified password policy compliance"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this service account is currently active"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the service account"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_accounts_created'
    )
    updated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_accounts_updated'
    )
    
    class Meta:
        verbose_name = 'Service Account'
        verbose_name_plural = 'Service Accounts'
        unique_together = ['account_name', 'system']
        ordering = ['system', 'account_name']
    
    def __str__(self):
        return f"{self.account_name} ({self.system.name})"
    
    @property
    def is_password_expired(self):
        """Check if password has expired"""
        if not self.password_expires_on:
            return False
        return timezone.now() > self.password_expires_on
    
    @property
    def is_password_expiring_soon(self):
        """Check if password is expiring within 30 days"""
        if not self.password_expires_on:
            return False
        days_until_expiry = (self.password_expires_on - timezone.now()).days
        return 0 <= days_until_expiry <= 30
    
    @property
    def days_until_password_expiry(self):
        """Get number of days until password expires"""
        if not self.password_expires_on:
            return None
        days = (self.password_expires_on - timezone.now()).days
        return max(0, days) if days >= 0 else None
    
    @property
    def is_compliant(self):
        """Check if account is fully compliant"""
        return (
            self.password_complies_with_policy and
            self.password_policy_verified_date is not None and
            not self.is_password_expired
        )
    
    @property
    def compliance_status(self):
        """Get compliance status"""
        if not self.is_active:
            return "Inactive"
        if not self.password_complies_with_policy:
            return "Non-Compliant"
        if not self.password_policy_verified_date:
            return "Unverified"
        if self.is_password_expired:
            return "Password Expired"
        if self.is_password_expiring_soon:
            return "Expiring Soon"
        return "Compliant"
    
    def get_compliance_color(self):
        """Get Bootstrap color class for compliance status"""
        status = self.compliance_status
        colors = {
            'Compliant': 'success',
            'Expiring Soon': 'warning',
            'Password Expired': 'danger',
            'Non-Compliant': 'danger',
            'Unverified': 'warning',
            'Inactive': 'secondary'
        }
        return colors.get(status, 'secondary')
    
    def get_account_type_color(self):
        """Get Bootstrap color class for account type"""
        colors = {
            'Service': 'primary',
            'Interface': 'info',
            'Backup': 'secondary',
            'Privileged': 'danger'
        }
        return colors.get(self.account_type, 'secondary')
    
    def get_latest_password_history(self):
        """Get the most recent password change record"""
        return self.password_history.order_by('-password_changed_date').first()
    
    def clean(self):
        """Validate the model instance"""
        super().clean()
        # Ensure account_name is not empty
        if not self.account_name or not self.account_name.strip():
            raise ValidationError("Account name cannot be empty")
    
    def save(self, *args, **kwargs):
        """Override save to handle validation"""
        self.full_clean()
        super().save(*args, **kwargs)


class ServiceAccountPasswordHistory(models.Model):
    """
    Service Account Password History model for tracking password changes
    Documents password change history for audit compliance
    """
    
    service_account = models.ForeignKey(
        ServiceAccount,
        on_delete=models.CASCADE,
        related_name='password_history',
        help_text="Service account this password change belongs to"
    )
    
    password_changed_date = models.DateTimeField(
        help_text="Date password was changed in the external system"
    )
    
    changed_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_account_password_changes',
        help_text="Who documented the change"
    )
    
    documented_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When it was documented in this system"
    )
    
    expires_on = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Password expiration date"
    )
    
    complies_with_policy = models.BooleanField(
        default=True,
        help_text="Whether password complies with RHG policy"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Notes about the password change"
    )
    
    class Meta:
        verbose_name = 'Service Account Password History'
        verbose_name_plural = 'Service Account Password History'
        ordering = ['-password_changed_date']
    
    def __str__(self):
        return f"{self.service_account.account_name} - Password changed on {self.password_changed_date.strftime('%Y-%m-%d')}"
    
    @property
    def is_expired(self):
        """Check if password has expired"""
        if not self.expires_on:
            return False
        return timezone.now() > self.expires_on
    
    @property
    def days_until_expiry(self):
        """Get number of days until password expires"""
        if not self.expires_on:
            return None
        days = (self.expires_on - timezone.now()).days
        return max(0, days) if days >= 0 else None

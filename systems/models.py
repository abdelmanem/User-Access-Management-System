from django.db import models
from django.utils import timezone
from django.core.validators import URLValidator


class System(models.Model):
    """
    System model for managing all IT systems and applications
    Tracks system details, access requirements, and metadata
    """
    
    SYSTEM_TYPE_CHOICES = [
        ('Web Application', 'Web Application'),
        ('Desktop Application', 'Desktop Application'),
        ('Mobile Application', 'Mobile Application'),
        ('Database', 'Database'),
        ('API', 'API'),
        ('Operating System', 'Operating System'),
        ('Network Device', 'Network Device'),
        ('Cloud Service', 'Cloud Service'),
        ('Third-party Service', 'Third-party Service'),
        ('Internal Tool', 'Internal Tool'),
        ('Legacy System', 'Legacy System'),
        ('Other', 'Other'),
    ]
    
    CRITICALITY_LEVEL_CHOICES = [
        ('Critical', 'Critical - Business Critical'),
        ('High', 'High - Important'),
        ('Medium', 'Medium - Standard'),
        ('Low', 'Low - Nice to Have'),
    ]
    
    ENVIRONMENT_TYPE_CHOICES = [
        ('Production', 'Production'),
        ('Staging', 'Staging'),
        ('Testing', 'Testing'),
        ('Development', 'Development'),
        ('Training', 'Training'),
        ('DR', 'Disaster Recovery'),
        ('Sandbox', 'Sandbox'),
    ]
    
    AUTHENTICATION_TYPE_CHOICES = [
        ('Local', 'Local Authentication'),
        ('LDAP', 'LDAP/Active Directory'),
        ('SSO', 'Single Sign-On'),
        ('OAuth', 'OAuth'),
        ('SAML', 'SAML'),
        ('API Key', 'API Key'),
        ('Certificate', 'Certificate'),
        ('Multi-Factor', 'Multi-Factor Authentication'),
        ('External', 'External Authentication'),
    ]
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="System name (must be unique)"
    )
    
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="System code (e.g., ERP, CRM, HRIS)"
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of the system"
    )
    
    system_type = models.CharField(
        max_length=50,
        choices=SYSTEM_TYPE_CHOICES,
        default='Web Application',
        help_text="The type of the system (e.g., Application, Database, Network Device)."
    )
    
    criticality_level = models.CharField(
        max_length=20,
        choices=CRITICALITY_LEVEL_CHOICES,
        default='Medium',
        help_text="Business criticality level"
    )
    
    environment_type = models.CharField(
        max_length=20,
        choices=ENVIRONMENT_TYPE_CHOICES,
        default='Production',
        help_text="Environment type"
    )
    
    url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator()],
        help_text="System URL or endpoint"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="System IP address (if applicable)"
    )
    
    server_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Server hostname or name"
    )
    
    version = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Current system version"
    )
    
    vendor = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="System vendor or provider"
    )
    
    vendor_contact = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Vendor contact information"
    )
    
    support_contact = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Internal support contact"
    )
    
    documentation_url = models.URLField(
        blank=True,
        null=True,
        validators=[URLValidator()],
        help_text="Link to system documentation"
    )
    
    authentication_type = models.CharField(
        max_length=30,
        choices=AUTHENTICATION_TYPE_CHOICES,
        default='Local',
        help_text="Authentication method used"
    )
    
    requires_approval = models.BooleanField(
        default=True,
        help_text="Whether access requires approval"
    )
    
    approval_workflow = models.TextField(
        blank=True,
        null=True,
        help_text="Description of approval workflow"
    )
    
    access_instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Instructions for accessing the system"
    )
    
    password_policy = models.TextField(
        blank=True,
        null=True,
        help_text="Password requirements and policies"
    )
    
    session_timeout = models.IntegerField(
        blank=True,
        null=True,
        help_text="Session timeout in minutes (if applicable)"
    )
    
    data_classification = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Data classification level (e.g., Public, Internal, Confidential)"
    )
    
    compliance_requirements = models.TextField(
        blank=True,
        null=True,
        help_text="Compliance requirements (SOX, HIPAA, etc.)"
    )
    
    backup_frequency = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Backup frequency and schedule"
    )
    
    disaster_recovery_plan = models.TextField(
        blank=True,
        null=True,
        help_text="Disaster recovery procedures"
    )
    
    maintenance_window = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Scheduled maintenance window"
    )
    
    last_maintenance_date = models.DateField(
        blank=True,
        null=True,
        help_text="Last maintenance date"
    )
    
    next_maintenance_date = models.DateField(
        blank=True,
        null=True,
        help_text="Next scheduled maintenance"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this system is currently active"
    )
    
    is_monitored = models.BooleanField(
        default=True,
        help_text="Whether system is actively monitored"
    )
    
    sla_uptime_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="SLA uptime percentage (e.g., 99.95)"
    )
    
    sla_response_time_hours = models.IntegerField(
        blank=True,
        null=True,
        help_text="SLA response time in hours"
    )
    
    sla_resolution_time_hours = models.IntegerField(
        blank=True,
        null=True,
        help_text="SLA resolution time in hours"
    )
    
    # System owner and technical details
    system_owner = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_systems',
        help_text="System owner/business owner"
    )
    
    technical_lead = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='technical_systems',
        help_text="Technical lead/administrator"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='systems_created'
    )
    updated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='systems_updated'
    )
    
    class Meta:
        verbose_name = 'System'
        verbose_name_plural = 'Systems'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    @property
    def full_name(self):
        """Return full system name with environment"""
        if self.environment_type != 'Production':
            return f"{self.name} ({self.environment_type})"
        return self.name
    
    @property
    def uptime_percentage_display(self):
        """Return formatted uptime percentage"""
        if self.sla_uptime_percentage:
            return f"{self.sla_uptime_percentage}%"
        return "Not specified"
    
    @property
    def is_critical(self):
        """Check if system is critical"""
        return self.criticality_level == 'Critical'
    
    @property
    def is_high_priority(self):
        """Check if system is high priority"""
        return self.criticality_level in ['Critical', 'High']
    
    @property
    def maintenance_due(self):
        """Check if maintenance is due"""
        if not self.next_maintenance_date:
            return False
        return self.next_maintenance_date <= timezone.now().date()
    
    def get_system_owner_name(self):
        """Return system owner's name or None"""
        return self.system_owner.full_name if self.system_owner else None
    
    def get_technical_lead_name(self):
        """Return technical lead's name or None"""
        return self.technical_lead.full_name if self.technical_lead else None
    
    def get_active_user_count(self):
        """Get number of active users with access to this system"""
        from access_management.models import UserSystemAccess
        return UserSystemAccess.objects.filter(
            system=self,
            status='Active'
        ).count()
    
    def get_pending_requests_count(self):
        """Get number of pending access requests"""
        from access_management.models import UserSystemAccess
        return UserSystemAccess.objects.filter(
            system=self,
            status='Pending'
        ).count()
    
    def get_recent_access_history(self, days=30):
        """Get recent access history for this system"""
        from access_management.models import AccessHistory
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return AccessHistory.objects.filter(
            system=self,
            accessed_at__gte=cutoff_date
        ).order_by('-accessed_at')
    
    def can_be_deleted(self):
        """Check if system can be safely deleted"""
        # Cannot delete if it has active user access
        if self.get_active_user_count() > 0:
            return False, "Cannot delete system with active user access"
        
        # Cannot delete if it has pending requests
        if self.get_pending_requests_count() > 0:
            return False, "Cannot delete system with pending access requests"
        
        return True, "Can be deleted"
    
    def get_compliance_requirements_list(self):
        """Return compliance requirements as a list"""
        if not self.compliance_requirements:
            return []
        return [req.strip() for req in self.compliance_requirements.split(',')]
    
    def get_maintenance_status(self):
        """Get maintenance status"""
        if not self.last_maintenance_date and not self.next_maintenance_date:
            return "Unknown"
        
        if self.maintenance_due:
            return "Overdue"
        
        if self.next_maintenance_date:
            days_until = (self.next_maintenance_date - timezone.now().date()).days
            if days_until <= 7:
                return f"Due in {days_until} days"
            elif days_until <= 30:
                return "Upcoming"
        
        return "Current"
    
    def get_environment_color(self):
        """Get color coding for environment type"""
        colors = {
            'Production': 'danger',
            'Staging': 'warning',
            'Testing': 'info',
            'Development': 'secondary',
            'Training': 'primary',
            'DR': 'dark',
            'Sandbox': 'light'
        }
        return colors.get(self.environment_type, 'secondary')

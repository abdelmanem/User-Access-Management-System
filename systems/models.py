from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
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
        ('Email Subscription', 'Email Subscription'),
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


class SystemContract(models.Model):
    """
    Commercial and renewal metadata for a system.
    One-to-one with System to track renewal, fees, payment terms, and support contact.
    """

    DURATION_UNIT_CHOICES = [
        ('months', 'Months'),
        ('years', 'Years'),
    ]

    BILLING_FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('one_time', 'One-time'),
    ]

    FEE_TYPE_CHOICES = [
        ('recurring', 'Recurring'),
        ('one_time', 'One-time'),
        ('hybrid', 'Hybrid / Mixed'),
    ]

    # ISO 4217 currency codes (broad set to cover most countries)
    CURRENCY_CHOICES = [
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('AUD', 'AUD - Australian Dollar'),
        ('CAD', 'CAD - Canadian Dollar'),
        ('NZD', 'NZD - New Zealand Dollar'),
        ('JPY', 'JPY - Japanese Yen'),
        ('CNY', 'CNY - Chinese Yuan'),
        ('HKD', 'HKD - Hong Kong Dollar'),
        ('SGD', 'SGD - Singapore Dollar'),
        ('KRW', 'KRW - South Korean Won'),
        ('INR', 'INR - Indian Rupee'),
        ('AED', 'AED - UAE Dirham'),
        ('SAR', 'SAR - Saudi Riyal'),
        ('QAR', 'QAR - Qatari Riyal'),
        ('OMR', 'OMR - Omani Rial'),
        ('BHD', 'BHD - Bahraini Dinar'),
        ('KWD', 'KWD - Kuwaiti Dinar'),
        ('EGP', 'EGP - Egyptian Pound'),
        ('ZAR', 'ZAR - South African Rand'),
        ('NGN', 'NGN - Nigerian Naira'),
        ('KES', 'KES - Kenyan Shilling'),
        ('GHS', 'GHS - Ghanaian Cedi'),
        ('CHF', 'CHF - Swiss Franc'),
        ('SEK', 'SEK - Swedish Krona'),
        ('NOK', 'NOK - Norwegian Krone'),
        ('DKK', 'DKK - Danish Krone'),
        ('PLN', 'PLN - Polish Zloty'),
        ('CZK', 'CZK - Czech Koruna'),
        ('HUF', 'HUF - Hungarian Forint'),
        ('RON', 'RON - Romanian Leu'),
        ('TRY', 'TRY - Turkish Lira'),
        ('ILS', 'ILS - Israeli Shekel'),
        ('PKR', 'PKR - Pakistani Rupee'),
        ('BDT', 'BDT - Bangladeshi Taka'),
        ('LKR', 'LKR - Sri Lankan Rupee'),
        ('THB', 'THB - Thai Baht'),
        ('MYR', 'MYR - Malaysian Ringgit'),
        ('IDR', 'IDR - Indonesian Rupiah'),
        ('PHP', 'PHP - Philippine Peso'),
        ('VND', 'VND - Vietnamese Dong'),
        ('BRL', 'BRL - Brazilian Real'),
        ('ARS', 'ARS - Argentine Peso'),
        ('CLP', 'CLP - Chilean Peso'),
        ('COP', 'COP - Colombian Peso'),
        ('PEN', 'PEN - Peruvian Sol'),
        ('MXN', 'MXN - Mexican Peso'),
        ('UYU', 'UYU - Uruguayan Peso'),
        ('RUB', 'RUB - Russian Ruble'),
        ('UAH', 'UAH - Ukrainian Hryvnia'),
        ('MAD', 'MAD - Moroccan Dirham'),
        ('TND', 'TND - Tunisian Dinar'),
        ('DZD', 'DZD - Algerian Dinar'),
        ('ETB', 'ETB - Ethiopian Birr'),
        ('TZS', 'TZS - Tanzanian Shilling'),
        ('UGX', 'UGX - Ugandan Shilling'),
        ('XOF', 'XOF - West African CFA Franc'),
        ('XAF', 'XAF - Central African CFA Franc'),
    ]

    system = models.OneToOneField(
        System,
        on_delete=models.CASCADE,
        related_name='contract'
    )
    support_contact_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Support contact full name"
    )
    support_contact_role = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Support contact role/title"
    )
    support_contact_phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Support contact phone number"
    )
    support_contact_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Support contact email"
    )
    renewal_date = models.DateField(
        blank=True,
        null=True,
        help_text="Contract renewal date"
    )
    renewal_duration_value = models.PositiveIntegerField(
        default=1,
        help_text="Duration value (e.g., 1 year)"
    )
    renewal_duration_unit = models.CharField(
        max_length=10,
        choices=DURATION_UNIT_CHOICES,
        default='years',
        help_text="Duration unit (months/years)"
    )
    contract_fee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Base contract fee amount"
    )
    contract_fee_currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text="Billing currency"
    )
    local_currency = models.CharField(
        max_length=10,
        choices=CURRENCY_CHOICES,
        default='USD',
        help_text="Local/home currency for reporting"
    )
    exchange_rate_to_local = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        blank=True,
        null=True,
        help_text="Rate to convert billing currency to local (local = billing * rate)"
    )
    fee_type = models.CharField(
        max_length=10,
        choices=FEE_TYPE_CHOICES,
        default='recurring',
        help_text="Recurring or one-time fee structure"
    )
    payment_frequency = models.CharField(
        max_length=10,
        choices=BILLING_FREQUENCY_CHOICES,
        default='yearly',
        help_text="Billing cadence for recurring fees"
    )
    payment_terms = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Payment terms (e.g., Net 30, milestones)"
    )
    vat_included = models.BooleanField(
        default=False,
        help_text="Whether VAT is included in the fee amount"
    )
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="VAT percentage (e.g., 5 for 5%)"
    )
    reminder_enabled = models.BooleanField(
        default=True,
        help_text="Enable in-app reminders for renewal"
    )
    reminder_days_before = models.PositiveIntegerField(
        default=60,
        help_text="Days before renewal to flag reminders"
    )
    renewal_copy = models.FileField(
        upload_to='system_contracts/renewal_copies/',
        blank=True,
        null=True,
        help_text="Upload renewal or contract copy"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'System Contract'
        verbose_name_plural = 'System Contracts'
        ordering = ['renewal_date']

    def __str__(self):
        return f"{self.system.name} contract"

    def fee_amount_including_vat(self):
        """
        Return fee amount including VAT if VAT is excluded in the base amount.
        """
        if self.contract_fee_amount is None:
            return None

        amount = self.contract_fee_amount
        if not self.vat_included and self.vat_rate:
            amount = amount * (Decimal('1') + (self.vat_rate / Decimal('100')))
        return amount

    def fee_amount_local(self):
        """
        Convert base fee to local currency using the exchange rate (without VAT uplift).
        """
        if self.contract_fee_amount is None or not self.exchange_rate_to_local:
            return None
        return self.contract_fee_amount * self.exchange_rate_to_local

    def vat_amount(self):
        """
        VAT component on base fee in billing currency.
        """
        if self.contract_fee_amount is None or not self.vat_rate:
            return None

        rate = self.vat_rate / Decimal('100')
        if self.vat_included:
            # VAT included: extract VAT part from gross
            return self.contract_fee_amount - (self.contract_fee_amount / (Decimal('1') + rate))
        # VAT excluded: apply on top
        return self.contract_fee_amount * rate

    def vat_amount_local(self):
        """
        VAT component converted to local currency if exchange rate present.
        """
        vat = self.vat_amount()
        if vat is None or not self.exchange_rate_to_local:
            return None
        return vat * self.exchange_rate_to_local

    def fee_amount_local_including_vat(self):
        """
        Return fee amount converted to local currency using exchange_rate_to_local.
        """
        amount = self.fee_amount_including_vat()
        if amount is None or not self.exchange_rate_to_local:
            return None
        return amount * self.exchange_rate_to_local

    def annualized_fee(self):
        """
        Estimate annualized fee based on payment frequency, useful for P&L alignment.
        """
        amount = self.fee_amount_including_vat()
        if amount is None:
            return None

        multiplier_map = {
            'monthly': Decimal('12'),
            'quarterly': Decimal('4'),
            'yearly': Decimal('1'),
            'one_time': Decimal('1'),
        }
        multiplier = multiplier_map.get(self.payment_frequency, Decimal('1'))
        return amount * multiplier

    def annualized_fee_local(self):
        """
        Annualized fee converted to local currency, if exchange rate is provided.
        """
        base = self.annualized_fee()
        if base is None or not self.exchange_rate_to_local:
            return None
        return base * self.exchange_rate_to_local

    def save(self, *args, **kwargs):
        """
        Override save to create history entry before saving changes.
        """
        # Only create history if this is an update (has pk) and not a new instance
        if self.pk:
            try:
                old_instance = SystemContract.objects.get(pk=self.pk)
                # Check if any financial fields changed
                financial_fields = [
                    'contract_fee_amount', 'contract_fee_currency', 'local_currency',
                    'exchange_rate_to_local', 'due_amount_monthly', 'due_amount_yearly',
                    'payment_frequency', 'vat_included', 'vat_rate', 'renewal_date'
                ]
                has_changes = any(
                    getattr(old_instance, field) != getattr(self, field)
                    for field in financial_fields
                )
                if has_changes:
                    # Get user from request if available (will be None if not in request context)
                    user = getattr(self, '_current_user', None)
                    SystemContractHistory.create_from_contract(old_instance, user=user)
            except SystemContract.DoesNotExist:
                pass

        # Auto-calculate dues if not explicitly provided
        if self.due_amount_monthly is None or self.due_amount_yearly is None:
            # Prefer subscription tiers if present
            # Only access subscription_tiers if the object has been saved (has pk)
            tiers = list(self.subscription_tiers.all()) if self.pk and hasattr(self, 'subscription_tiers') else []
            if tiers:
                monthly = sum((t.monthly_billing_amount() or Decimal('0')) for t in tiers)
                yearly = sum((t.yearly_billing_amount() or Decimal('0')) for t in tiers)
            else:
                base = self.fee_amount_including_vat() or self.contract_fee_amount or Decimal('0')
                freq = (self.payment_frequency or '').lower()
                monthly = self.due_amount_monthly
                yearly = self.due_amount_yearly

                if monthly is None or yearly is None:
                    if freq == 'monthly':
                        monthly = monthly if monthly is not None else base
                        yearly = yearly if yearly is not None else (base * Decimal('12'))
                    elif freq == 'quarterly':
                        monthly = monthly if monthly is not None else (base / Decimal('3'))
                        yearly = yearly if yearly is not None else (base * Decimal('4'))
                    elif freq == 'yearly':
                        yearly = yearly if yearly is not None else base
                        monthly = monthly if monthly is not None else (yearly / Decimal('12'))
                    else:
                        # one_time or unspecified: treat as yearly, spread across 12 for monthly
                        yearly = yearly if yearly is not None else base
                        monthly = monthly if monthly is not None else (yearly / Decimal('12'))

            if monthly is not None and yearly is not None:
                self.due_amount_monthly = monthly.quantize(Decimal('0.01'))
                self.due_amount_yearly = yearly.quantize(Decimal('0.01'))

        super().save(*args, **kwargs)

    def recalc_dues_from_tiers(self, save=True):
        """
        Recalculate due amounts from subscription tiers.
        Ensures monthly/yearly dues stay in sync when tier billing frequency or prices change.
        """
        tiers = list(self.subscription_tiers.all())
        monthly = sum((t.monthly_billing_amount() or Decimal('0')) for t in tiers)
        yearly = sum((t.yearly_billing_amount() or Decimal('0')) for t in tiers)

        monthly = monthly.quantize(Decimal('0.01'))
        yearly = yearly.quantize(Decimal('0.01'))

        self.due_amount_monthly = monthly
        self.due_amount_yearly = yearly

        if save:
            self.save(update_fields=["due_amount_monthly", "due_amount_yearly", "updated_at"])

    # Optional explicit due amounts
    due_amount_monthly = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Explicit monthly due amount (billing currency)"
    )
    due_amount_yearly = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Explicit yearly due amount (billing currency)"
    )


class SystemContractHistory(models.Model):
    """
    Historical snapshot of SystemContract for tracking changes over time.
    Allows comparison of contract values between periods (month-over-month, year-over-year).
    """
    contract = models.ForeignKey(
        SystemContract,
        on_delete=models.CASCADE,
        related_name='history',
        help_text="The contract this history entry belongs to"
    )
    
    # Financial fields snapshot
    contract_fee_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Base contract fee amount at time of snapshot"
    )
    contract_fee_currency = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Billing currency at time of snapshot"
    )
    local_currency = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Local currency at time of snapshot"
    )
    exchange_rate_to_local = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        blank=True,
        null=True,
        help_text="Exchange rate at time of snapshot"
    )
    due_amount_monthly = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Monthly due amount at time of snapshot"
    )
    due_amount_yearly = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Yearly due amount at time of snapshot"
    )
    payment_frequency = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Payment frequency at time of snapshot"
    )
    vat_included = models.BooleanField(
        default=False,
        help_text="Whether VAT was included at time of snapshot"
    )
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="VAT rate at time of snapshot"
    )
    renewal_date = models.DateField(
        blank=True,
        null=True,
        help_text="Renewal date at time of snapshot"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who made the change"
    )
    change_reason = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Optional reason for the change"
    )
    
    class Meta:
        verbose_name = 'Contract History'
        verbose_name_plural = 'Contract Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract', '-created_at']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.contract.system.name} contract history - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def create_from_contract(cls, contract, user=None, reason=None):
        """
        Create a history entry from a contract instance.
        """
        return cls.objects.create(
            contract=contract,
            contract_fee_amount=contract.contract_fee_amount,
            contract_fee_currency=contract.contract_fee_currency,
            local_currency=contract.local_currency,
            exchange_rate_to_local=contract.exchange_rate_to_local,
            due_amount_monthly=contract.due_amount_monthly,
            due_amount_yearly=contract.due_amount_yearly,
            payment_frequency=contract.payment_frequency,
            vat_included=contract.vat_included,
            vat_rate=contract.vat_rate,
            renewal_date=contract.renewal_date,
            created_by=user,
            change_reason=reason,
        )
    
    def calculate_monthly_local(self):
        """Calculate monthly amount in local currency for this snapshot."""
        if not self.due_amount_monthly or not self.exchange_rate_to_local:
            return None
        return (self.due_amount_monthly * self.exchange_rate_to_local).quantize(Decimal('0.01'))
    
    def calculate_yearly_local(self):
        """Calculate yearly amount in local currency for this snapshot."""
        if not self.due_amount_yearly or not self.exchange_rate_to_local:
            return None
        return (self.due_amount_yearly * self.exchange_rate_to_local).quantize(Decimal('0.01'))


class SystemSubscriptionTier(models.Model):
    BILLING_FREQUENCY_CHOICES = [
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    ]

    contract = models.ForeignKey(
        SystemContract,
        on_delete=models.CASCADE,
        related_name='subscription_tiers'
    )
    name = models.CharField(max_length=100, help_text="License or SKU name (e.g., E1, E3)")
    license_category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Category key to match assigned users (e.g., E1, E3)"
    )
    billing_frequency = models.CharField(
        max_length=10,
        choices=BILLING_FREQUENCY_CHOICES,
        default='monthly'
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Unit price per seat in billing currency"
    )
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Discount percentage for this tier"
    )
    seats_committed = models.PositiveIntegerField(
        default=0,
        help_text="Contracted seats"
    )
    seats_manual = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Optional manual seats used override"
    )
    overage_unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Overage price per extra seat (billing currency). Defaults to unit price if blank."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription Tier"
        verbose_name_plural = "Subscription Tiers"

    def __str__(self):
        return f"{self.name} ({self.contract.system.name})"

    @property
    def seats_used_from_assignments(self):
        if not self.license_category:
            return None
        from access_management.models import UserSystemAccess
        return UserSystemAccess.objects.filter(
            system=self.contract.system,
            license_category__iexact=self.license_category
        ).count()

    @property
    def seats_used_effective(self):
        if self.seats_manual is not None:
            return self.seats_manual
        derived = self.seats_used_from_assignments
        # If no assignments or license_category is not set, fall back to committed seats
        if derived is None or derived == 0:
            return self.seats_committed
        return derived

    def _effective_unit_price(self):
        price = self.unit_price
        if self.discount_pct:
            price = price * (Decimal('1') - (self.discount_pct / Decimal('100')))
        return price

    def monthly_billing_amount(self):
        seats = self.seats_used_effective
        if seats <= 0:
            return Decimal('0')

        unit = self._effective_unit_price()
        overage_price = self.overage_unit_price or unit
        # Only charge overage when there is a committed seat baseline
        overage_units = max(0, seats - self.seats_committed) if self.seats_committed > 0 else 0

        if self.billing_frequency == 'monthly':
            base = unit * seats
            overage = overage_price * overage_units
            return base + overage
        # annual: spread across 12
        yearly = unit * seats
        overage_yearly = overage_price * overage_units
        return (yearly + overage_yearly) / Decimal('12')

    def yearly_billing_amount(self):
        seats = self.seats_used_effective
        if seats <= 0:
            return Decimal('0')

        unit = self._effective_unit_price()
        overage_price = self.overage_unit_price or unit
        # Only charge overage when there is a committed seat baseline
        overage_units = max(0, seats - self.seats_committed) if self.seats_committed > 0 else 0

        if self.billing_frequency == 'monthly':
            monthly = unit * seats
            overage = overage_price * overage_units
            return (monthly + overage) * Decimal('12')
        # annual
        yearly = unit * seats
        overage_yearly = overage_price * overage_units
        return yearly + overage_yearly


# Keep contract dues in sync with subscription tiers when tiers change
@receiver(post_save, sender=SystemSubscriptionTier)
def update_contract_dues_on_tier_save(sender, instance, **kwargs):
    contract = instance.contract
    contract.recalc_dues_from_tiers(save=True)


@receiver(post_delete, sender=SystemSubscriptionTier)
def update_contract_dues_on_tier_delete(sender, instance, **kwargs):
    contract = instance.contract
    contract.recalc_dues_from_tiers(save=True)

    def renewal_status(self):
        """
        Returns a simple status string to drive UI badges.
        """
        if not self.renewal_date:
            return 'missing'

        today = timezone.now().date()
        if self.renewal_date < today:
            return 'overdue'

        if self.reminder_enabled and self.renewal_date <= today + timedelta(days=self.reminder_days_before):
            return 'due_soon'

        return 'current'

    def is_within_reminder_window(self):
        if not self.renewal_date or not self.reminder_enabled:
            return False

        today = timezone.now().date()
        return self.renewal_date <= today + timedelta(days=self.reminder_days_before)

from django import forms
from django.utils.text import slugify
from django.forms import inlineformset_factory
from .models import System, SystemContract, SystemSubscriptionTier
from accounts.models import CustomUser
from access_management.models import UserSystemAccess
from hardware.models import HardwareAsset


class SystemForm(forms.ModelForm):
    class Meta:
        model = System
        fields = [
            'name',
            'code',
            'description',
            'system_type',
            'criticality_level',
            'environment_type',
            'url',
            'ip_address',
            'server_name',
            'version',
            'vendor',
            'vendor_contact',
            'support_contact',
            'documentation_url',
            'authentication_type',
            'requires_approval',
            'approval_workflow',
            'access_instructions',
            'password_policy',
            'session_timeout',
            'data_classification',
            'compliance_requirements',
            'backup_frequency',
            'disaster_recovery_plan',
            'maintenance_window',
            'last_maintenance_date',
            'next_maintenance_date',
            'is_active',
            'is_monitored',
            'sla_uptime_percentage',
            'sla_response_time_hours',
            'sla_resolution_time_hours',
            'system_owner',
            'technical_lead',
        ]
        widgets = {
            'last_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].required = False
        self.fields['code'].help_text = "Leave blank to auto-generate from the system name"
        qs = CustomUser.objects.order_by('first_name', 'last_name')
        self.fields['system_owner'].queryset = qs
        self.fields['technical_lead'].queryset = qs
        # Populate server_name choices from hardware assets so UI shows a dropdown of servers
        server_qs = HardwareAsset.objects.filter(
            hardware_type__in=['Server', 'Virtual Server']
        ).order_by('name', 'asset_tag')
        server_choices = [('', '---------')] + [
            (asset.name, f"{asset.name} [{asset.asset_tag}]")
            for asset in server_qs
        ]
        self.fields['server_name'] = forms.ChoiceField(
            choices=server_choices,
            required=False,
            label='Server name',
        )

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if code:
            return code

        name = self.cleaned_data.get('name', '')
        base = slugify(name).upper().replace('-', '')
        if not base:
            base = 'SYSTEM'
        base = base[:50]
        code_candidate = base
        counter = 1
        while System.objects.filter(code=code_candidate).exclude(pk=self.instance.pk).exists():
            suffix = f"-{counter}"
            code_candidate = f"{base[:50 - len(suffix)]}{suffix}"
            counter += 1
        return code_candidate


class SystemContractForm(forms.ModelForm):
    class Meta:
        model = SystemContract
        fields = [
            'support_contact_name',
            'support_contact_role',
            'support_contact_phone',
            'support_contact_email',
            'renewal_date',
            'renewal_duration_value',
            'renewal_duration_unit',
            'contract_fee_amount',
            'contract_fee_currency',
            'local_currency',
            'exchange_rate_to_local',
            'fee_type',
            'payment_frequency',
            'payment_terms',
            'vat_included',
            'vat_rate',
            'reminder_enabled',
            'reminder_days_before',
            'due_amount_monthly',
            'due_amount_yearly',
            'renewal_copy',
        ]
        widgets = {
            'renewal_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['contract_fee_currency'].help_text = "Billing currency (choose ISO code)"
        self.fields['local_currency'].help_text = "Local/home currency for reporting (choose ISO code)"
        self.fields['exchange_rate_to_local'].help_text = "Local = billing * exchange rate"
        self.fields['renewal_copy'].help_text = "Upload renewal copy (PDF/Image/Doc)"


SystemSubscriptionTierFormSet = inlineformset_factory(
    SystemContract,
    SystemSubscriptionTier,
    fields=[
        'name',
        'license_category',
        'billing_frequency',
        'unit_price',
        'discount_pct',
        'seats_committed',
        'seats_manual',
        'overage_unit_price',
    ],
    extra=1,
    can_delete=True,
    widgets={
        'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
        'discount_pct': forms.NumberInput(attrs={'step': '0.01'}),
        'overage_unit_price': forms.NumberInput(attrs={'step': '0.01'}),
    }
)


class SystemUserAssignForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select d-none'}),
        label='System Users',
        help_text='Move users between the Available and Selected boxes, then save.'
    )

    def __init__(self, *args, **kwargs):
        system = kwargs.pop('system')
        super().__init__(*args, **kwargs)
        self.system = system
        self.fields['users'].queryset = CustomUser.objects.order_by('first_name', 'last_name', 'username')
        existing_user_ids = UserSystemAccess.objects.filter(system=system).values_list('user_id', flat=True)
        self.fields['users'].initial = existing_user_ids


class SystemHardwareAssignForm(forms.Form):
    hardware_assets = forms.ModelMultipleChoiceField(
        queryset=HardwareAsset.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 15}),
        label='Hardware Assets',
        help_text='Select hardware assets that host or are associated with this system.'
    )

    def __init__(self, *args, **kwargs):
        system = kwargs.pop('system')
        super().__init__(*args, **kwargs)
        self.system = system
        self.fields['hardware_assets'].queryset = HardwareAsset.objects.order_by('name', 'asset_tag')
        existing_hardware_ids = system.hardware_assets.values_list('id', flat=True)
        self.fields['hardware_assets'].initial = existing_hardware_ids

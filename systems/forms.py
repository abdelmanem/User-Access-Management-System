from django import forms
from django.utils.text import slugify
from .models import System
from accounts.models import CustomUser
from access_management.models import UserSystemAccess


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


class SystemUserAssignForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=CustomUser.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 15}),
        label='System Users',
        help_text='Select users who should have access assignments for this system.'
    )

    def __init__(self, *args, **kwargs):
        system = kwargs.pop('system')
        super().__init__(*args, **kwargs)
        self.system = system
        self.fields['users'].queryset = CustomUser.objects.order_by('first_name', 'last_name', 'username')
        existing_user_ids = UserSystemAccess.objects.filter(system=system).values_list('user_id', flat=True)
        self.fields['users'].initial = existing_user_ids

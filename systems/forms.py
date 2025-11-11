from django import forms
from .models import System
from accounts.models import CustomUser


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
        qs = CustomUser.objects.order_by('first_name', 'last_name')
        self.fields['system_owner'].queryset = qs
        self.fields['technical_lead'].queryset = qs



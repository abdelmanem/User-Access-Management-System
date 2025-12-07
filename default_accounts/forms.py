from django import forms
from django.utils import timezone

from accounts.models import CustomUser
from systems.models import System

from .models import (
    DefaultAccount,
    DefaultAccountAction,
    DefaultAccountTemplate,
)


class DefaultAccountForm(forms.ModelForm):
    """Form used to document remediation evidence for default accounts."""

    class Meta:
        model = DefaultAccount
        fields = [
            'account_name',
            'system',
            'account_type',
            'status',
            'removal_required',
            'password_changed_in_external_system',
            'password_changed_date',
            'password_changed_by',
            'password_change_reference',
            'password_change_notes',
            'removed_from_external_system',
            'removal_date',
            'removal_confirmed_by',
            'removal_reference',
            'remediation_notes',
            'installation_checklist_completed',
            'installation_checklist_completed_date',
            'installation_documented_by',
            'installation_notes',
            'last_verified_date',
            'last_verified_by',
            'verification_artifact',
            'hosted_not_applicable_reason',
            'is_rhg_special_account',
        ]
        widgets = {
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'system': forms.Select(attrs={'class': 'form-select'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'removal_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'password_changed_in_external_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'password_changed_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'password_changed_by': forms.Select(attrs={'class': 'form-select'}),
            'password_change_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'password_change_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'removed_from_external_system': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'removal_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'removal_confirmed_by': forms.Select(attrs={'class': 'form-select'}),
            'removal_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'remediation_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'installation_checklist_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'installation_checklist_completed_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'installation_documented_by': forms.Select(attrs={'class': 'form-select'}),
            'installation_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'last_verified_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'last_verified_by': forms.Select(attrs={'class': 'form-select'}),
            'verification_artifact': forms.TextInput(attrs={'class': 'form-control'}),
            'hosted_not_applicable_reason': forms.TextInput(attrs={'class': 'form-control'}),
            'is_rhg_special_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_systems = System.objects.filter(is_active=True).order_by('name')
        active_users = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['system'].queryset = active_systems
        for field_name in [
            'password_changed_by',
            'removal_confirmed_by',
            'installation_documented_by',
            'last_verified_by',
        ]:
            self.fields[field_name].queryset = active_users
            self.fields[field_name].required = False

        for datetime_field in [
            'password_changed_date',
            'removal_date',
            'installation_checklist_completed_date',
            'last_verified_date',
        ]:
            self.fields[datetime_field].required = False

        self.fields['password_change_reference'].required = False
        self.fields['password_change_notes'].required = False
        self.fields['removal_reference'].required = False
        self.fields['remediation_notes'].required = False
        self.fields['installation_notes'].required = False
        self.fields['verification_artifact'].required = False
        self.fields['hosted_not_applicable_reason'].required = False


class DefaultAccountActionForm(forms.ModelForm):
    """Quick action form for logging password resets, removals, and verifications."""

    class Meta:
        model = DefaultAccountAction
        fields = ['action_type', 'action_date', 'evidence_reference', 'notes', 'status_applied']
        widgets = {
            'action_type': forms.Select(attrs={'class': 'form-select'}),
            'action_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'evidence_reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'status_applied': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['action_date'].initial = timezone.now()
        self.fields['evidence_reference'].required = False
        self.fields['notes'].required = False
        self.fields['status_applied'].required = False


class DefaultAccountTemplateForm(forms.ModelForm):
    """Admin form to maintain template registry without using Django admin."""

    class Meta:
        model = DefaultAccountTemplate
        fields = [
            'system',
            'account_name',
            'account_type',
            'removal_required',
            'applies_to_all',
            'rhg_special_account',
            'default_status',
            'description',
            'notes',
        ]
        widgets = {
            'system': forms.Select(attrs={'class': 'form-select'}),
            'account_name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'removal_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'applies_to_all': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'rhg_special_account': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'default_status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow selecting a specific system or leave blank for global templates.
        active_systems = System.objects.filter(is_active=True).order_by('name')
        self.fields['system'].queryset = active_systems
        self.fields['system'].required = False
        self.fields['system'].empty_label = "All Systems (Global Template)"



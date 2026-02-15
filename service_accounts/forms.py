from django import forms
from django.utils import timezone
from .models import (
    ServiceAccount,
    ServiceAccountPasswordHistory,
    ServiceAccountAttestation,
)
from systems.models import System
from accounts.models import CustomUser


class ServiceAccountForm(forms.ModelForm):
    """Form for creating and editing service accounts"""
    
    class Meta:
        model = ServiceAccount
        fields = [
            'account_name',
            'system',
            'account_type',
            'is_privileged',
            'admin_user',
            'purpose',
            'owner',
            'password_last_changed',
            'password_expires_on',
            'password_complies_with_policy',
            'password_policy_verified_date',
            'password_policy_verified_by',
            'change_request_id',
            'sop_reference',
            'sop_document',
            'password_storage_location',
            'is_active',
            'notes',
        ]
        widgets = {
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., svc_backup, admin_account'
            }),
            'system': forms.Select(attrs={'class': 'form-select'}),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'is_privileged': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'admin_user': forms.Select(attrs={'class': 'form-select'}),
            'purpose': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe what this service account is used for...'
            }),
            'owner': forms.Select(attrs={'class': 'form-select'}),
            'password_last_changed': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'password_expires_on': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'password_complies_with_policy': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'password_policy_verified_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'password_policy_verified_by': forms.Select(attrs={'class': 'form-select'}),
            'change_request_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'CHG-12345'
            }),
            'sop_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'SOP-ACCESS-001'
            }),
            'sop_document': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'password_storage_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vault path / safe location'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to active systems only
        self.fields['system'].queryset = System.objects.filter(is_active=True).order_by('name')
        active_users = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['owner'].queryset = active_users
        self.fields['password_policy_verified_by'].queryset = active_users
        self.fields['admin_user'].queryset = active_users
        
        # Make owner and verified_by optional
        self.fields['owner'].required = False
        self.fields['password_policy_verified_by'].required = False
        self.fields['admin_user'].required = False
        self.fields['password_last_changed'].required = False
        self.fields['password_expires_on'].required = False
        self.fields['password_policy_verified_date'].required = False


class ServiceAccountPasswordHistoryForm(forms.ModelForm):
    """Form for recording password changes"""
    
    class Meta:
        model = ServiceAccountPasswordHistory
        fields = [
            'service_account',
            'password_changed_date',
            'expires_on',
            'complies_with_policy',
            'notes',
        ]
        widgets = {
            'service_account': forms.Select(attrs={'class': 'form-select'}),
            'password_changed_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'expires_on': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'complies_with_policy': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes about the password change...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to active service accounts only
        self.fields['service_account'].queryset = ServiceAccount.objects.filter(is_active=True).order_by('account_name')
        # Mark expires_on as optional but add helpful label
        self.fields['expires_on'].required = False
        self.fields['expires_on'].help_text = 'When will this password expire? Leave empty if password does not expire.'
        self.fields['notes'].required = False
    
    def save(self, commit=True, changed_by=None):
        """Override save to set changed_by"""
        instance = super().save(commit=False)
        if changed_by:
            instance.changed_by = changed_by
        if commit:
            instance.save()
        return instance


class ServiceAccountAttestationForm(forms.ModelForm):
    """Form for capturing owner attestations."""

    class Meta:
        model = ServiceAccountAttestation
        fields = ['status', 'storage_location', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'storage_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vault path / safe / password manager reference'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Attestation notes, evidence, change ticket, etc.'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['storage_location'].required = False
        self.fields['notes'].required = False


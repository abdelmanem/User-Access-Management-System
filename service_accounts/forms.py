from django import forms
from django.utils import timezone
from .models import ServiceAccount, ServiceAccountPasswordHistory
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
            'purpose',
            'owner',
            'password_last_changed',
            'password_expires_on',
            'password_complies_with_policy',
            'password_policy_verified_date',
            'password_policy_verified_by',
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
        self.fields['owner'].queryset = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
        self.fields['password_policy_verified_by'].queryset = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
        
        # Make owner and verified_by optional
        self.fields['owner'].required = False
        self.fields['password_policy_verified_by'].required = False
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
        self.fields['expires_on'].required = False
        self.fields['notes'].required = False
    
    def save(self, commit=True, changed_by=None):
        """Override save to set changed_by"""
        instance = super().save(commit=False)
        if changed_by:
            instance.changed_by = changed_by
        if commit:
            instance.save()
        return instance


from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group, Permission
from .models import CustomUser, LDAPConfiguration


class UserBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False
        # Add placeholders for phone number fields to show required format
        self.fields['phone_primary'].widget.attrs['placeholder'] = 'e.g., +1234567890 or 1234567890'
        self.fields['phone_primary'].help_text = 'Format: 9-15 digits, optionally starting with + or +1'
        if 'phone_secondary' in self.fields:
            self.fields['phone_secondary'].widget.attrs['placeholder'] = 'e.g., +1234567890 or 1234567890'
            self.fields['phone_secondary'].help_text = 'Format: 9-15 digits, optionally starting with + or +1'

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'personal_email',
            'department',
            'sub_department',
            'reports_to',
            'employment_type',
            'employment_status',
            'position',
            'job_title',
            'employee_level',
            'phone_primary',
            'phone_secondary',
            'office_location',
            'office_room',
            'work_address',
            'city',
            'state_province',
            'country',
            'postal_code',
            'join_date',
            'end_date',
            'probation_end_date',
            'date_of_birth',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relation',
            'profile_photo',
            'description',
            'notes',
            'flag_for_follow_up',
            # IT Administrator governance (RHG 4.3)
            'is_it_administrator',
            'it_admin_certification_date',
            'it_admin_certified_by',
            'is_active',
            'exclude_from_metrics',
        ]


class UserCreateForm(UserBaseForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput, required=False)

    class Meta(UserBaseForm.Meta):
        pass

    def clean(self):
        cleaned = super().clean()
        pwd1 = cleaned.get('password1')
        pwd2 = cleaned.get('password2')
        if pwd1 or pwd2:
            if pwd1 != pwd2:
                self.add_error('password2', 'Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        pwd1 = self.cleaned_data.get('password1')
        if pwd1:
            user.set_password(pwd1)
        else:
            user.set_unusable_password()
        if commit:
            user.save()
            self.save_m2m()
        return user


class UserUpdateForm(UserBaseForm):
    password = ReadOnlyPasswordHashField(label='Password', help_text='Password is not editable here.')

    class Meta(UserBaseForm.Meta):
        fields = UserBaseForm.Meta.fields + ['password']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show the hashed password read-only
        if self.instance and self.instance.pk:
            self.initial['password'] = self.instance.password
        self.fields['password'].disabled = True


class UserPermissionForm(forms.Form):
    is_staff = forms.BooleanField(
        required=False,
        label='Staff Status',
        help_text='Staff users can access the administrative areas that rely on the is_staff flag.'
    )
    is_superuser = forms.BooleanField(
        required=False,
        label='Superuser Status',
        help_text='Superusers bypass permission checks. Use with caution.'
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Groups',
        help_text='Select the groups this user should belong to.'
    )
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select', 'size': 15}),
        label='Individual Permissions',
        help_text='Hold Ctrl (Windows) or Command (Mac) to select multiple permissions.'
    )

    def __init__(self, *args, **kwargs):
        user_instance = kwargs.pop('user_instance')
        super().__init__(*args, **kwargs)

        self.fields['is_staff'].initial = user_instance.is_staff
        self.fields['is_superuser'].initial = user_instance.is_superuser
        self.fields['is_staff'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['is_superuser'].widget.attrs.update({'class': 'form-check-input'})

        self.fields['groups'].queryset = Group.objects.order_by('name')
        self.fields['permissions'].queryset = Permission.objects.select_related('content_type').order_by(
            'content_type__app_label', 'codename'
        )

        self.fields['groups'].initial = user_instance.groups.all()
        self.fields['permissions'].initial = user_instance.user_permissions.all()

        def permission_label(perm: Permission) -> str:
            return f"{perm.content_type.app_label} | {perm.name}"

        self.fields['permissions'].label_from_instance = permission_label


class UserPhotoForm(forms.ModelForm):
    """
    Standalone form to handle profile photo uploads/removals without
    requiring the full user form.
    """

    class Meta:
        model = CustomUser
        fields = ['profile_photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_photo'].required = False


class LDAPConfigurationForm(forms.ModelForm):
    """
    Form for LDAP/AD configuration
    """
    class Meta:
        model = LDAPConfiguration
        fields = [
            'ldap_enabled',
            'is_active_directory',
            'cache_passwords',
            'ad_domain',
            'ldap_client_tls_key',
            'ldap_client_tls_cert',
            'ldap_server',
            'use_tls',
            'allow_invalid_ssl',
            'bind_username',
            'base_dn',
            'ldap_filter',
            'ldap_auth_query',
            'default_permission_group',
            'ldap_username_field',
            'ldap_lastname_field',
            'ldap_firstname_field',
            'ldap_displayname_field',
            'ldap_employeenumber_field',
            'ldap_department_field',
            'ldap_manager_field',
            'ldap_email_field',
            'ldap_phone_field',
            'ldap_mobile_field',
            'ldap_jobtitle_field',
            'ldap_address_field',
            'ldap_city_field',
            'ldap_state_field',
            'ldap_postalcode_field',
            'ldap_country_field',
            'ldap_location_field',
            'ldap_active_flag',
            'ldap_invert_active_flag',
            'custom_password_reset_url',
        ]
        widgets = {
            'ldap_client_tls_key': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'ldap_client_tls_cert': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'ldap_filter': forms.TextInput(attrs={'class': 'form-control'}),
            'ldap_auth_query': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'ldap_server': 'Format: ldap://server:389 or ldaps://server:636',
            'base_dn': 'Example: DC=example,DC=com',
            'bind_username': 'Format: CN=ServiceAccount,CN=Users,DC=example,DC=com or username@domain.com',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name not in ['ldap_enabled', 'is_active_directory', 'cache_passwords',
                                   'use_tls', 'allow_invalid_ssl', 'ldap_invert_active_flag']:
                if not isinstance(field.widget, forms.Textarea):
                    field.widget.attrs['class'] = 'form-control'


class LDAPBindPasswordForm(forms.Form):
    """
    Form for providing the LDAP bind password at run-time.

    This allows admins to avoid storing the bind password in the database.
    """
    bind_password = forms.CharField(
        label='LDAP Bind Password (not stored)',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter LDAP bind password (will not be saved)',
            }
        ),
        help_text='Used only for this operation and not saved to the database.',
    )


class LDAPTestConnectionForm(forms.Form):
    """
    Form for testing LDAP connection
    """
    # Kept for backwards compatibility; currently unused directly
    pass  # No fields needed, uses active config


class LDAPTestLoginForm(forms.Form):
    """
    Form for testing LDAP login
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter LDAP username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )


class LDAPSyncForm(forms.Form):
    """
    Form for syncing users from LDAP
    """
    force_sync = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Force sync all users even if they were recently synced',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
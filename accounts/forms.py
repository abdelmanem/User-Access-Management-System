from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group, Permission
from .models import CustomUser


class UserBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = False

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
            'is_active',
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


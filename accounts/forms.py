from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import CustomUser


class UserBaseForm(forms.ModelForm):
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



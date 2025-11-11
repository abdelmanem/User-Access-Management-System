from django import forms
from .models import Department
from accounts.models import CustomUser


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = [
            'name',
            'code',
            'description',
            'parent_department',
            'department_type',
            'head_of_department',
            'cost_center',
            'budget_code',
            'office_location',
            'phone',
            'email',
            'is_active',
            'established_date',
        ]
        widgets = {
            'established_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head_of_department'].queryset = CustomUser.objects.order_by('first_name', 'last_name')
        self.fields['parent_department'].queryset = Department.objects.order_by('name')



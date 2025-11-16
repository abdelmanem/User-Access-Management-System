from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta

from departments.models import Department
from systems.models import System
from access_management.models import UserSystemAccess, AccessHistory
from hardware.models import HardwareAsset
from utils.exporters import export_to_csv
from utils.importers import (
    import_users_from_csv,
    import_departments_from_csv,
    import_systems_from_csv,
    import_hardware_from_csv,
    ImportErrorCollection,
)

User = get_user_model()

@login_required
def data_import_export_home(request):
    """Main page for data import/export."""
    return render(request, 'data_import_export/home.html')

@login_required
def export_users(request):
    """Export all users to CSV."""
    fields = [
        'username',
        'email',
        'first_name',
        'last_name',
        'employee_id',
        'phone_primary',
        'position',
        'employment_type',
        'employment_status',
        ('department_code', 'department__code'),
        'description',
        'is_active',
        'join_date',
        'date_joined',
    ]
    return export_to_csv(User.objects.all(), 'users.csv', fields)

@login_required
def export_departments(request):
    """Export all departments to CSV."""
    fields = [
        'name',
        'code',
        'description',
        'department_type',
        ('parent_department_code', 'parent_department__code'),
        ('head_of_department_employee_id', 'head_of_department__employee_id'),
        ('head_of_department', 'head_of_department__full_name'),
        'is_active',
        'established_date',
        'created_at',
    ]
    return export_to_csv(Department.objects.all(), 'departments.csv', fields)

@login_required
def export_systems(request):
    """Export all systems to CSV."""
    fields = [
        'name',
        'code',
        'description',
        'system_type',
        'criticality_level',
        'environment_type',
        'authentication_type',
        ('system_owner_employee_id', 'system_owner__employee_id'),
        ('system_owner', 'system_owner__full_name'),
        ('technical_lead_employee_id', 'technical_lead__employee_id'),
        ('technical_lead', 'technical_lead__full_name'),
        'requires_approval',
        'is_active',
        'is_monitored',
        'url',
        'ip_address',
        'created_at',
    ]
    return export_to_csv(System.objects.all(), 'systems.csv', fields)

@login_required
def export_access_assignments(request):
    """Export all access assignments to CSV."""
    fields = [
        ('user_employee_id', 'user__employee_id'),
        ('user_username', 'user__username'),
        ('system_code', 'system__code'),
        ('system_name', 'system__name'),
        'access_type',
        'status',
        'priority',
        'request_type',
        ('access_start', 'access_start_date'),
        ('access_end', 'access_end_date'),
        'created_at',
    ]
    return export_to_csv(UserSystemAccess.objects.all(), 'access_assignments.csv', fields)

@login_required
def export_access_history(request):
    """Export all access history to CSV."""
    fields = [
        ('user_employee_id', 'user__employee_id'),
        ('user_username', 'user__username'),
        ('system_code', 'system__code'),
        ('system_name', 'system__name'),
        'action',
        ('action_description', 'action_description'),
        ('accessed_at', 'accessed_at'),
        ('ip_address', 'ip_address'),
        ('success', 'success'),
        ('error_message', 'error_message'),
    ]
    return export_to_csv(AccessHistory.objects.all(), 'access_history.csv', fields)


@login_required
def export_hardware(request):
    """Export all hardware assets to CSV."""
    fields = [
        'name',
        'asset_tag',
        'serial_number',
        'hardware_type',
        'status',
        'manufacturer',
        'model_number',
        'operating_system',
        'cpu',
        'memory_gb',
        'storage_capacity_gb',
        'location',
        'ip_address',
        'mac_address',
        'is_virtual',
        'requires_patch_management',
        'purchase_date',
        'warranty_expiration',
        'end_of_life_date',
        'last_inventory_check',
        'next_inventory_check',
        ('department_code', 'department__code'),
        ('primary_user_employee_id', 'primary_user__employee_id'),
        ('assigned_user_employee_ids', 'get_assigned_user_employee_ids'),
        ('related_system_codes', 'get_related_system_codes'),
        'created_at',
        'updated_at',
    ]
    return export_to_csv(HardwareAsset.objects.all(), 'hardware_assets.csv', fields)

@login_required
def import_users(request):
    """Import users from CSV."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            import_users_from_csv(csv_file)
            messages.success(request, 'Users imported successfully.')
        except ImportErrorCollection as error_collection:
            for error in error_collection.errors:
                messages.error(request, error)
        except Exception as e:
            messages.error(request, f'Error importing users: {str(e)}')
    return redirect('data_import_export:home')

@login_required
def import_departments(request):
    """Import departments from CSV."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            import_departments_from_csv(csv_file)
            messages.success(request, 'Departments imported successfully.')
        except ImportErrorCollection as error_collection:
            for error in error_collection.errors:
                messages.error(request, error)
        except Exception as e:
            messages.error(request, f'Error importing departments: {str(e)}')
    return redirect('data_import_export:home')

@login_required
def import_systems(request):
    """Import systems from CSV."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            import_systems_from_csv(csv_file)
            messages.success(request, 'Systems imported successfully.')
        except ImportErrorCollection as error_collection:
            for error in error_collection.errors:
                messages.error(request, error)
        except Exception as e:
            messages.error(request, f'Error importing systems: {str(e)}')
    return redirect('data_import_export:home')


@login_required
def import_hardware(request):
    """Import hardware assets from CSV."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            import_hardware_from_csv(csv_file)
            messages.success(request, 'Hardware assets imported successfully.')
        except ImportErrorCollection as error_collection:
            for error in error_collection.errors:
                messages.error(request, error)
        except Exception as e:
            messages.error(request, f'Error importing hardware: {str(e)}')
    return redirect('data_import_export:home')


@login_required
def custom_export(request):
    """Custom export page with column selection and filters."""
    # Define available models and their field options
    model_configs = {
        'users': {
            'model': User,
            'name': 'Users',
            'fields': {
                'username': 'Username',
                'email': 'Email',
                'first_name': 'First Name',
                'last_name': 'Last Name',
                'employee_id': 'Employee ID',
                'phone_primary': 'Primary Phone',
                'phone_secondary': 'Secondary Phone',
                'personal_email': 'Personal Email',
                'position': 'Position',
                'job_title': 'Job Title',
                'description': 'Description',
                'employment_type': 'Employment Type',
                'employment_status': 'Employment Status',
                'employee_level': 'Employee Level',
                'department': 'Department',
                'department__name': 'Department Name',
                'department__code': 'Department Code',
                'reports_to__username': 'Reports To (Username)',
                'reports_to__first_name': 'Reports To (First Name)',
                'reports_to__last_name': 'Reports To (Last Name)',
                'office_location': 'Office Location',
                'office_room': 'Office Room',
                'city': 'City',
                'state_province': 'State/Province',
                'country': 'Country',
                'postal_code': 'Postal Code',
                'join_date': 'Join Date',
                'end_date': 'End Date',
                'is_active': 'Is Active',
                'date_joined': 'Date Joined',
                'notes': 'Notes',
            },
            'filters': {
                'is_active': {'type': 'boolean', 'label': 'Active Status'},
                'employment_status': {'type': 'choice', 'label': 'Employment Status', 'choices': User.EMPLOYMENT_STATUS_CHOICES},
                'employment_type': {'type': 'choice', 'label': 'Employment Type', 'choices': User.EMPLOYMENT_TYPE_CHOICES},
                'department': {'type': 'foreignkey', 'label': 'Department', 'queryset': Department.objects.all()},
            }
        },
        'departments': {
            'model': Department,
            'name': 'Departments',
            'fields': {
                'name': 'Name',
                'code': 'Code',
                'description': 'Description',
                'department_type': 'Department Type',
                'parent_department__name': 'Parent Department',
                'parent_department__code': 'Parent Department Code',
                'head_of_department__username': 'Head of Department',
                'head_of_department__employee_id': 'Head Employee ID',
                'is_active': 'Is Active',
                'established_date': 'Established Date',
                'created_at': 'Created At',
            },
            'filters': {
                'is_active': {'type': 'boolean', 'label': 'Active Status'},
                'department_type': {'type': 'choice', 'label': 'Department Type', 'choices': Department.DEPARTMENT_TYPE_CHOICES},
            }
        },
        'systems': {
            'model': System,
            'name': 'Systems',
            'fields': {
                'name': 'Name',
                'code': 'Code',
                'description': 'Description',
                'system_type': 'System Type',
                'criticality_level': 'Criticality Level',
                'environment_type': 'Environment Type',
                'authentication_type': 'Authentication Type',
                'system_owner__username': 'System Owner',
                'system_owner__employee_id': 'System Owner Employee ID',
                'technical_lead__username': 'Technical Lead',
                'technical_lead__employee_id': 'Technical Lead Employee ID',
                'requires_approval': 'Requires Approval',
                'is_active': 'Is Active',
                'is_monitored': 'Is Monitored',
                'url': 'URL',
                'ip_address': 'IP Address',
                'created_at': 'Created At',
            },
            'filters': {
                'is_active': {'type': 'boolean', 'label': 'Active Status'},
                'system_type': {'type': 'choice', 'label': 'System Type', 'choices': System.SYSTEM_TYPE_CHOICES},
                'criticality_level': {'type': 'choice', 'label': 'Criticality Level', 'choices': System.CRITICALITY_LEVEL_CHOICES},
            }
        },
        'access_assignments': {
            'model': UserSystemAccess,
            'name': 'Access Assignments',
            'fields': {
                'user__username': 'User Username',
                'user__employee_id': 'User Employee ID',
                'user__first_name': 'User First Name',
                'user__last_name': 'User Last Name',
                'user__email': 'User Email',
                'system__name': 'System Name',
                'system__code': 'System Code',
                'access_type': 'Access Type',
                'status': 'Status',
                'priority': 'Priority',
                'request_type': 'Request Type',
                'access_start_date': 'Access Start Date',
                'access_end_date': 'Access End Date',
                'created_at': 'Created At',
            },
            'filters': {
                'status': {'type': 'choice', 'label': 'Status', 'choices': UserSystemAccess.STATUS_CHOICES},
                'access_type': {'type': 'choice', 'label': 'Access Type', 'choices': UserSystemAccess.ACCESS_TYPE_CHOICES},
                'user__department': {'type': 'foreignkey', 'label': 'User Department', 'queryset': Department.objects.all()},
            }
        },
    }
    
    selected_model = request.GET.get('model', 'users')
    config = model_configs.get(selected_model, model_configs['users'])
    
    # Handle POST request for export
    if request.method == 'POST':
        selected_columns = request.POST.getlist('columns')
        model_type = request.POST.get('model_type', 'users')
        
        if not selected_columns:
            messages.error(request, 'Please select at least one column to export.')
            return render(request, 'data_import_export/custom_export.html', {
                'model_configs': model_configs,
                'selected_model': selected_model,
                'config': config,
            })
        
        # Get the queryset
        queryset = config['model'].objects.all()
        
        # Apply filters
        if model_type == 'users':
            if request.POST.get('filter_is_active') == 'active':
                queryset = queryset.filter(is_active=True)
            elif request.POST.get('filter_is_active') == 'inactive':
                queryset = queryset.filter(is_active=False)
            
            if request.POST.get('filter_employment_status'):
                queryset = queryset.filter(employment_status=request.POST.get('filter_employment_status'))
            
            if request.POST.get('filter_employment_type'):
                queryset = queryset.filter(employment_type=request.POST.get('filter_employment_type'))
            
            if request.POST.get('filter_department'):
                queryset = queryset.filter(department_id=request.POST.get('filter_department'))
            
            if request.POST.get('filter_search'):
                search_term = request.POST.get('filter_search')
                queryset = queryset.filter(
                    Q(username__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term) |
                    Q(email__icontains=search_term) |
                    Q(employee_id__icontains=search_term)
                )
        
        elif model_type == 'departments':
            if request.POST.get('filter_is_active') == 'active':
                queryset = queryset.filter(is_active=True)
            elif request.POST.get('filter_is_active') == 'inactive':
                queryset = queryset.filter(is_active=False)
            
            if request.POST.get('filter_department_type'):
                queryset = queryset.filter(department_type=request.POST.get('filter_department_type'))
        
        elif model_type == 'systems':
            if request.POST.get('filter_is_active') == 'active':
                queryset = queryset.filter(is_active=True)
            elif request.POST.get('filter_is_active') == 'inactive':
                queryset = queryset.filter(is_active=False)
            
            if request.POST.get('filter_system_type'):
                queryset = queryset.filter(system_type=request.POST.get('filter_system_type'))
            
            if request.POST.get('filter_criticality_level'):
                queryset = queryset.filter(criticality_level=request.POST.get('filter_criticality_level'))
        
        elif model_type == 'access_assignments':
            if request.POST.get('filter_status'):
                queryset = queryset.filter(status=request.POST.get('filter_status'))
            
            if request.POST.get('filter_access_type'):
                queryset = queryset.filter(access_type=request.POST.get('filter_access_type'))
            
            if request.POST.get('filter_department'):
                queryset = queryset.filter(user__department_id=request.POST.get('filter_department'))
        
        # Prepare fields for export
        fields = []
        for col in selected_columns:
            if col in config['fields']:
                # Use the field name as both header and attribute path
                fields.append((config['fields'][col], col))
        
        filename = f"{config['name'].lower().replace(' ', '_')}_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return export_to_csv(queryset, filename, fields)
    
    # GET request - show the form
    return render(request, 'data_import_export/custom_export.html', {
        'model_configs': model_configs,
        'selected_model': selected_model,
        'config': config,
    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model

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

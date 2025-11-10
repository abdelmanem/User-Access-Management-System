from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.management import call_command
from django.contrib.auth import get_user_model
from departments.models import Department
from systems.models import System
from access_management.models import UserSystemAccess, AccessHistory
from utils.exporters import export_to_csv
from utils.importers import import_users_from_csv, import_departments_from_csv, import_systems_from_csv
import csv
import io

User = get_user_model()

@login_required
def data_import_export_home(request):
    """Main page for data import/export."""
    return render(request, 'data_import_export/home.html')

@login_required
def export_users(request):
    """Export all users to CSV."""
    fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
    return export_to_csv(User.objects.all(), 'users.csv', fields)

@login_required
def export_departments(request):
    """Export all departments to CSV."""
    fields = ['name', 'description', 'is_active', 'created_at']
    return export_to_csv(Department.objects.all(), 'departments.csv', fields)

@login_required
def export_systems(request):
    """Export all systems to CSV."""
    fields = ['name', 'description', 'owner', 'is_active', 'created_at']
    return export_to_csv(System.objects.all(), 'systems.csv', fields)

@login_required
def export_access_assignments(request):
    """Export all access assignments to CSV."""
    fields = ['user', 'system', 'access_type', 'status', 'priority', 'created_at']
    return export_to_csv(UserSystemAccess.objects.all(), 'access_assignments.csv', fields)

@login_required
def export_access_history(request):
    """Export all access history to CSV."""
    fields = ['user', 'system', 'action', 'action_description', 'timestamp', 'ip_address']
    return export_to_csv(AccessHistory.objects.all(), 'access_history.csv', fields)

@login_required
def import_users(request):
    """Import users from CSV."""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csv_file = request.FILES['csv_file']
        try:
            import_users_from_csv(csv_file)
            messages.success(request, 'Users imported successfully.')
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
        except Exception as e:
            messages.error(request, f'Error importing systems: {str(e)}')
    return redirect('data_import_export:home')

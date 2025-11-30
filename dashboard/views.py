from copy import deepcopy
import csv
import json
from datetime import timedelta, datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q, Avg, Max, Min, Sum
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDate
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils import timezone

from access_management.models import UserSystemAccess, AccessHistory
from accounts.models import LDAPConfiguration
from departments.models import Department
from default_accounts.models import DefaultAccountTemplate
from default_accounts.services import (
    create_default_accounts_for_system,
    ensure_default_account_templates_seeded,
)
from hardware.models import HardwareAsset
from systems.models import System

from .forms import (
    ActiveDirectorySettingsForm,
    DatabaseMaintenanceForm,
    SystemSeedForm,
)
from .models import ApplicationSetting

User = get_user_model()


def home(request):
    """
    Root landing page - shows welcome page if authenticated, otherwise redirects to login.
    """
    if request.user.is_authenticated:
        # User is logged in, show welcome page
        return render(request, 'dashboard/home.html', {
            'user': request.user,
        })
    else:
        # User is not authenticated, redirect to login
        from django.shortcuts import redirect
        from django.urls import reverse
        return redirect('accounts:login')


@login_required
def dashboard_home(request):
    """Main dashboard view with overview statistics."""
    
    # Get basic statistics (exclude non-reportable accounts)
    reportable_users = User.objects.included_in_metrics()
    total_users = reportable_users.count()
    active_users = reportable_users.filter(is_active=True).count()

    all_users = User.objects.all()
    total_user_population = all_users.count()
    excluded_users_count = all_users.filter(exclude_from_metrics=True).count()
    total_active_users = reportable_users.filter(is_active=True).count()
    total_inactive_users = reportable_users.filter(is_active=False).count()
    no_department_users = reportable_users.filter(department__isnull=True).count()
    follow_up_users = reportable_users.filter(flag_for_follow_up=True).count()
    total_systems = System.objects.count()
    active_systems = System.objects.filter(is_active=True).count()
    total_departments = Department.objects.count()
    active_departments = Department.objects.filter(is_active=True).count()
    
    # Get failed logins from today
    today = timezone.now().date()
    failed_logins_today = AccessHistory.objects.filter(
        action='Failed Login',
        accessed_at__date=today
    ).count()
    
    # Get active access records
    now = timezone.now()
    active_access = UserSystemAccess.objects.filter(
        status='Active',
        access_start_date__lte=now
    ).filter(
        Q(access_end_date__isnull=True) | Q(access_end_date__gte=now)
    ).count()
    
    # Get pending access requests
    pending_requests = UserSystemAccess.objects.filter(status='Pending').count()
    
    context = {
        'title': 'Dashboard',
        'total_users': total_users,
        'active_users': active_users,
        'total_user_population': total_user_population,
        'excluded_users_count': excluded_users_count,
        'total_active_users': total_active_users,
        'total_inactive_users': total_inactive_users,
        'no_department_users': no_department_users,
        'follow_up_users': follow_up_users,
        'total_systems': total_systems,
        'active_systems': active_systems,
        'total_departments': total_departments,
        'active_departments': active_departments,
        'failed_logins_today': failed_logins_today,
        'active_access': active_access,
        'pending_requests': pending_requests,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
def analytics_view(request):
    """Analytics and reporting view."""
    from dashboard.admin import dashboard_admin_site
    
    context = {
        'title': 'Analytics & Reports',
        'access_trends': dashboard_admin_site.get_access_trends(),
        'system_usage': dashboard_admin_site.get_system_usage(),
        'department_stats': dashboard_admin_site.get_department_stats(),
        'security_metrics': dashboard_admin_site.get_security_metrics(),
    }
    return render(request, 'admin/analytics.html', context)


@login_required
def reports_view(request):
    """Reports view."""
    from dashboard.admin import dashboard_admin_site
    
    context = {
        'title': 'Reports',
        'report_types': dashboard_admin_site.get_available_reports(),
    }
    return render(request, 'admin/reports.html', context)


@login_required
def application_settings_view(request):
    """Application settings view."""
    # Placeholder - implement based on your needs
    return render(request, 'admin/application_settings.html', {
        'title': 'Application Settings',
    })


@login_required
def generate_user_access_report(request):
    """Generate user access report."""
    # Placeholder - implement report generation logic
    messages.info(request, 'User access report generation not yet implemented.')
    return redirect('dashboard:reports')


@login_required
def generate_system_usage_report(request):
    """Generate system usage report."""
    # Placeholder - implement report generation logic
    messages.info(request, 'System usage report generation not yet implemented.')
    return redirect('dashboard:reports')


@login_required
def generate_security_audit_report(request):
    """Generate security audit report."""
    # Placeholder - implement report generation logic
    messages.info(request, 'Security audit report generation not yet implemented.')
    return redirect('dashboard:reports')


@login_required
def generate_department_access_report(request):
    """Generate department access report."""
    # Placeholder - implement report generation logic
    messages.info(request, 'Department access report generation not yet implemented.')
    return redirect('dashboard:reports')


@login_required
def generate_hardware_inventory_report(request):
    """Generate hardware inventory report."""
    # Placeholder - implement report generation logic
    messages.info(request, 'Hardware inventory report generation not yet implemented.')
    return redirect('dashboard:reports')


@login_required
def api_dashboard_data(request):
    """API endpoint for dashboard data."""
    reportable_users = User.objects.included_in_metrics()
    now = timezone.now()
    
    data = {
        'total_users': reportable_users.count(),
        'active_users': reportable_users.filter(is_active=True).count(),
        'total_systems': System.objects.count(),
        'active_systems': System.objects.filter(is_active=True).count(),
        'total_departments': Department.objects.count(),
        'active_access': UserSystemAccess.objects.filter(
            status='Active',
            access_start_date__lte=now
        ).filter(
            Q(access_end_date__isnull=True) | Q(access_end_date__gte=now)
        ).count(),
        'pending_requests': UserSystemAccess.objects.filter(status='Pending').count(),
    }
    
    return JsonResponse(data)


APPLICATION_SETTING_DEFAULTS = {
    'active_directory': {
        'label': 'Active Directory Integration',
        'description': 'Manage synchronization with corporate Active Directory.',
        'category': 'integration',
        'value': {
            'enabled': False,
            'domain_controller': '',
            'base_dn': '',
            'service_account': '',
            'sync_frequency': 'daily',
            'last_sync': None,
        },
    },
}

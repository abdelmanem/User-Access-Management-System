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
    from dashboard.admin import dashboard_admin_site
    
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
    pending_requests_count = UserSystemAccess.objects.filter(status='Pending').count()
    pending_requests_queryset = UserSystemAccess.objects.filter(status='Pending').select_related(
        'user', 'system', 'created_by'
    ).order_by('-created_at')[:10]
    
    pending_requests = [
        {
            'user_name': req.user.get_full_name() if hasattr(req.user, 'get_full_name') and req.user.get_full_name() else req.user.username,
            'system_name': req.system.name if req.system else 'Unknown',
            'priority': getattr(req, 'priority', 'Normal'),
            'priority_badge': {
                'High': 'danger',
                'Medium': 'warning',
                'Low': 'info',
                'Normal': 'secondary',
            }.get(getattr(req, 'priority', 'Normal'), 'secondary'),
            'submitted': req.created_at,
        }
        for req in pending_requests_queryset
    ]
    
    # Hardware statistics
    total_hardware = HardwareAsset.objects.count()
    active_hardware = HardwareAsset.objects.filter(status='In Service').count()
    hardware_counts = {
        'total': total_hardware,
        'in_service': HardwareAsset.objects.filter(status='In Service').count(),
        'in_storage': HardwareAsset.objects.filter(status='In Storage').count(),
        'retired': HardwareAsset.objects.filter(status='Retired').count(),
    }
    virtual_assets = HardwareAsset.objects.filter(is_virtual=True).count()
    
    # Hardware warranties
    warranty_cutoff = today + timedelta(days=90)
    warranty_expiring_soon = HardwareAsset.objects.filter(
        warranty_expiration__lte=warranty_cutoff,
        warranty_expiration__gte=today
    ).count()
    
    hardware_warranties = {
        'upcoming': [
            {
                'id': hw.id,
                'name': hw.name,
                'asset_tag': hw.asset_tag,
                'department': hw.department.name if hw.department else None,
                'warranty_expiration': hw.warranty_expiration,
                'days_remaining': (hw.warranty_expiration - today).days if hw.warranty_expiration else None,
            }
            for hw in HardwareAsset.objects.filter(
                warranty_expiration__lte=warranty_cutoff,
                warranty_expiration__gte=today
            ).select_related('department').order_by('warranty_expiration')[:10]
        ],
        'overdue': [
            {
                'id': hw.id,
                'name': hw.name,
                'asset_tag': hw.asset_tag,
                'department': hw.department.name if hw.department else None,
                'warranty_expiration': hw.warranty_expiration,
                'overdue_days': (today - hw.warranty_expiration).days if hw.warranty_expiration else None,
            }
            for hw in HardwareAsset.objects.filter(
                warranty_expiration__lt=today
            ).select_related('department').order_by('warranty_expiration')[:10]
        ],
    }
    
    # Hardware patch exceptions
    hardware_patch_exceptions_list = []
    for hw in HardwareAsset.objects.filter(
        requires_patch_management=False
    ).select_related('department').prefetch_related('related_systems')[:10]:
        hardware_patch_exceptions_list.append({
            'id': hw.id,
            'name': hw.name,
            'asset_tag': hw.asset_tag,
            'department': hw.department.name if hw.department else None,
            'status': hw.status,
            'status_badge': hw.lifecycle_state_color,
            'systems_count': hw.related_systems.count(),
        })
    hardware_patch_exceptions = hardware_patch_exceptions_list
    
    # Hardware status breakdown
    status_counts = HardwareAsset.objects.values('status').annotate(count=Count('id'))
    total_for_percentage = sum(s['count'] for s in status_counts)
    hardware_status_breakdown = [
        {
            'label': s['status'] or 'Unknown',
            'count': s['count'],
            'percentage': round((s['count'] / total_for_percentage * 100) if total_for_percentage > 0 else 0, 1),
            'color': {
                'In Service': 'success',
                'In Storage': 'info',
                'Retired': 'secondary',
            }.get(s['status'], 'secondary'),
        }
        for s in status_counts
    ]
    
    # Hardware top systems
    hardware_top_systems = System.objects.annotate(
        hardware_count=Count('hardware_assets', distinct=True),
        active_assignments=Count(
            'user_accesses',
            filter=Q(
                user_accesses__status='Active',
                user_accesses__access_start_date__lte=now
            ) & (
                Q(user_accesses__access_end_date__isnull=True) |
                Q(user_accesses__access_end_date__gte=now)
            ),
            distinct=True
        )
    ).filter(hardware_count__gt=0).order_by('-hardware_count')[:10]
    
    # Recent activity
    recent_activity = [
        {
            'title': f"{ah.user.get_full_name() if hasattr(ah.user, 'get_full_name') else ah.user.username} {ah.action.lower()} {ah.system.name if ah.system else 'system'}",
            'timestamp': ah.accessed_at,
            'icon': 'sign-in-alt' if ah.action == 'Login' else 'key' if 'Access' in ah.action else 'info-circle',
        }
        for ah in AccessHistory.objects.select_related('user', 'system').order_by('-accessed_at')[:10]
    ]
    
    # Access trends for charts (last 7 days)
    access_trends_data = []
    access_trends_labels = []
    for i in range(7):
        date = today - timedelta(days=6-i)
        access_count = AccessHistory.objects.filter(
            action='Login',
            success=True,
            accessed_at__date=date
        ).count()
        access_trends_data.append(access_count)
        access_trends_labels.append(date.strftime('%b %d'))
    
    access_trends = {
        'labels': json.dumps(access_trends_labels),
        'data': json.dumps(access_trends_data),
    }
    
    # System usage for charts
    system_usage_queryset = System.objects.filter(is_active=True).annotate(
        user_count=Count(
            'user_accesses',
            filter=Q(
                user_accesses__status='Active',
                user_accesses__access_start_date__lte=now
            ) & (
                Q(user_accesses__access_end_date__isnull=True) |
                Q(user_accesses__access_end_date__gte=now)
            ),
            distinct=True
        )
    ).filter(user_count__gt=0).order_by('-user_count')[:10]
    
    system_usage_labels = [s.name for s in system_usage_queryset]
    system_usage_data = [s.user_count for s in system_usage_queryset]
    
    system_usage = {
        'labels': json.dumps(system_usage_labels),
        'data': json.dumps(system_usage_data),
    }
    
    # Hardware distribution for charts
    hardware_distribution_data = HardwareAsset.objects.values('hardware_type').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    hardware_distribution_labels = [h['hardware_type'] or 'Unknown' for h in hardware_distribution_data]
    hardware_distribution_counts = [h['count'] for h in hardware_distribution_data]
    
    hardware_distribution = {
        'labels': json.dumps(hardware_distribution_labels),
        'data': json.dumps(hardware_distribution_counts),
    }
    
    # Create User KPI Snapshot list
    user_kpis = [
        {
            'label': 'Reportable Users',
            'value': total_users,
            'badge': 'primary',
            'description': 'Included in KPI metrics',
        },
        {
            'label': 'Active Reportable Users',
            'value': active_users,
            'badge': 'success',
            'description': 'Reportable accounts currently active',
        },
        {
            'label': 'Excluded from Metrics',
            'value': excluded_users_count,
            'badge': 'secondary',
            'description': 'Users intentionally excluded from reporting',
        },
        {
            'label': 'Active',
            'value': total_active_users,
            'badge': 'info',
            'description': 'All reportable users marked active',
        },
        {
            'label': 'Inactive',
            'value': total_inactive_users,
            'badge': 'warning',
            'description': 'All reportable users marked inactive',
        },
        {
            'label': 'No Department',
            'value': no_department_users,
            'badge': 'danger',
            'description': 'Users missing department assignment',
        },
        {
            'label': 'Need Follow-up',
            'value': follow_up_users,
            'badge': 'dark',
            'description': 'Flagged for manual review',
        },
    ]
    
    # Stats dictionary for template
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_hardware': total_hardware,
        'active_hardware': active_hardware,
        'pending_requests': pending_requests_count,
        'failed_logins_24h': failed_logins_today,
        'warranty_expiring': warranty_expiring_soon,
        'patch_exceptions': len(hardware_patch_exceptions),
        'virtual_assets': virtual_assets,
    }
    
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
        'user_kpis': user_kpis,
        'stats': stats,
        'access_trends': access_trends,
        'system_usage': system_usage,
        'hardware_distribution': hardware_distribution,
        'hardware_counts': hardware_counts,
        'hardware_warranties': hardware_warranties,
        'hardware_patch_exceptions': hardware_patch_exceptions,
        'hardware_status_breakdown': hardware_status_breakdown,
        'hardware_top_systems': hardware_top_systems,
        'recent_activity': recent_activity,
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

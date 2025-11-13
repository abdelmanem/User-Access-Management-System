from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Avg, Max, Min, Sum
from django.db.models.functions import ExtractHour, ExtractWeekDay, TruncDate
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from datetime import timedelta, datetime
import csv
import json
from access_management.models import UserSystemAccess, AccessHistory
from systems.models import System
from departments.models import Department
from hardware.models import HardwareAsset

User = get_user_model()

@login_required
def dashboard_home(request):
    """Main dashboard view with overview statistics."""
    
    # Get basic statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
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
    
    # Get suspicious activities (multiple failed logins from same IP)
    suspicious_activities = AccessHistory.objects.filter(
        action='Failed Login',
        accessed_at__date=today
    ).values('ip_address').annotate(
        failure_count=Count('id')
    ).filter(failure_count__gte=3).count()
    
    # Get recent activities
    recent_activities = AccessHistory.objects.select_related(
        'user', 'system'
    ).order_by('-accessed_at')[:10]
    
    # Format recent activities for template
    formatted_activities = []
    for activity in recent_activities:
        if activity.action == 'Login':
            formatted_activities.append({
                'type': 'login',
                'icon': 'sign-in-alt',
                'title': f"{activity.user.get_full_name()} logged into {activity.system.name}",
                'timestamp': activity.accessed_at
            })
        elif activity.action == 'Approved':
            formatted_activities.append({
                'type': 'access',
                'icon': 'key',
                'title': f"Access granted to {activity.user.get_full_name()} for {activity.system.name}",
                'timestamp': activity.accessed_at
            })
        elif activity.action == 'Failed Login':
            formatted_activities.append({
                'type': 'error',
                'icon': 'exclamation-triangle',
                'title': f"Failed login attempt for {activity.user.get_full_name() if activity.user else 'Unknown user'}",
                'timestamp': activity.accessed_at
            })
    
    # Get pending access requests
    pending_requests = UserSystemAccess.objects.filter(
        status='Pending'
    ).select_related('user', 'system').order_by('-created_at')[:5]
    
    # Format pending requests for template
    formatted_requests = []
    for request in pending_requests:
        formatted_requests.append({
            'id': request.id,
            'user_name': request.user.get_full_name(),
            'system_name': request.system.name,
            'priority': request.priority.lower()
        })
    
    # System usage for doughnut chart
    system_usage = UserSystemAccess.objects.values('system__name').annotate(count=Count('id')).order_by('-count')
    system_usage_labels = [item['system__name'] for item in system_usage]
    system_usage_data = [item['count'] for item in system_usage]

    access_trends = AccessHistory.objects.filter(
        accessed_at__gte=timezone.now() - timezone.timedelta(days=7)
    ).values('accessed_at__date').annotate(count=Count('id')).order_by('accessed_at__date')

    access_trends_labels = [item['accessed_at__date'].strftime('%Y-%m-%d') for item in access_trends]
    access_trends_data = [item['count'] for item in access_trends]

    context = {
        'title': 'Dashboard',
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'total_systems': total_systems,
            'active_systems': active_systems,
            'total_departments': total_departments,
            'active_departments': active_departments,
            'failed_logins_24h': failed_logins_today,
            'suspicious_activities': suspicious_activities,
            'pending_requests': len(formatted_requests),
        },
        'recent_activity': formatted_activities,
        'access_trends': {
            'labels': access_trends_labels,
            'data': access_trends_data,
        },
        'system_usage': {
            'labels': system_usage_labels,
            'data': system_usage_data,
        },
    }
    
    return render(request, 'admin/dashboard.html', context)

@login_required
def analytics_view(request):
    """Analytics view with detailed charts and statistics."""
    
    # Get access trends data for the last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    access_trends = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date]
    ).annotate(
        date=TruncDate('accessed_at')
    ).values('date').annotate(
        total_access=Count('id', filter=Q(action__in=['Approved', 'Activated', 'Login'])),
        failed_access=Count('id', filter=Q(action__in=['Access Denied', 'Failed Login']))
    ).order_by('date')
    
    # Get system usage statistics
    system_usage = System.objects.annotate(
        access_count=Count('access_history', filter=Q(
            access_history__accessed_at__date__range=[start_date, end_date]
        ))
    ).order_by('-access_count')[:10]
    
    # Get department statistics
    department_stats = Department.objects.annotate(
        member_count=Count('department_members', distinct=True),
        active_systems=Count(
            'department_members__system_accesses__system',
            filter=Q(department_members__system_accesses__system__is_active=True),
            distinct=True
        )
    ).order_by('-member_count')[:10]
    
    # Get security metrics
    security_metrics = {
        'failed_logins_last_30_days': AccessHistory.objects.filter(
            action='Failed Login',
            accessed_at__date__range=[start_date, end_date]
        ).count(),
        'suspicious_activities': AccessHistory.objects.filter(
            action='Failed Login',
            accessed_at__date__range=[start_date, end_date]
        ).values('ip_address').annotate(
            failure_count=Count('id')
        ).filter(failure_count__gte=5).count(),
        'password_changes': AccessHistory.objects.filter(
            action='Password Reset',
            accessed_at__date__range=[start_date, end_date]
        ).count(),
        'access_revocations': AccessHistory.objects.filter(
            action='Revoked',
            accessed_at__date__range=[start_date, end_date]
        ).count(),
    }
    
    context = {
        'title': 'Analytics',
        'access_trends': access_trends,
        'system_usage': system_usage,
        'department_stats': department_stats,
        'security_metrics': security_metrics,
    }
    
    return render(request, 'admin/analytics.html', context)

@login_required
def reports_view(request):
    """Reports view with report generation options."""
    
    report_types = [
        {
            'name': 'User Access Report',
            'description': 'Comprehensive report on user access to systems.',
            'icon': 'users',
            'url': reverse('user_access_report'),
            'export_url': f"{reverse('user_access_report')}?export=csv",
        },
        {
            'name': 'System Usage Report',
            'description': 'Analysis of system usage patterns and trends.',
            'icon': 'server',
            'url': reverse('system_usage_report'),
            'export_url': f"{reverse('system_usage_report')}?export=csv",
        },
        {
            'name': 'Security Audit Report',
            'description': 'Security events, failed logins, and compliance metrics.',
            'icon': 'shield-halved',
            'url': reverse('security_audit_report'),
            'export_url': f"{reverse('security_audit_report')}?export=csv",
        },
        {
            'name': 'Department Access Report',
            'description': 'Access distribution and risk indicators per department.',
            'icon': 'building',
            'url': reverse('department_access_report'),
            'export_url': f"{reverse('department_access_report')}?export=csv",
        },
        {
            'name': 'Hardware Inventory Report',
            'description': 'Inventory health, lifecycle, and system mappings for hardware assets.',
            'icon': 'desktop',
            'url': reverse('hardware_inventory_report'),
            'export_url': f"{reverse('hardware_inventory_report')}?export=csv",
        },
    ]
    
    now = timezone.now()
    today = now.date()
    warranty_threshold = today + timedelta(days=60)
    
    total_hardware = HardwareAsset.objects.count()
    in_service_hardware = HardwareAsset.objects.filter(status='In Service').count()
    warranty_expiring_soon = HardwareAsset.objects.filter(
        warranty_expiration__isnull=False,
        warranty_expiration__gte=today,
        warranty_expiration__lte=warranty_threshold
    ).count()
    overdue_warranty = HardwareAsset.objects.filter(
        warranty_expiration__isnull=False,
        warranty_expiration__lt=today
    ).count()
    patch_exceptions = HardwareAsset.objects.filter(requires_patch_management=False).count()
    virtual_assets = HardwareAsset.objects.filter(is_virtual=True).count()
    
    quick_insights = [
        {
            'label': 'Failed Logins (24h)',
            'value': AccessHistory.objects.filter(
                action='Failed Login',
                accessed_at__gte=now - timedelta(hours=24)
            ).count(),
            'icon': 'triangle-exclamation',
            'variant': 'danger',
        },
        {
            'label': 'Pending Access Requests',
            'value': UserSystemAccess.objects.filter(status='Pending').count(),
            'icon': 'hourglass-half',
            'variant': 'warning',
        },
        {
            'label': 'Access Expiring (30d)',
            'value': UserSystemAccess.objects.filter(
                status='Active',
                access_end_date__isnull=False,
                access_end_date__lte=now + timedelta(days=30),
                access_end_date__gte=now
            ).count(),
            'icon': 'calendar-xmark',
            'variant': 'info',
        },
        {
            'label': 'Inactive Users with Access',
            'value': UserSystemAccess.objects.filter(
                status='Active',
                user__is_active=False
            ).count(),
            'icon': 'user-slash',
            'variant': 'secondary',
        },
        {
            'label': 'Hardware Assets (Total)',
            'value': total_hardware,
            'icon': 'desktop',
            'variant': 'primary',
        },
        {
            'label': 'Hardware Assets (Active)',
            'value': in_service_hardware,
            'icon': 'laptop',
            'variant': 'success',
        },
        {
            'label': 'Warranties Expiring (60d)',
            'value': warranty_expiring_soon,
            'icon': 'calendar-check',
            'variant': 'warning',
        },
        {
            'label': 'Warranty Overdue',
            'value': overdue_warranty,
            'icon': 'triangle-exclamation',
            'variant': 'danger',
        },
        {
            'label': 'Virtual Hardware',
            'value': virtual_assets,
            'icon': 'cloud',
            'variant': 'info',
        },
        {
            'label': 'Patch Exceptions',
            'value': patch_exceptions,
            'icon': 'screwdriver-wrench',
            'variant': 'secondary',
        },
    ]
    
    context = {
        'title': 'Reports',
        'report_types': report_types,
        'quick_insights': quick_insights,
        'quick_updated_at': now,
    }
    
    return render(request, 'admin/reports.html', context)

@login_required
def generate_user_access_report(request):
    """Generate comprehensive user access report."""
    
    # Get all users with their access statistics
    users = User.objects.annotate(
        total_access=Count('system_accesses', distinct=True),
        active_access=Count('system_accesses', filter=Q(system_accesses__status='Active'), distinct=True),
        pending_requests=Count('system_accesses', filter=Q(system_accesses__status='Pending'), distinct=True),
        expired_access=Count('system_accesses', filter=Q(system_accesses__status='Expired'), distinct=True),
        shared_hardware=Count('hardware_assets', distinct=True),
        primary_hardware=Count('primary_hardware_assets', distinct=True),
    ).order_by('-total_access')
    
    access_summary = UserSystemAccess.objects.aggregate(
        total_access=Count('id'),
        active_access=Count('id', filter=Q(status='Active')),
        pending_requests=Count('id', filter=Q(status='Pending')),
        expired_access=Count('id', filter=Q(status='Expired'))
    )
    
    # Get access trends by user
    raw_trends = AccessHistory.objects.filter(
        accessed_at__gte=timezone.now() - timedelta(days=30),
        user__isnull=False
    ).values('user__username', 'user__first_name', 'user__last_name').annotate(
        access_count=Count('id', filter=Q(action__in=['Approved', 'Activated', 'Login'])),
        failed_count=Count('id', filter=Q(action__in=['Access Denied', 'Failed Login']))
    ).order_by('-access_count')[:20]
    
    access_trends = []
    for trend in raw_trends:
        total = trend['access_count'] + trend['failed_count']
        success_rate = round((trend['access_count'] / total) * 100, 1) if total else 0.0
        access_trends.append({
            'user__username': trend['user__username'],
            'user__first_name': trend['user__first_name'],
            'user__last_name': trend['user__last_name'],
            'access_count': trend['access_count'],
            'failed_count': trend['failed_count'],
            'success_rate': success_rate,
        })
    
    # Get department access distribution
    department_queryset = Department.objects.annotate(
        total_users=Count('department_members', distinct=True),
        total_access=Count('department_members__system_accesses', distinct=True),
        active_access=Count(
            'department_members__system_accesses',
            filter=Q(department_members__system_accesses__status='Active'),
            distinct=True
        )
    ).order_by('-total_access')
    
    department_access = []
    for dept in department_queryset:
        per_user = round(dept.total_access / dept.total_users, 1) if dept.total_users else 0.0
        department_access.append({
            'id': dept.id,
            'name': dept.name,
            'total_users': dept.total_users,
            'total_access': dept.total_access,
            'active_access': dept.active_access,
            'access_per_user': per_user,
        })
    
    hardware_totals = users.aggregate(
        total_shared=Sum('shared_hardware'),
        total_primary=Sum('primary_hardware')
    )
    hardware_summary = {
        'total_shared': hardware_totals['total_shared'] or 0,
        'total_primary': hardware_totals['total_primary'] or 0,
        'users_with_shared': users.filter(shared_hardware__gt=0).count(),
        'users_with_primary': users.filter(primary_hardware__gt=0).count(),
    }
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="user_access_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'User',
            'Department',
            'Total Access',
            'Active Access',
            'Pending Requests',
            'Expired Access',
            'Primary Hardware Assets',
            'Shared Hardware Assets',
        ])
        
        for user in users:
            writer.writerow([
                f"{user.first_name} {user.last_name}",
                user.department.name if user.department else 'No Department',
                user.total_access,
                user.active_access,
                user.pending_requests,
                user.expired_access,
                user.primary_hardware,
                user.shared_hardware,
            ])
        
        return response
    
    context = {
        'title': 'User Access Report',
        'users': users,
        'access_trends': access_trends,
        'department_access': department_access,
        'access_summary': {
            'total_access': access_summary['total_access'] or 0,
            'active_access': access_summary['active_access'] or 0,
            'pending_requests': access_summary['pending_requests'] or 0,
            'expired_access': access_summary['expired_access'] or 0,
        },
        'hardware_summary': hardware_summary,
    }
    
    return render(request, 'admin/reports/user_access_report.html', context)

@login_required
def generate_system_usage_report(request):
    """Generate system usage and performance report."""
    
    # Get system usage statistics
    systems_qs = System.objects.annotate(
        total_access=Count('access_history'),
        successful_access=Count('access_history', filter=Q(access_history__action__in=['Approved', 'Activated', 'Login'])),
        failed_access=Count('access_history', filter=Q(access_history__action__in=['Access Denied', 'Failed Login'])),
        unique_users=Count('access_history__user', distinct=True),
        active_assignments=Count('user_accesses', filter=Q(user_accesses__status='Active')),
        hardware_count=Count('hardware_assets', distinct=True),
    ).order_by('-total_access')
    
    systems = []
    for system in systems_qs:
        success_rate = round((system.successful_access / system.total_access) * 100, 1) if system.total_access else 0.0
        systems.append({
            'id': system.id,
            'name': system.name,
            'description': system.description,
            'total_access': system.total_access,
            'successful_access': system.successful_access,
            'failed_access': system.failed_access,
            'success_rate': success_rate,
            'unique_users': system.unique_users,
            'active_assignments': system.active_assignments,
            'hardware_count': system.hardware_count,
        })
    
    system_totals = systems_qs.aggregate(
        total_access_sum=Sum('total_access'),
        failed_access_sum=Sum('failed_access'),
        unique_users_sum=Sum('unique_users'),
        hardware_sum=Sum('hardware_count'),
    )
    summary = {
        'total_systems': systems_qs.count(),
        'total_access': system_totals['total_access_sum'] or 0,
        'failed_access': system_totals['failed_access_sum'] or 0,
        'unique_users': system_totals['unique_users_sum'] or 0,
        'hardware_assets': system_totals['hardware_sum'] or 0,
    }
    
    # Get daily usage trends for last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    daily_usage = list(AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date],
        action__in=['Approved', 'Activated', 'Login']
    ).annotate(
        date=TruncDate('accessed_at')
    ).values('system__name', 'date').annotate(
        access_count=Count('id')
    ).order_by('date', 'system__name'))
    
    # Get peak usage hours
    peak_hours_qs = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date],
        action__in=['Approved', 'Activated', 'Login']
    ).annotate(
        hour=ExtractHour('accessed_at')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    total_peak = sum(item['count'] for item in peak_hours_qs)
    peak_hours = [{
        'hour': int(item['hour']) if item['hour'] is not None else 0,
        'count': item['count'],
        'percentage': round((item['count'] / total_peak) * 100, 1) if total_peak else 0.0,
    } for item in peak_hours_qs]
    
    # Get access patterns by day of week
    day_patterns_qs = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date],
        action__in=['Approved', 'Activated', 'Login']
    ).annotate(
        day_of_week=ExtractWeekDay('accessed_at')
    ).values('day_of_week').annotate(
        count=Count('id')
    ).order_by('day_of_week')
    
    # Map day numbers to names
    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    total_day_count = sum(item['count'] for item in day_patterns_qs)
    day_patterns = []
    for pattern in day_patterns_qs:
        index = int(pattern['day_of_week']) - 1
        day_patterns.append({
            'day_name': day_names[index],
            'count': pattern['count'],
            'percentage': round((pattern['count'] / total_day_count) * 100, 1) if total_day_count else 0.0,
        })
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="system_usage_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['System', 'Total Access', 'Successful Access', 'Failed Access', 'Unique Users', 'Active Assignments', 'Linked Hardware Assets'])
        
        for system in systems_qs:
            writer.writerow([
                system.name,
                system.total_access,
                system.successful_access,
                system.failed_access,
                system.unique_users,
                system.active_assignments,
                system.hardware_count,
            ])
        
        return response
    
    context = {
        'title': 'System Usage Report',
        'systems': systems,
        'daily_usage': daily_usage,
        'peak_hours': peak_hours,
        'day_patterns': day_patterns,
        'summary': summary,
    }
    
    return render(request, 'admin/reports/system_usage_report.html', context)

@login_required
def generate_security_audit_report(request):
    """Generate security audit and compliance report."""
    
    # Get security events for last 30 days
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Security events breakdown
    security_events = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date]
    ).values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Failed login attempts by user
    failed_logins = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date],
        action='Failed Login'
    ).values('user__username', 'user__first_name', 'user__last_name').annotate(
        failure_count=Count('id')
    ).order_by('-failure_count')[:20]
    
    # Suspicious IP addresses (multiple failed logins)
    suspicious_ips = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date],
        action='Failed Login'
    ).values('ip_address').annotate(
        failure_count=Count('id'),
        unique_users=Count('user', distinct=True)
    ).filter(failure_count__gte=5).order_by('-failure_count')
    
    # Access violations (access denied to authorized users)
    access_violations = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date],
        action='Access Denied',
        user__isnull=False
    ).select_related('user', 'system').order_by('-accessed_at')[:50]
    
    # Password changes
    password_changes = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date],
        action='Password Reset'
    ).select_related('user').order_by('-accessed_at')[:50]
    
    # Access revocations
    access_revocations = AccessHistory.objects.filter(
        accessed_at__date__range=[start_date, end_date],
        action='Revoked'
    ).select_related('user', 'system').order_by('-accessed_at')[:50]
    
    # Compliance metrics
    compliance_metrics = {
        'total_users_with_access': UserSystemAccess.objects.filter(
            status='Active'
        ).values('user').distinct().count(),
        'users_with_expired_access': UserSystemAccess.objects.filter(
            status='Expired'
        ).values('user').distinct().count(),
        'pending_reviews': UserSystemAccess.objects.filter(
            next_review_date__lte=timezone.now().date()
        ).count(),
        'users_without_recent_activity': User.objects.exclude(
            id__in=AccessHistory.objects.filter(
                accessed_at__date__gte=timezone.now().date() - timedelta(days=90)
            ).values('user_id')
        ).count(),
    }
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="security_audit_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Security Event', 'Count'])
        
        for event in security_events:
            writer.writerow([
                event['action'],
                event['count']
            ])
        
        return response
    
    context = {
        'title': 'Security Audit Report',
        'security_events': security_events,
        'failed_logins': failed_logins,
        'suspicious_ips': suspicious_ips,
        'access_violations': access_violations,
        'password_changes': password_changes,
        'access_revocations': access_revocations,
        'compliance_metrics': compliance_metrics,
    }
    
    return render(request, 'admin/reports/security_audit_report.html', context)

@login_required
def generate_department_access_report(request):
    """Generate department access and permissions report."""
    
    # Get department statistics
    departments = Department.objects.annotate(
        total_members=Count('department_members', distinct=True),
        active_members=Count(
            'department_members',
            filter=Q(department_members__is_active=True),
            distinct=True
        ),
        total_access=Count('department_members__system_accesses', distinct=True),
        active_access=Count(
            'department_members__system_accesses',
            filter=Q(department_members__system_accesses__status='Active'),
            distinct=True
        ),
        pending_requests=Count(
            'department_members__system_accesses',
            filter=Q(department_members__system_accesses__status='Pending'),
            distinct=True
        )
    ).order_by('-total_members')
    
    # Get system access by department
    system_access_by_dept = System.objects.annotate(
        dept_access=Count(
            'user_accesses',
            filter=Q(user_accesses__user__department__isnull=False),
            distinct=True
        )
    ).order_by('-dept_access')
    
    # Get access patterns by department
    access_patterns = AccessHistory.objects.filter(
        accessed_at__gte=timezone.now() - timedelta(days=30)
    ).values('user__department__name').annotate(
        total_access=Count('id', filter=Q(action__in=['Approved', 'Activated', 'Login'])),
        failed_access=Count('id', filter=Q(action='Access Denied'))
    ).order_by('-total_access')
    
    # Get high-risk departments (high failure rate)
    risk_departments = []
    for dept in departments:
        if dept.total_members > 0:
            dept_access = AccessHistory.objects.filter(
                user__department=dept,
                accessed_at__gte=timezone.now() - timedelta(days=30)
            ).aggregate(
                total=Count('id'),
                failed=Count('id', filter=Q(action='Access Denied'))
            )
            
            if dept_access['total'] > 0:
                failure_rate = (dept_access['failed'] / dept_access['total']) * 100
                if failure_rate > 10:  # More than 10% failure rate
                    risk_departments.append({
                        'department': dept,
                        'failure_rate': failure_rate,
                        'total_attempts': dept_access['total'],
                        'failed_attempts': dept_access['failed']
                    })
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="department_access_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Department', 'Total Members', 'Active Members', 'Total Access', 'Active Access', 'Pending Requests'])
        
        for dept in departments:
            writer.writerow([
                dept.name,
                dept.total_members,
                dept.active_members,
                dept.total_access,
                dept.active_access,
                dept.pending_requests
            ])
        
        return response
    
    context = {
        'title': 'Department Access Report',
        'departments': departments,
        'system_access_by_dept': system_access_by_dept,
        'access_patterns': access_patterns,
        'risk_departments': risk_departments,
    }
    
    return render(request, 'admin/reports/department_access_report.html', context)


@login_required
def generate_hardware_inventory_report(request):
    """Generate comprehensive hardware inventory report."""
    
    assets_qs = HardwareAsset.objects.select_related('department', 'primary_user').prefetch_related('assigned_users', 'related_systems')
    today = timezone.now().date()
    warranty_threshold = today + timedelta(days=90)
    
    summary = {
        'total_assets': assets_qs.count(),
        'in_service': assets_qs.filter(status='In Service').count(),
        'in_storage': assets_qs.filter(status='In Storage').count(),
        'retired': assets_qs.filter(status__in=['Retired', 'Disposed']).count(),
        'patch_exceptions': assets_qs.filter(requires_patch_management=False).count(),
        'virtual_assets': assets_qs.filter(is_virtual=True).count(),
        'physical_assets': assets_qs.filter(is_virtual=False).count(),
        'warranty_expiring': assets_qs.filter(
            warranty_expiration__isnull=False,
            warranty_expiration__gte=today,
            warranty_expiration__lte=warranty_threshold
        ).count(),
        'warranty_overdue': assets_qs.filter(
            warranty_expiration__isnull=False,
            warranty_expiration__lt=today
        ).count(),
    }
    
    assets = []
    for asset in assets_qs:
        assigned_users = list(asset.assigned_users.all())
        related_systems = list(asset.related_systems.all())
        assets.append({
            'id': asset.id,
            'name': asset.name,
            'asset_tag': asset.asset_tag,
            'serial_number': asset.serial_number,
            'hardware_type': asset.get_hardware_type_display(),
            'status': asset.status,
            'status_badge': asset.lifecycle_state_color,
            'department': asset.department.name if asset.department else None,
            'primary_user': asset.primary_user.full_name if asset.primary_user else None,
            'primary_user_id': asset.primary_user.id if asset.primary_user else None,
            'systems_count': len(related_systems),
            'users_count': len(assigned_users),
            'location': asset.location,
            'warranty_expiration': asset.warranty_expiration,
            'days_until_warranty': asset.days_until_warranty_expires,
            'warranty_overdue_days': asset.warranty_overdue_days,
            'is_virtual': asset.is_virtual,
            'requires_patch_management': asset.requires_patch_management,
            'related_systems': related_systems,
            'assigned_users': assigned_users,
        })
    
    type_breakdown = list(
        assets_qs.values('hardware_type').annotate(
            count=Count('id'),
            in_service=Count('id', filter=Q(status='In Service')),
            virtual_count=Count('id', filter=Q(is_virtual=True)),
        ).order_by('-count')
    )
    
    status_breakdown = list(
        assets_qs.values('status').annotate(
            count=Count('id')
        ).order_by('-count')
    )
    
    department_breakdown = []
    for row in assets_qs.values('department__name').annotate(
        count=Count('id'),
        in_service=Count('id', filter=Q(status='In Service')),
        virtual_count=Count('id', filter=Q(is_virtual=True))
    ).order_by('-count'):
        department_breakdown.append({
            'department': row['department__name'] or 'Unassigned',
            'count': row['count'],
            'in_service': row['in_service'],
            'virtual': row['virtual_count'],
        })
    
    upcoming_warranties = []
    for asset in assets_qs.filter(
        warranty_expiration__isnull=False,
        warranty_expiration__gte=today,
        warranty_expiration__lte=warranty_threshold
    ).order_by('warranty_expiration'):
        upcoming_warranties.append({
            'asset': asset,
            'days_remaining': asset.days_until_warranty_expires,
        })
    
    overdue_warranties = assets_qs.filter(
        warranty_expiration__isnull=False,
        warranty_expiration__lt=today
    ).order_by('warranty_expiration')
    
    patch_exceptions = assets_qs.filter(requires_patch_management=False).order_by('name')
    
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="hardware_inventory_report.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name',
            'Asset Tag',
            'Serial Number',
            'Hardware Type',
            'Status',
            'Department',
            'Primary User',
            'Systems Linked',
            'Assigned Users',
            'Location',
            'Warranty Expiration',
            'Days Until Warranty',
            'Is Virtual',
            'Requires Patch Management',
        ])
        
        for asset in assets_qs:
            related_systems = list(asset.related_systems.all())
            assigned_users = list(asset.assigned_users.all())
            writer.writerow([
                asset.name,
                asset.asset_tag,
                asset.serial_number or '',
                asset.get_hardware_type_display(),
                asset.status,
                asset.department.name if asset.department else '',
                asset.primary_user.full_name if asset.primary_user else '',
                len(related_systems),
                len(assigned_users),
                asset.location or '',
                asset.warranty_expiration.isoformat() if asset.warranty_expiration else '',
                asset.days_until_warranty_expires if asset.days_until_warranty_expires is not None else '',
                'Yes' if asset.is_virtual else 'No',
                'Yes' if asset.requires_patch_management else 'No',
            ])
        
        return response
    
    context = {
        'title': 'Hardware Inventory Report',
        'summary': summary,
        'assets': assets,
        'type_breakdown': type_breakdown,
        'status_breakdown': status_breakdown,
        'department_breakdown': department_breakdown,
        'upcoming_warranties': upcoming_warranties,
        'overdue_warranties': overdue_warranties,
        'patch_exceptions': patch_exceptions,
    }
    
    return render(request, 'admin/reports/hardware_inventory_report.html', context)


@login_required
def api_dashboard_data(request):
    """API endpoint for dashboard data (for AJAX updates)."""
    
    # Get real-time statistics
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_systems': System.objects.count(),
        'active_systems': System.objects.filter(is_active=True).count(),
        'total_departments': Department.objects.count(),
        'active_departments': Department.objects.filter(is_active=True).count(),
        'failed_logins_today': AccessHistory.objects.filter(
            action='Failed Login',
            accessed_at__date=timezone.now().date()
        ).count(),
        'pending_requests': UserSystemAccess.objects.filter(status='Pending').count(),
        'active_access_assignments': UserSystemAccess.objects.filter(status='Active').count(),
    }
    
    # Get recent activities (last 5)
    recent_activities = AccessHistory.objects.select_related('user', 'system').order_by('-accessed_at')[:5]
    activities = []
    
    for activity in recent_activities:
        activities.append({
            'user': activity.user.get_full_name() if activity.user else 'Unknown User',
            'system': activity.system.name if activity.system else 'Unknown System',
            'action': activity.action_type,
            'timestamp': activity.timestamp.isoformat(),
            'success': activity.success
        })
    
    data = {
        'stats': stats,
        'recent_activities': activities,
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(data)

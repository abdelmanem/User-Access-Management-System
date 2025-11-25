from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from access_management.models import UserSystemAccess, AccessHistory
from systems.models import System
from departments.models import Department
from accounts.models import CustomUser

User = get_user_model()


class DashboardAdminSite(admin.AdminSite):
    site_header = 'User Access Management System'
    site_title = 'UAMS Admin'
    index_title = 'Dashboard'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard'),
            path('analytics/', self.admin_view(self.analytics_view), name='analytics'),
            path('reports/', self.admin_view(self.reports_view), name='reports'),
        ]
        return custom_urls + urls
    
    def index(self, request, extra_context=None):
        context = {
            'title': self.index_title,
            'dashboard_stats': self.get_dashboard_stats(),
            'recent_activities': self.get_recent_activities(),
            'pending_requests': self.get_pending_requests(),
            **(extra_context or {}),
        }
        return render(request, 'admin/dashboard_index.html', context)
    
    def dashboard_view(self, request):
        context = {
            'title': 'System Dashboard',
            'dashboard_stats': self.get_dashboard_stats(),
            'recent_activities': self.get_recent_activities(),
            'pending_requests': self.get_pending_requests(),
            'system_health': self.get_system_health(),
            'user_stats': self.get_user_stats(),
        }
        return render(request, 'admin/dashboard.html', context)
    
    def analytics_view(self, request):
        context = {
            'title': 'Analytics & Reports',
            'access_trends': self.get_access_trends(),
            'system_usage': self.get_system_usage(),
            'department_stats': self.get_department_stats(),
            'security_metrics': self.get_security_metrics(),
        }
        return render(request, 'admin/analytics.html', context)
    
    def reports_view(self, request):
        context = {
            'title': 'Reports',
            'report_types': self.get_available_reports(),
        }
        return render(request, 'admin/reports.html', context)
    
    def get_dashboard_stats(self):
        now = timezone.now()
        reportable_users = CustomUser.objects.included_in_metrics()
        return {
            'total_users': reportable_users.count(),
            'active_users': reportable_users.filter(is_active=True).count(),
            'total_systems': System.objects.filter(is_active=True).count(),
            'total_departments': Department.objects.filter(is_active=True).count(),
            'active_access': UserSystemAccess.objects.filter(
                status='Active',
                access_start_date__lte=now
            ).filter(
                Q(access_end_date__isnull=True) | Q(access_end_date__gte=now)
            ).count(),
            'pending_requests': UserSystemAccess.objects.filter(status='Pending').count(),
            'recent_logins': AccessHistory.objects.filter(
                action='Login',
                success=True,
                accessed_at__gte=now - timedelta(days=7)
            ).count(),
            'failed_logins': AccessHistory.objects.filter(
                action='Failed Login',
                success=False,
                accessed_at__gte=now - timedelta(days=7)
            ).count(),
        }
    
    def get_recent_activities(self):
        return AccessHistory.objects.select_related('user', 'system').order_by('-accessed_at')[:10]
    
    def get_pending_requests(self):
        return UserSystemAccess.objects.filter(
            status='Pending'
        ).select_related('user', 'system', 'created_by').order_by('-created_at')[:10]
    
    def get_system_health(self):
        systems = System.objects.filter(is_active=True)
        health_data = []
        now = timezone.now()
        for system in systems[:5]:  # Show top 5 systems
            active_users = UserSystemAccess.objects.filter(
                system=system,
                status='Active',
                access_start_date__lte=now
            ).filter(
                Q(access_end_date__isnull=True) | Q(access_end_date__gte=now)
            ).count()
            
            recent_failures = AccessHistory.objects.filter(
                system=system,
                success=False,
                accessed_at__gte=now - timedelta(days=7)
            ).count()
            
            health_data.append({
                'system': system,
                'active_users': active_users,
                'recent_failures': recent_failures,
                'health_status': 'Good' if recent_failures < 5 else 'Warning' if recent_failures < 10 else 'Critical'
            })
        return health_data
    
    def get_user_stats(self):
        reportable_users = CustomUser.objects.included_in_metrics()
        return {
            'by_department': reportable_users.values('department__name').annotate(
                count=Count('id')
            ).order_by('-count')[:5],
            'by_status': reportable_users.values('employment_status').annotate(
                count=Count('id')
            ),
            'recent_joined': reportable_users.filter(
                join_date__gte=timezone.now() - timedelta(days=30)
            ).count(),
        }
    
    def get_access_trends(self):
        # Get access trends for the last 30 days
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        
        trends = []
        for i in range(30):
            date = start_date + timedelta(days=i)
            access_count = AccessHistory.objects.filter(
                action='Login',
                success=True,
                accessed_at__date=date
            ).count()
            
            trends.append({
                'date': date.strftime('%Y-%m-%d'),
                'access_count': access_count
            })
        
        return trends
    
    def get_system_usage(self):
        now = timezone.now()
        return System.objects.filter(is_active=True).annotate(
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
        ).order_by('-user_count')[:10]
    
    def get_department_stats(self):
        return Department.objects.filter(is_active=True).annotate(
            user_count=Count(
                'department_members',
                filter=Q(department_members__exclude_from_metrics=False),
                distinct=True
            )
        ).order_by('-user_count')[:10]
    
    def get_security_metrics(self):
        return {
            'expired_access': UserSystemAccess.objects.filter(
                status='Active',
                access_end_date__lt=timezone.now()
            ).count(),
            'upcoming_reviews': UserSystemAccess.objects.filter(
                status='Approved',
                next_review_date__lte=timezone.now() + timedelta(days=7)
            ).count(),
            'failed_logins_week': AccessHistory.objects.filter(
                action='Failed Login',
                success=False,
                accessed_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'password_changes_week': AccessHistory.objects.filter(
                action='Password Reset',
                accessed_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
        }
    
    def get_available_reports(self):
        return [
            {
                'name': 'User Access Report',
                'description': 'Comprehensive report of all user access across systems',
                'icon': 'users',
            },
            {
                'name': 'System Usage Report',
                'description': 'Analysis of system usage patterns and access trends',
                'icon': 'chart-line',
            },
            {
                'name': 'Hardware Inventory Report',
                'description': 'Lifecycle, warranty, and ownership insights for hardware assets',
                'icon': 'desktop',
            },
            {
                'name': 'Security Audit Report',
                'description': 'Security events, failed logins, and access violations',
                'icon': 'shield-alt',
            },
            {
                'name': 'Compliance Report',
                'description': 'Compliance status and review schedules',
                'icon': 'check-circle',
            },
            {
                'name': 'Department Access Report',
                'description': 'Access distribution across departments',
                'icon': 'building',
            },
        ]


# Create the custom admin site instance
dashboard_admin_site = DashboardAdminSite(name='dashboard')

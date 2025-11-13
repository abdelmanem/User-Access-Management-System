from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/user-access/', views.generate_user_access_report, name='user_access_report'),
    path('reports/system-usage/', views.generate_system_usage_report, name='system_usage_report'),
    path('reports/security-audit/', views.generate_security_audit_report, name='security_audit_report'),
    path('reports/department-access/', views.generate_department_access_report, name='department_access_report'),
    path('reports/hardware-inventory/', views.generate_hardware_inventory_report, name='hardware_inventory_report'),
    path('api/dashboard-data/', views.api_dashboard_data, name='api_dashboard_data'),
]
from django.urls import path
from . import views

app_name = 'access_management'

urlpatterns = [
    # Access Assignment Management
    path('assignments/', views.access_assignment_list, name='access_assignment_list'),
    path('assignments/create/', views.access_assignment_create, name='access_assignment_create'),
    path('assignments/<int:pk>/', views.access_assignment_detail, name='access_assignment_detail'),
    path('assignments/<int:pk>/update/', views.access_assignment_update, name='access_assignment_update'),
    path('assignments/<int:pk>/delete/', views.access_assignment_delete, name='access_assignment_delete'),
    
    # User-specific access assignments
    path('users/<int:user_id>/assignments/', views.user_access_assignments, name='user_access_assignments'),
    
    # System-specific access assignments
    path('systems/<int:system_id>/assignments/', views.system_access_assignments, name='system_access_assignments'),
    
    # Access assignment actions
    path('assignments/<int:pk>/approve/', views.approve_access_assignment, name='approve_access_assignment'),
    path('assignments/<int:pk>/reject/', views.reject_access_assignment, name='reject_access_assignment'),
    
    # Access History
    path('history/', views.access_history_list, name='access_history_list'),
    path('history/user/<int:user_id>/', views.user_access_history, name='user_access_history'),
    path('history/system/<int:system_id>/', views.system_access_history, name='system_access_history'),
    path('history/assignment/<int:assignment_id>/', views.assignment_access_history, name='assignment_access_history'),
    
    # Generic Accounts Report
    path('generic-accounts/', views.generic_accounts_report, name='generic_accounts_report'),
    path('generic-accounts/<int:pk>/remediate/', views.mark_generic_account_remediated, name='mark_generic_account_remediated'),
    
    # Policy Drift Monitoring
    path('policy-drift-monitoring/', views.policy_drift_monitoring, name='policy_drift_monitoring'),

    # Administrator Accounts Compliance (RHG 4.3)
    path('admin-accounts/', views.admin_accounts_report, name='admin_accounts_report'),

    # Cross-System Account Mapping
    path('cross-system-mapping/', views.cross_system_account_mapping, name='cross_system_account_mapping'),
    path('users/<int:user_id>/cross-system-accounts/', views.user_cross_system_accounts, name='user_cross_system_accounts'),
]
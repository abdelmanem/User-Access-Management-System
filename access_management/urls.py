from django.urls import path
from . import views, views_new

app_name = 'access_management'

urlpatterns = [
    # Access Assignment Management
    path('assignments/', views.access_assignment_list, name='access_assignment_list'),
    path('assignments/my-pending/', views.my_pending_approvals, name='my_pending_approvals'),
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
    
    # Quarterly reviews & permission change documentation (RHG 4.5)
    path('quarterly-reviews/', views.quarterly_access_review_dashboard, name='quarterly_access_review_dashboard'),
    path('quarterly-reviews/bulk/', views.quarterly_access_review_bulk, name='quarterly_access_review_bulk'),
    path('quarterly-reviews/input/', views.quarterly_review_input, name='quarterly_review_input'),
    path('quarterly-reviews/output/', views.quarterly_review_output, name='quarterly_review_output'),
    path('permission-changes/output/', views.permission_change_output, name='permission_change_output'),
    # Legacy/advanced log pages
    path('quarterly-reviews/simple/', views.quarterly_access_review_simple, name='quarterly_access_review_simple'),
    path('quarterly-reviews/detailed/', views.quarterly_access_review_detailed, name='quarterly_access_review_detailed'),
    path('quarterly-reviews/detailed/<int:review_id>/', views.quarterly_access_review_detailed, name='quarterly_access_review_detailed_edit'),

    # Access approval compliance (RHG 4.6)
    path('access-approval-compliance/', views.access_approval_compliance, name='access_approval_compliance'),
    path('approval-summary-dashboard/', views.approval_summary_dashboard, name='approval_summary_dashboard'),
    path('unapproved-access/', views.unapproved_access_list, name='unapproved_access_list'),
    path('my-unapproved-access-gaps/', views.my_unapproved_access_gaps, name='my_unapproved_access_gaps'),

    # Policy Drift Monitoring
    path('policy-drift-monitoring/', views.policy_drift_monitoring, name='policy_drift_monitoring'),

    # Administrator Accounts Compliance (RHG 4.3)
    path('admin-accounts/', views.admin_accounts_report, name='admin_accounts_report'),

    # Cross-System Account Mapping
    path('cross-system-mapping/', views.cross_system_account_mapping, name='cross_system_account_mapping'),
    path('users/<int:user_id>/cross-system-accounts/', views.user_cross_system_accounts, name='user_cross_system_accounts'),
    path('accounts/status/', views.accounts_status, name='accounts_status'),
    
    # ===== NEW: IAM GOVERNANCE WORKFLOWS (Gaps 1-10) =====
    
    # Approval Workflow Routes - Gap 7 & 9
    path('approvals/', views_new.approval_dashboard, name='approval_dashboard'),
    path('approvals/<int:workflow_id>/step/<int:step_id>/', views_new.approve_access_request, name='approve_access_request'),
    
    # Evidence Repository Routes - Gap 6
    path('assignments/<int:access_id>/evidence/upload/', views_new.upload_evidence, name='upload_evidence'),
    path('assignments/<int:access_id>/evidence/gallery/', views_new.evidence_gallery, name='evidence_gallery'),
    
    # Attestation Routes - Gap 10
    path('assignments/<int:access_id>/attest/', views_new.attest_access, name='attest_access'),
    
    # Access Revocation Routes - Gap 5
    path('assignments/<int:access_id>/revoke/', views_new.revoke_access_view, name='revoke_access'),
    path('assignments/<int:access_id>/revoke/confirm/', views_new.revoke_access_confirm, name='revoke_access_confirm'),
    path('assignments/<int:access_id>/activate/', views_new.activate_access_view, name='activate_access'),
    path('assignments/<int:access_id>/activate/confirm/', views_new.activate_access_confirm, name='activate_access_confirm'),
]
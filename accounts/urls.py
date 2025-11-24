from django.urls import path
from django.contrib.auth import views as auth_views
from . import views, test_auth

app_name = 'accounts'

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('test/', test_auth.test_login, name='test_login'),
    path('test/protected/', test_auth.test_protected, name='test_protected'),
    path('users/', views.user_list, name='user_list'),
    path('users/export/excel/', views.user_export_excel, name='user_export_excel'),
    path('users/export/pdf/', views.user_export_pdf, name='user_export_pdf'),
    path('users/bulk-action/', views.user_bulk_action, name='user_bulk_action'),
    path('users/<int:pk>/assign-department/', views.user_assign_department, name='user_assign_department'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/toggle-follow-up/', views.user_toggle_follow_up, name='user_toggle_follow_up'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/photo/update/', views.user_photo_update, name='user_photo_update'),
    path('users/<int:pk>/photo/delete/', views.user_photo_delete, name='user_photo_delete'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/reset-password/', views.user_reset_password, name='user_reset_password'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/permissions/', views.user_manage_permissions, name='user_manage_permissions'),
    path('audit/deactivations/', views.user_deactivation_audit_list, name='user_deactivation_audit_list'),
    path('audit/deactivations/<int:pk>/', views.user_deactivation_audit_detail, name='user_deactivation_audit_detail'),
    path('audit/deactivations/export/excel/', views.user_deactivation_audit_export_excel, name='user_deactivation_audit_export_excel'),
    path('audit/deactivations/export/pdf/', views.user_deactivation_audit_export_pdf, name='user_deactivation_audit_export_pdf'),
    path('audit/archives/', views.user_archive_list, name='user_archive_list'),
    path('audit/archives/<int:pk>/', views.user_archive_detail, name='user_archive_detail'),
    path('audit/archives/export/excel/', views.user_archive_export_excel, name='user_archive_export_excel'),
    path('audit/archives/export/pdf/', views.user_archive_export_pdf, name='user_archive_export_pdf'),
]
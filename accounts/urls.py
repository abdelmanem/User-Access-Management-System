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
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]
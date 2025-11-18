from django.urls import path

from . import views

app_name = 'default_accounts'

urlpatterns = [
    path('', views.default_account_dashboard, name='default_account_dashboard'),
    path('create/', views.default_account_create, name='default_account_create'),
    path('export/', views.default_account_export, name='default_account_export'),
    path('templates/', views.default_account_template_list, name='default_account_templates'),
    path('seed/system/<int:system_id>/', views.seed_defaults_for_system, name='seed_defaults_for_system'),
    path('<int:pk>/', views.default_account_detail, name='default_account_detail'),
    path('<int:pk>/update/', views.default_account_update, name='default_account_update'),
    path('<int:pk>/delete/', views.default_account_delete, name='default_account_delete'),
    path('<int:pk>/log-action/', views.default_account_log_action, name='default_account_log_action'),
]


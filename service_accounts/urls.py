from django.urls import path
from . import views

app_name = 'service_accounts'

urlpatterns = [
    # Service Account Management
    path('', views.service_account_list, name='service_account_list'),
    path('create/', views.service_account_create, name='service_account_create'),
    path('<int:pk>/', views.service_account_detail, name='service_account_detail'),
    path('<int:pk>/update/', views.service_account_update, name='service_account_update'),
    path('<int:pk>/delete/', views.service_account_delete, name='service_account_delete'),
    
    # Password History
    path('<int:pk>/password-history/add/', views.service_account_password_history_add, name='service_account_password_history_add'),
    
    # Reports
    path('compliance-report/', views.service_account_compliance_report, name='service_account_compliance_report'),
    path('export/', views.export_service_accounts_to_excel, name='export_service_accounts'),
]


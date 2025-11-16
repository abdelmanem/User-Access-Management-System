from django.urls import path
from . import views

app_name = 'data_import_export'

urlpatterns = [
    path('', views.data_import_export_home, name='home'),
    path('custom-export/', views.custom_export, name='custom_export'),
    path('export/users/', views.export_users, name='export_users'),
    path('export/departments/', views.export_departments, name='export_departments'),
    path('export/systems/', views.export_systems, name='export_systems'),
    path('export/hardware/', views.export_hardware, name='export_hardware'),
    path('export/access-assignments/', views.export_access_assignments, name='export_access_assignments'),
    path('export/access-history/', views.export_access_history, name='export_access_history'),
    path('import/users/', views.import_users, name='import_users'),
    path('import/departments/', views.import_departments, name='import_departments'),
    path('import/systems/', views.import_systems, name='import_systems'),
    path('import/hardware/', views.import_hardware, name='import_hardware'),
]
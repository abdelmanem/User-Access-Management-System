from django.urls import path
from . import views

app_name = 'systems'

urlpatterns = [
    path('', views.system_list, name='system_list'),
    path('create/', views.system_create, name='system_create'),
    path('types/', views.system_type_management, name='system_type_management'),
    path('notifications/', views.system_notifications, name='system_notifications'),
    path('<int:pk>/contract/', views.system_contract_edit, name='system_contract_edit'),
    path('<int:pk>/', views.system_detail, name='system_detail'),
    path('<int:pk>/update/', views.system_update, name='system_update'),
    path('<int:pk>/delete/', views.system_delete, name='system_delete'),
]
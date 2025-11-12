from django.urls import path

from . import views

app_name = "hardware"

urlpatterns = [
    path("", views.hardware_list, name="hardware_list"),
    path("create/", views.hardware_create, name="hardware_create"),
    path("<int:pk>/", views.hardware_detail, name="hardware_detail"),
    path("<int:pk>/edit/", views.hardware_update, name="hardware_update"),
    path("<int:pk>/delete/", views.hardware_delete, name="hardware_delete"),
]


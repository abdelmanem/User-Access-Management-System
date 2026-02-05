from django.urls import path

from . import views

app_name = "hardware"

urlpatterns = [
    # Hardware Asset URLs
    path("", views.hardware_list, name="hardware_list"),
    path("create/", views.hardware_create, name="hardware_create"),
    path("<int:pk>/", views.hardware_detail, name="hardware_detail"),
    path("<int:pk>/edit/", views.hardware_update, name="hardware_update"),
    path("<int:pk>/delete/", views.hardware_delete, name="hardware_delete"),

    # Accessory URLs
    path("accessories/", views.accessory_list, name="accessory_list"),
    path("accessories/create/", views.accessory_create, name="accessory_create"),
    path("accessories/<int:pk>/", views.accessory_detail, name="accessory_detail"),
    path("accessories/<int:pk>/edit/", views.accessory_update, name="accessory_update"),
    path("accessories/<int:pk>/delete/", views.accessory_delete, name="accessory_delete"),

    # Related Asset (Assignment) URLs
    path("assignments/create/", views.related_asset_create, name="related_asset_create"),
    path("assignments/<int:pk>/", views.related_asset_detail, name="related_asset_detail"),
    path("assignments/<int:pk>/edit/", views.related_asset_update, name="related_asset_update"),
    path("assignments/<int:pk>/delete/", views.related_asset_delete, name="related_asset_delete"),
]


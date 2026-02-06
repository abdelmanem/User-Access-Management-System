from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "change_management"

# REST API router
router = DefaultRouter()
router.register(r'requests', views.AccountChangeRequestViewSet, basename='api-change-request')

urlpatterns = [
    # Web UI endpoints
    path("requests/", views.change_request_list, name="change_request_list"),
    path("requests/create/", views.change_request_create, name="change_request_create"),
    path("requests/<int:pk>/", views.change_request_detail, name="change_request_detail"),
    path("requests/<int:pk>/update/", views.change_request_update, name="change_request_update"),
    
    # REST API endpoints
    path("api/", include(router.urls)),
]



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
    path("requests/<int:pk>/quick-approve/", views.change_request_quick_approve, name="change_request_quick_approve"),
    path("requests/<int:pk>/quick-reject/", views.change_request_quick_reject, name="change_request_quick_reject"),
    
    # REST API endpoints
    path("api/", include(router.urls)),
]



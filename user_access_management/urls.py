"""
URL configuration for user_access_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from dashboard.admin import dashboard_admin_site
from django.http import JsonResponse
from django.db import connection

# Use the shared admin site instance
admin_site = dashboard_admin_site

urlpatterns = [
    path('dashboard/', include('dashboard.urls')),
    path('admin/', admin_site.urls),
    path('', include('accounts.urls')),
    path('departments/', include('departments.urls')),
    path('systems/', include('systems.urls')),
    path('access-management/', include('access_management.urls')),
    path('search/', include('search.urls')),
    path('data-import-export/', include('data_import_export.urls')),
    path('healthz/', lambda request: JsonResponse({
        'status': 'ok',
        'db': True if connection.cursor() else False
    })),
]

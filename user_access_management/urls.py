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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from dashboard.admin import dashboard_admin_site
from django.http import JsonResponse, FileResponse, Http404, HttpResponseRedirect
from django.db import connection
from django.views.static import serve
from pathlib import Path
import os


def serve_docs(request, path):
    """Serve documentation files, handling directory indexes by serving index.html"""
    site_dir = settings.BASE_DIR / 'site'
    
    # Normalize the path - remove leading/trailing slashes
    clean_path = path.strip('/')
    file_path = site_dir / clean_path if clean_path else site_dir
    
    # If path is empty, ends with /, or points to a directory, serve index.html
    if not clean_path or path.endswith('/') or (file_path.exists() and file_path.is_dir()):
        # Try to serve index.html from this directory
        if clean_path:
            index_path = f"{clean_path}/index.html"
        else:
            index_path = "index.html"
        file_path = site_dir / index_path
    else:
        # Try to serve the file directly
        file_path = site_dir / clean_path
    
    # If file doesn't exist, try as a directory with index.html
    if not file_path.exists() and clean_path:
        file_path = site_dir / clean_path / "index.html"
    
    if not file_path.exists():
        raise Http404("Documentation file not found")
    
    # Get the relative path for serve()
    relative_path = str(file_path.relative_to(site_dir))
    return serve(request, relative_path, document_root=str(site_dir))

# Use the shared admin site instance
admin_site = dashboard_admin_site

urlpatterns = [
    path('dashboard/', include('dashboard.urls')),
    path('admin/', admin_site.urls),
    path('', include('accounts.urls')),
    path('departments/', include('departments.urls')),
    path('systems/', include('systems.urls')),
    path('access-management/', include('access_management.urls')),
    path('change-management/', include('change_management.urls')),
    path('hardware/', include('hardware.urls')),
    path('service-accounts/', include('service_accounts.urls')),
    path('default-accounts/', include('default_accounts.urls')),
    path('search/', include('search.urls')),
    path('data-import-export/', include('data_import_export.urls')),
    path('healthz/', lambda request: JsonResponse({
        'status': 'ok',
        'db': True if connection.cursor() else False
    })),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Serve documentation site
    site_dir = settings.BASE_DIR / 'site'
    if site_dir.exists():
        # Redirect /site and /site/ to the first documentation page (USER_GUIDE)
        urlpatterns += [
            path('site', lambda request: HttpResponseRedirect('/site/USER_GUIDE/')),
            path('site/', lambda request: HttpResponseRedirect('/site/USER_GUIDE/')),
            re_path(r'^site/(?P<path>.*)$', serve_docs),
        ]

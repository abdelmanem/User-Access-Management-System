from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth import authenticate, login
from django.contrib.auth.backends import ModelBackend
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.http import url_has_allowed_host_and_scheme
from . import views, test_auth, ldap_views
from .models import LDAPConfiguration
from .ldap_backend import LDAPAuthenticationBackend

app_name = 'accounts'

# Custom LoginView with cache control headers
class CustomLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        # Clear any stale session data if user is not authenticated
        if not self.request.user.is_authenticated:
            self.request.session.flush()
        response = super().dispatch(*args, **kwargs)
        # Add cache-control headers to prevent browser caching
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if LDAP is enabled
        ldap_config = LDAPConfiguration.get_active_config()
        context['ldap_enabled'] = ldap_config is not None and ldap_config.ldap_enabled
        return context
    
    def form_valid(self, form):
        import logging
        logger = logging.getLogger(__name__)
        
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        auth_method = self.request.POST.get('auth_method', 'auto')  # 'auto', 'ldap', or 'django'
        remember_me = self.request.POST.get('remember_me') == 'on'
        
        user = None
        error_message = 'Invalid username or password.'
        
        # Determine which backend to use
        try:
            if auth_method == 'ldap':
                # Try LDAP only
                logger.info(f"Attempting LDAP authentication for user: {username}")
                ldap_backend = LDAPAuthenticationBackend()
                user = ldap_backend.authenticate(self.request, username=username, password=password)
                if user is None:
                    logger.warning(f"LDAP authentication failed for user: {username}")
                    error_message = 'LDAP authentication failed. Please check your username and password, or try "Auto" authentication method.'
                elif not user.is_active:
                    logger.warning(f"LDAP user {username} is inactive")
                    error_message = 'Your account is inactive. Please contact your administrator.'
                    user = None
            elif auth_method == 'django':
                # Try Django DB only
                logger.info(f"Attempting Django DB authentication for user: {username}")
                django_backend = ModelBackend()
                user = django_backend.authenticate(self.request, username=username, password=password)
                if user is None:
                    logger.warning(f"Django DB authentication failed for user: {username}")
                    error_message = 'Django DB authentication failed. Please check your username and password.'
                elif not user.is_active:
                    logger.warning(f"Django user {username} is inactive")
                    error_message = 'Your account is inactive. Please contact your administrator.'
                    user = None
            else:
                # Auto: try both (default Django behavior)
                logger.info(f"Attempting auto authentication for user: {username}")
                user = authenticate(self.request, username=username, password=password)
                if user is None:
                    logger.warning(f"Auto authentication failed for user: {username}")
                    error_message = 'Authentication failed. Please check your username and password.'
                elif not user.is_active:
                    logger.warning(f"User {username} is inactive")
                    error_message = 'Your account is inactive. Please contact your administrator.'
                    user = None
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {str(e)}", exc_info=True)
            error_message = f'An error occurred during authentication: {str(e)}'
        
        if user is not None:
            login(self.request, user)
            logger.info(f"User {username} successfully logged in using {auth_method} method")
            
            # Handle remember me checkbox
            if remember_me:
                # Set session to expire after a longer period (e.g., 2 weeks)
                self.request.session.set_expiry(1209600)  # 2 weeks in seconds
                # Also set session cookie to persist
                self.request.session.modified = True
            else:
                # Use default session expiry (browser close or configured timeout)
                self.request.session.set_expiry(None)
            
            redirect_to = self.request.POST.get('next', self.request.GET.get('next', ''))
            if redirect_to:
                # Security check
                if url_has_allowed_host_and_scheme(redirect_to, allowed_hosts=self.request.get_host()):
                    return HttpResponseRedirect(redirect_to)
            return HttpResponseRedirect(self.get_success_url())
        else:
            # Authentication failed
            form.add_error(None, error_message)
            return self.form_invalid(form)

urlpatterns = [
    path('', CustomLoginView.as_view(), name='login'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('test/', test_auth.test_login, name='test_login'),
    path('test/protected/', test_auth.test_protected, name='test_protected'),
    path('users/', views.user_list, name='user_list'),
    path('users/export/excel/', views.user_export_excel, name='user_export_excel'),
    path('users/export/pdf/', views.user_export_pdf, name='user_export_pdf'),
    path('users/bulk-action/', views.user_bulk_action, name='user_bulk_action'),
    path('users/<int:pk>/assign-department/', views.user_assign_department, name='user_assign_department'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/toggle-follow-up/', views.user_toggle_follow_up, name='user_toggle_follow_up'),
    path('users/<int:pk>/toggle-metrics/', views.user_toggle_metrics, name='user_toggle_metrics'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/photo/update/', views.user_photo_update, name='user_photo_update'),
    path('users/<int:pk>/photo/delete/', views.user_photo_delete, name='user_photo_delete'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('users/<int:pk>/reset-password/', views.user_reset_password, name='user_reset_password'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:pk>/permissions/', views.user_manage_permissions, name='user_manage_permissions'),
    path('audit/deactivations/', views.user_deactivation_audit_list, name='user_deactivation_audit_list'),
    path('audit/deactivations/<int:pk>/', views.user_deactivation_audit_detail, name='user_deactivation_audit_detail'),
    path('audit/deactivations/export/excel/', views.user_deactivation_audit_export_excel, name='user_deactivation_audit_export_excel'),
    path('audit/deactivations/export/pdf/', views.user_deactivation_audit_export_pdf, name='user_deactivation_audit_export_pdf'),
    path('audit/archives/', views.user_archive_list, name='user_archive_list'),
    path('audit/archives/<int:pk>/', views.user_archive_detail, name='user_archive_detail'),
    path('audit/archives/export/excel/', views.user_archive_export_excel, name='user_archive_export_excel'),
    path('audit/archives/export/pdf/', views.user_archive_export_pdf, name='user_archive_export_pdf'),
    # LDAP/AD Configuration
    path('ldap/configuration/', ldap_views.ldap_configuration, name='ldap_configuration'),
    path('ldap/configuration/list/', ldap_views.ldap_configuration_list, name='ldap_configuration_list'),
    path('ldap/test-connection/', ldap_views.ldap_test_connection, name='ldap_test_connection'),
    path('ldap/test-login/', ldap_views.ldap_test_login, name='ldap_test_login'),
    path('ldap/sync-users/', ldap_views.ldap_sync_users, name='ldap_sync_users'),
]
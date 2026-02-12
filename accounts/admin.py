from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django import forms
from django.utils.html import format_html
from .models import CustomUser, UserDeactivationAudit, UserArchive, LDAPConfiguration
from dashboard.admin import dashboard_admin_site


class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name')


class CustomUserAdmin(BaseUserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    
    # List display configuration
    list_display = [
        'username', 'full_name', 'employee_id', 'department', 'position',
        'employment_status', 'is_active', 'flag_for_follow_up', 'exclude_from_metrics',
        'exclude_from_ldap_sync', 'created_at', 'last_login'
    ]
    
    list_filter = [
        'is_active', 'flag_for_follow_up', 'exclude_from_metrics', 'exclude_from_ldap_sync',
        'employment_status', 'department', 'employment_type',
        'is_staff', 'is_superuser', 'created_at', 'last_login'
    ]
    
    search_fields = [
        'username', 'first_name', 'last_name', 'email', 'employee_id',
        'national_id', 'phone_primary', 'position'
    ]
    
    ordering = ['-created_at']
    
    readonly_fields = [
        'created_at', 'updated_at', 'last_login', 'date_joined',
        'created_by', 'updated_by', 'profile_photo_preview'
    ]
    
    # Fieldsets for the change form
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': (
                'first_name', 'last_name', 'email', 'personal_email',
                'phone_primary', 'phone_secondary', 'date_of_birth',
                'nationality', 'national_id', 'passport_number'
            )
        }),
        ('Employment Information', {
            'fields': (
                'employee_id', 'employment_type', 'position', 'job_title',
                'department', 'reports_to', 'join_date', 'employment_status'
            )
        }),
        ('Location & Contact', {
            'fields': (
                'office_location', 'work_location', 'address',
                'emergency_contact_name', 'emergency_contact_phone'
            )
        }),
        ('Profile & Media', {
            'fields': ('profile_photo', 'profile_photo_preview')
        }),
        ('Monitoring & Metrics', {
            'fields': ('flag_for_follow_up', 'exclude_from_metrics', 'exclude_from_ldap_sync')
        }),
        ('AD Integration', {
            'fields': (
                'ad_username', 'ad_domain', 'ad_last_sync',
                'ad_guid', 'ad_disabled'
            ),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'groups',
                'user_permissions'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'exit_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    # Fieldsets for the add form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'password1', 'password2'
            ),
        }),
    )
    
    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" width="150" height="150" style="object-fit: cover;" />',
                obj.profile_photo.url
            )
        return "No photo"
    profile_photo_preview.short_description = 'Profile Photo Preview'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new user
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Unregister from default admin if registered, then register with custom admin site
if admin.site.is_registered(CustomUser):
    admin.site.unregister(CustomUser)

# Register with the custom admin site
dashboard_admin_site.register(CustomUser, CustomUserAdmin)


class UserDeactivationAuditAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'user_full_name',
        'user_employee_id',
        'admin',
        'deactivated_at',
        'system_confirmed',
        'hardware_confirmed',
        'hardware_status_action',
    )
    list_filter = ('hardware_status_action', 'system_confirmed', 'hardware_confirmed', 'deactivated_at')
    search_fields = ('user_username', 'user_full_name', 'user_employee_id', 'admin__username')
    readonly_fields = (
        'user',
        'user_username',
        'user_full_name',
        'user_employee_id',
        'admin',
        'deactivated_at',
        'system_confirmed',
        'hardware_confirmed',
        'hardware_status_action',
        'system_assignments',
        'hardware_assignments',
        'notes',
    )
    ordering = ['-deactivated_at']


class UserArchiveAdmin(admin.ModelAdmin):
    list_display = ('username', 'employee_id', 'department_name', 'archived_at', 'archived_by', 'exclude_from_ldap_sync')
    list_filter = ('archived_at', 'department_name', 'exclude_from_ldap_sync')
    search_fields = ('username', 'employee_id', 'full_name', 'department_name')
    readonly_fields = (
        'source_user_id',
        'username',
        'full_name',
        'employee_id',
        'email',
        'department_name',
        'archived_by',
        'archived_at',
        'payload',
    )
    fieldsets = (
        ('Archive Information', {
            'fields': ('source_user_id', 'username', 'full_name', 'employee_id', 'email', 'department_name', 'archived_by', 'archived_at')
        }),
        ('LDAP Sync Control', {
            'fields': ('exclude_from_ldap_sync',),
            'description': 'Controls whether this archived user will be re-synced from LDAP. Set to True to prevent this user from being recreated during LDAP sync.'
        }),
        ('Archive Payload', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-archived_at']


dashboard_admin_site.register(UserDeactivationAudit, UserDeactivationAuditAdmin)
dashboard_admin_site.register(UserArchive, UserArchiveAdmin)


class LDAPConfigurationAdmin(admin.ModelAdmin):
    """
    Admin interface for LDAP Configuration
    """
    list_display = (
        'ldap_server',
        'ldap_enabled',
        'is_active_directory',
        'cache_passwords',
        'updated_at',
        'updated_by',
    )
    list_filter = ('ldap_enabled', 'is_active_directory', 'cache_passwords', 'use_tls', 'allow_invalid_ssl')
    search_fields = ('ldap_server', 'base_dn', 'bind_username', 'ad_domain')
    readonly_fields = ('created_at', 'updated_at', 'updated_by')
    
    fieldsets = (
        ('Server Settings', {
            'fields': (
                'ldap_enabled',
                'is_active_directory',
                'cache_passwords',
                'ad_domain',
            )
        }),
        ('TLS/SSL Configuration', {
            'fields': (
                'ldap_client_tls_key',
                'ldap_client_tls_cert',
                'ldap_server',
                'use_tls',
                'allow_invalid_ssl',
            )
        }),
        ('Bind Settings', {
            'fields': (
                'bind_username',
                'base_dn',
            )
        }),
        ('Search and Authentication', {
            'fields': (
                'ldap_filter',
                'ldap_auth_query',
                'default_permission_group',
            )
        }),
        ('Field Mapping - Basic', {
            'fields': (
                'ldap_username_field',
                'ldap_firstname_field',
                'ldap_lastname_field',
                'ldap_displayname_field',
                'ldap_email_field',
            )
        }),
        ('Field Mapping - Extended', {
            'fields': (
                'ldap_employeenumber_field',
                'ldap_department_field',
                'ldap_manager_field',
                'ldap_phone_field',
                'ldap_mobile_field',
                'ldap_jobtitle_field',
            ),
            'classes': ('collapse',)
        }),
        ('Field Mapping - Location', {
            'fields': (
                'ldap_address_field',
                'ldap_city_field',
                'ldap_state_field',
                'ldap_postalcode_field',
                'ldap_country_field',
                'ldap_location_field',
            ),
            'classes': ('collapse',)
        }),
        ('Active Flag Settings', {
            'fields': (
                'ldap_active_flag',
                'ldap_invert_active_flag',
            )
        }),
        ('Miscellaneous', {
            'fields': (
                'custom_password_reset_url',
            )
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of LDAP configurations
        return False


dashboard_admin_site.register(LDAPConfiguration, LDAPConfigurationAdmin)

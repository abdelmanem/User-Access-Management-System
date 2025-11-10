from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import UserSystemAccess, AccessHistory


@admin.register(UserSystemAccess)
class UserSystemAccessAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'system_link', 'access_type', 'status',
        'priority_badge', 'request_type', 'approved_by_link',
        'access_start_date', 'access_end_date', 'created_at'
    ]
    
    list_filter = [
        'status', 'access_type', 'request_type', 'priority',
        'created_at', 'updated_at'
    ]
    
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'user__employee_id', 'system__name', 'system__code',
        'justification', 'access_username', 'approved_by__first_name',
        'approved_by__last_name'
    ]
    
    ordering = ['-created_at']
    
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'status_badge', 'priority_badge', 'user_link', 'system_link',
        'approved_by_link', 'access_duration_display'
    ]
    
    fieldsets = (
        ('Request Information', {
            'fields': (
                'user_link', 'system_link', 'access_type', 'request_type',
                'priority_badge', 'justification'
            )
        }),
        ('Status & Approval', {
            'fields': (
                'status_badge', 'approved_by_link', 'approval_date',
                'rejection_reason'
            )
        }),
        ('Access Details', {
            'fields': (
                'access_username', 'access_password', 'access_url',
                'access_instructions'
            )
        }),
        ('Time-based Access', {
            'fields': (
                'access_start_date', 'access_end_date', 'access_duration_display'
            )
        }),
        ('Review & Audit', {
            'fields': (
                'last_review_date', 'next_review_date', 'review_notes',
                'security_clearance_level'
            )
        }),
        ('Security & Compliance', {
            'fields': (
                'multi_factor_enabled', 'ip_restriction_enabled',
                'last_password_change', 'failed_login_attempts'
            )
        }),
        ('Notifications', {
            'fields': (
                'notification_enabled', 'notification_email',
                'notification_frequency'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at', 'updated_at', 'created_by', 'updated_by'
            ),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        if obj and obj.user:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse('admin:accounts_customuser_change', args=[obj.user.id]),
                f"{obj.user.get_full_name()} ({obj.user.username})"
            )
        return "No user"
    user_link.short_description = 'User'
    
    def system_link(self, obj):
        if obj and obj.system:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse('admin:systems_system_change', args=[obj.system.id]),
                obj.system.name
            )
        return "No system"
    system_link.short_description = 'System'
    
    def approved_by_link(self, obj):
        if obj and obj.approved_by:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse('admin:accounts_customuser_change', args=[obj.approved_by.id]),
                obj.approved_by.get_full_name()
            )
        return "Not approved"
    approved_by_link.short_description = 'Approved By'
    
    def status_badge(self, obj):
        if obj:
            colors = {
                'pending': '#ffc107',
                'approved': '#28a745',
                'rejected': '#dc3545',
                'expired': '#6c757d',
                'suspended': '#fd7e14'
            }
            color = colors.get(obj.status, '#6c757d')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 12px;">{}</span>',
                color, obj.status.upper()
            )
        return "-"
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        if obj:
            colors = {
                'low': '#28a745',
                'medium': '#ffc107',
                'high': '#fd7e14',
                'urgent': '#dc3545'
            }
            color = colors.get(obj.priority, '#6c757d')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 12px;">{}</span>',
                color, obj.priority.upper()
            )
        return "-"
    priority_badge.short_description = 'Priority'
    
    def access_duration_display(self, obj):
        if obj and obj.access_start_date and obj.access_end_date:
            duration = obj.access_end_date - obj.access_start_date
            days = duration.days
            if days > 365:
                return f"{days // 365} years, {(days % 365) // 30} months"
            elif days > 30:
                return f"{days // 30} months, {days % 30} days"
            else:
                return f"{days} days"
        return "No duration set"
    access_duration_display.short_description = 'Access Duration'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AccessHistory)
class AccessHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'user_link', 'system_link', 'access_link', 'action_type_display',
        'timestamp_display', 'ip_address', 'success_status', 'session_duration_display'
    ]
    
    list_filter = [
        'success', 'access_level'
    ]
    
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'system__name', 'system__code', 'description', 'ip_address',
        'error_message'
    ]
    

    
    readonly_fields = [
        'user_link', 'system_link', 'access_link', 'success_status',
        'session_duration_display', 'error_display'
    ]
    
    fieldsets = (
        ('Access Information', {
            'fields': (
                'user_link', 'system_link', 'access_link', 'action_type'
            )
        }),
        ('Event Details', {
            'fields': (
                'description', 'timestamp', 'ip_address', 'user_agent'
            )
        }),
        ('Status & Results', {
            'fields': (
                'success_status', 'error_display', 'access_level',
                'session_duration_display'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at', 'metadata_json'
            ),
            'classes': ('collapse',)
        })
    )
    
    def user_link(self, obj):
        if obj and obj.user:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse('admin:accounts_customuser_change', args=[obj.user.id]),
                f"{obj.user.get_full_name()} ({obj.user.username})"
            )
        return "No user"
    user_link.short_description = 'User'
    
    def system_link(self, obj):
        if obj and obj.system:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse('admin:systems_system_change', args=[obj.system.id]),
                obj.system.name
            )
        return "No system"
    system_link.short_description = 'System'
    
    def access_link(self, obj):
        if obj and obj.user_system_access:
            return format_html(
                '<a href="{}" target="_blank">Access #{}</a>',
                reverse('admin:access_management_usersystemaccess_change', args=[obj.user_system_access.id]),
                obj.user_system_access.id
            )
        return "No access record"
    access_link.short_description = 'Access Record'
    
    def success_status(self, obj):
        if obj:
            color = '#28a745' if obj.success else '#dc3545'
            status = 'Success' if obj.success else 'Failed'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, status
            )
        return "-"
    success_status.short_description = 'Status'
    
    def session_duration_display(self, obj):
        if obj and obj.session_duration_seconds:
            minutes = obj.session_duration_seconds // 60
            seconds = obj.session_duration_seconds % 60
            if minutes > 60:
                hours = minutes // 60
                minutes = minutes % 60
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "No duration"
    session_duration_display.short_description = 'Session Duration'
    
    def error_display(self, obj):
        if obj and obj.error_message:
            return format_html(
                '<div style="background-color: #f8d7da; color: #721c24; '
                'padding: 10px; border-radius: 4px; font-family: monospace;">{}</div>',
                obj.error_message
            )
        return "No errors"
    error_display.short_description = 'Error Details'

    def action_type_display(self, obj):
        """Display action type."""
        return obj.action_type
    action_type_display.short_description = 'Action Type'

    def timestamp_display(self, obj):
        """Display timestamp."""
        return obj.timestamp
    timestamp_display.short_description = 'Timestamp'

from django.contrib import admin
from django.utils import timezone

from .models import AccountChangeRequest, ChangeAuditLog
from .admin_actions import (
    approve_change_requests,
    reject_change_requests,
    mark_changes_completed,
)


@admin.register(AccountChangeRequest)
class AccountChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "change_type",
        "user_display",
        "system",
        "status",
        "requested_by",
        "system_owner_approved",
        "completed_in_external_system",
        "created_at",
    )
    list_filter = (
        "change_type",
        "status",
        "system_owner_approved",
        "completed_in_external_system",
        "system",
        "created_at",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__username",
        "system__name",
        "system__code",
        "business_justification",
    )
    readonly_fields = (
        "created_at",
        "system_owner_approval_date",
        "it_approval_date",
        "completed_date",
        "audit_trail_display",
    )
    
    fieldsets = (
        ('Change Information', {
            'fields': (
                'change_type',
                'user',
                'system',
                'business_justification',
                'status',
            )
        }),
        ('Request Details', {
            'fields': (
                'requested_by',
                'created_at',
            ),
            'classes': ('collapse',)
        }),
        ('System Owner Approval', {
            'fields': (
                'system_owner',
                'system_owner_approved',
                'system_owner_approval_date',
                'system_owner_approval_notes',
            )
        }),
        ('IT Approval', {
            'fields': (
                'it_approval',
                'it_approval_date',
            ),
            'classes': ('collapse',)
        }),
        ('Completion', {
            'fields': (
                'completed_in_external_system',
                'completed_date',
            )
        }),
        ('Audit Trail', {
            'fields': ('audit_trail_display',),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        approve_change_requests,
        reject_change_requests,
        mark_changes_completed,
    ]
    
    ordering = ['-created_at']
    
    def user_display(self, obj):
        """Display user with employee ID."""
        if obj.user:
            return f"{obj.user.get_full_name()} ({obj.user.employee_id})"
        return "— Unassigned —"
    user_display.short_description = "User"
    
    def audit_trail_display(self, obj):
        """Display audit trail for this change request."""
        if not obj.pk:
            return "N/A (not saved yet)"
        
        logs = obj.audit_logs.all().order_by('-timestamp')[:10]
        if not logs:
            return "No audit entries"
        
        html = '<table style="width:100%; border-collapse:collapse;">'
        for log in logs:
            user = log.performed_by.username if log.performed_by else "System"
            html += f'<tr><td style="border:1px solid #ddd; padding:5px;">'
            html += f'{log.timestamp.strftime("%Y-%m-%d %H:%M")} - {log.action} by {user}'
            if log.notes:
                html += f' ({log.notes})'
            html += '</td></tr>'
        html += '</table>'
        
        from django.utils.safestring import mark_safe
        return mark_safe(html)
    audit_trail_display.short_description = "Recent Audit Trail"
    
    def save_model(self, request, obj, form, change):
        """Override to track who made changes."""
        if not change:  # New object
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChangeAuditLog)
class ChangeAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for ChangeAuditLog model."""
    
    list_display = (
        'id',
        'change_request_id',
        'action',
        'performed_by',
        'timestamp',
    )
    
    list_filter = (
        'action',
        'timestamp',
        'performed_by',
    )
    
    search_fields = (
        'change_request__id',
        'performed_by__username',
        'notes',
    )
    
    readonly_fields = (
        'change_request',
        'action',
        'performed_by',
        'timestamp',
        'old_values',
        'new_values',
    )
    
    fieldsets = (
        ('Audit Information', {
            'fields': (
                'change_request',
                'action',
                'timestamp',
                'performed_by',
            )
        }),
        ('Changes', {
            'fields': (
                'old_values',
                'new_values',
            ),
            'classes': ('collapse',)
        }),
        ('Additional Details', {
            'fields': (
                'ip_address',
                'user_agent',
                'notes',
            ),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['-timestamp']
    
    def has_add_permission(self, request):
        """Prevent manual creation of audit logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of audit logs."""
        return False



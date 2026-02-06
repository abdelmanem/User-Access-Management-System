"""
Admin integration actions for Change Management.

Provides admin actions for quick approval, rejection, and completion of changes.
"""

from django.contrib import admin
from django.utils import timezone
from .models import AccountChangeRequest


@admin.action(description="Approve selected change requests")
def approve_change_requests(modeladmin, request, queryset):
    """Admin action to approve multiple change requests."""
    updated_count = 0
    for change_request in queryset:
        if change_request.status != AccountChangeRequest.STATUS_APPROVED:
            change_request.status = AccountChangeRequest.STATUS_APPROVED
            change_request.system_owner = request.user
            change_request.system_owner_approved = True
            change_request.system_owner_approval_date = timezone.now()
            change_request.save()
            updated_count += 1
    
    modeladmin.message_user(
        request,
        f"✓ Approved {updated_count} change request(s)"
    )


@admin.action(description="Reject selected change requests")
def reject_change_requests(modeladmin, request, queryset):
    """Admin action to reject multiple change requests."""
    updated_count = 0
    for change_request in queryset:
        if change_request.status != AccountChangeRequest.STATUS_REJECTED:
            change_request.status = AccountChangeRequest.STATUS_REJECTED
            change_request.system_owner = request.user
            change_request.save()
            updated_count += 1
    
    modeladmin.message_user(
        request,
        f"✓ Rejected {updated_count} change request(s)"
    )


@admin.action(description="Mark selected changes as completed")
def mark_changes_completed(modeladmin, request, queryset):
    """Admin action to mark changes as completed."""
    updated_count = 0
    for change_request in queryset:
        if not change_request.completed_in_external_system:
            change_request.status = AccountChangeRequest.STATUS_COMPLETED
            change_request.completed_in_external_system = True
            change_request.completed_date = timezone.now()
            change_request.save()
            updated_count += 1
    
    modeladmin.message_user(
        request,
        f"✓ Marked {updated_count} change(s) as completed"
    )


class AccountChangeRequestAdmin(admin.ModelAdmin):
    """Admin interface for AccountChangeRequest model."""
    
    list_display = [
        'id',
        'change_type',
        'user_display',
        'system',
        'status',
        'system_owner_approved',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'change_type',
        'system',
        'system_owner_approved',
        'created_at',
    ]
    
    search_fields = [
        'user__username',
        'user__first_name',
        'user__last_name',
        'system__name',
        'business_justification',
    ]
    
    readonly_fields = [
        'created_at',
        'system_owner_approval_date',
        'it_approval_date',
        'completed_date',
    ]
    
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
    
    def save_model(self, request, obj, form, change):
        """Override to track who made changes."""
        if not change:  # New object
            obj.requested_by = request.user
        super().save_model(request, obj, form, change)

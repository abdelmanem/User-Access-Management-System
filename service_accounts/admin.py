from django.contrib import admin
from .models import ServiceAccount, ServiceAccountPasswordHistory


@admin.register(ServiceAccount)
class ServiceAccountAdmin(admin.ModelAdmin):
    list_display = [
        'account_name',
        'system',
        'account_type',
        'owner',
        'password_complies_with_policy',
        'password_expires_on',
        'is_active',
        'compliance_status',
        'created_at',
    ]
    list_filter = [
        'account_type',
        'is_active',
        'password_complies_with_policy',
        'system',
        'created_at',
    ]
    search_fields = [
        'account_name',
        'system__name',
        'purpose',
        'notes',
    ]
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('account_name', 'system', 'account_type', 'purpose', 'owner', 'is_active')
        }),
        ('Password & Compliance', {
            'fields': (
                'password_last_changed',
                'password_expires_on',
                'password_complies_with_policy',
                'password_policy_verified_date',
                'password_policy_verified_by',
            )
        }),
        ('Additional Information', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Disable hard delete from admin UI to preserve history."""
        return False

    def delete_model(self, request, obj):
        """When delete is attempted via code, archive instead of hard-delete."""
        obj.is_active = False
        if hasattr(request, 'user'):
            obj.updated_by = request.user
        obj.save()


@admin.register(ServiceAccountPasswordHistory)
class ServiceAccountPasswordHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'service_account',
        'password_changed_date',
        'expires_on',
        'complies_with_policy',
        'changed_by',
        'documented_at',
    ]
    list_filter = [
        'complies_with_policy',
        'password_changed_date',
        'documented_at',
    ]
    search_fields = [
        'service_account__account_name',
        'service_account__system__name',
        'notes',
    ]
    readonly_fields = ['documented_at']
    date_hierarchy = 'password_changed_date'

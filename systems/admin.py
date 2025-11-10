from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import System


@admin.register(System)
class SystemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'system_type', 'system_environment', 'status_color',
        'system_criticality', 'system_owner_link', 'technical_lead_link',
        'vendor', 'created_at'
    ]
    list_filter = [
        'system_type', 'is_active',
        'authentication_type', 'approval_workflow', 'data_classification',
        'compliance_requirements', 'created_at', 'updated_at'
    ]
    
    search_fields = [
        'name', 'code', 'description', 'url', 'ip_address',
        'server_details', 'version', 'vendor', 'vendor_contact_person',
        'vendor_contact_email', 'system_owner__first_name',
        'system_owner__last_name', 'technical_lead__first_name',
        'technical_lead__last_name'
    ]
    
    ordering = ['name']
    
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'status_color', 'criticality_badge', 'uptime_display',
        'access_count_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'code', 'description', 'system_type',
                'environment', 'is_active'
            )
        }),
        ('Technical Details', {
            'fields': (
                'url', 'ip_address', 'server_details', 'version',
                'operating_system', 'database_type'
            )
        }),
        ('Vendor Information', {
            'fields': (
                'vendor', 'vendor_contact_person', 'vendor_contact_email',
                'vendor_contact_phone', 'vendor_support_level'
            )
        }),
        ('Security & Access', {
            'fields': (
                'authentication_type', 'approval_workflow', 'access_instructions',
                'password_policy', 'session_timeout_minutes'
            )
        }),
        ('Risk & Compliance', {
            'fields': (
                'criticality', 'criticality_badge', 'data_classification',
                'compliance_requirements', 'backup_policy', 'disaster_recovery_plan'
            )
        }),
        ('Maintenance', {
            'fields': (
                'maintenance_window', 'last_maintenance_date',
                'next_maintenance_date', 'uptime_display'
            )
        }),
        ('Ownership & Management', {
            'fields': (
                'system_owner_link', 'technical_lead_link', 'access_count_display'
            )
        }),
        ('SLA & Performance', {
            'fields': (
                'sla_availability_percentage', 'sla_response_time_hours',
                'sla_resolution_time_hours'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at', 'updated_at', 'created_by', 'updated_by'
            ),
            'classes': ('collapse',)
        })
    )
    
    def status_color(self, obj):
        if obj and obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">● Active</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">● Inactive</span>'
        )
    status_color.short_description = 'Status'

    def system_environment(self, obj):
        """Display system environment."""
        return obj.environment
    system_environment.short_description = 'Environment'

    def system_criticality(self, obj):
        """Display system criticality."""
        return obj.criticality
    system_criticality.short_description = 'Criticality'
    
    def criticality_badge(self, obj):
        if obj:
            colors = {
                'low': '#28a745',
                'medium': '#ffc107', 
                'high': '#fd7e14',
                'critical': '#dc3545'
            }
            color = colors.get(obj.criticality, '#6c757d')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 2px 8px; '
                'border-radius: 12px; font-size: 12px;">{}</span>',
                color, obj.criticality.upper()
            )
        return "-"
    criticality_badge.short_description = 'Criticality'
    
    def system_owner_link(self, obj):
        if obj and obj.system_owner:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse('admin:accounts_customuser_change', args=[obj.system_owner.id]),
                obj.system_owner.get_full_name()
            )
        return "No owner"
    system_owner_link.short_description = 'System Owner'
    
    def technical_lead_link(self, obj):
        if obj and obj.technical_lead:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse('admin:accounts_customuser_change', args=[obj.technical_lead.id]),
                obj.technical_lead.get_full_name()
            )
        return "No lead"
    technical_lead_link.short_description = 'Technical Lead'
    
    def uptime_display(self, obj):
        if obj:
            return f"{obj.sla_availability_percentage}% (SLA)"
        return "-"
    uptime_display.short_description = 'Uptime'
    
    def access_count_display(self, obj):
        if obj:
            count = obj.get_active_access_count()
            url = reverse('admin:access_management_usersystemaccess_changelist')
            return format_html(
                '<a href="{}?system__id={}&status=approved" target="_blank">{} active users</a>',
                url, obj.id, count
            )
        return "0 users"
    access_count_display.short_description = 'Active Users'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

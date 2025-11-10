from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'code', 'department_type', 'head_name', 'parent_department',
        'member_count_display', 'is_active', 'established_date'
    ]
    
    list_filter = [
        'is_active', 'department_type', 'parent_department',
        'established_date', 'created_at'
    ]
    
    search_fields = [
        'name', 'code', 'description', 'head_of_department__first_name',
        'head_of_department__last_name', 'head_of_department__username',
        'cost_center', 'budget_code'
    ]
    
    ordering = ['name']
    
    readonly_fields = [
        'created_at', 'updated_at', 'created_by', 'updated_by',
        'breadcrumb_path', 'level_display', 'member_count_display',
        'sub_departments_display'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name', 'code', 'description', 'department_type',
                'is_active', 'established_date'
            )
        }),
        ('Hierarchy', {
            'fields': (
                'parent_department', 'breadcrumb_path', 'level_display'
            )
        }),
        ('Management', {
            'fields': (
                'head_of_department', 'member_count_display',
                'sub_departments_display'
            )
        }),
        ('Financial', {
            'fields': (
                'cost_center', 'budget_code', 'annual_budget'
            )
        }),
        ('Location & Contact', {
            'fields': (
                'office_location', 'phone', 'email'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at', 'updated_at', 'created_by', 'updated_by'
            ),
            'classes': ('collapse',)
        })
    )
    
    def breadcrumb_path(self, obj):
        if obj:
            path = obj.get_full_path()
            return format_html('<div style="font-family: monospace;">{}</div>', path)
        return "-"
    breadcrumb_path.short_description = 'Full Path'
    
    def level_display(self, obj):
        if obj:
            return f"Level {obj.get_level()}"
        return "-"
    level_display.short_description = 'Hierarchy Level'
    
    def member_count_display(self, obj):
        if obj:
            count = obj.get_member_count()
            url = reverse('admin:accounts_customuser_changelist')
            return format_html(
                '<a href="{}?department__id={}" target="_blank">{} members</a>',
                url, obj.id, count
            )
        return "0 members"
    member_count_display.short_description = 'Members'
    
    def sub_departments_display(self, obj):
        if obj:
            sub_depts = obj.get_sub_departments()
            if sub_depts:
                links = []
                for dept in sub_depts[:5]:  # Show first 5 sub-departments
                    url = reverse('admin:departments_department_change', args=[dept.id])
                    links.append(format_html('<a href="{}">{}</a>', url, dept.name))
                
                if len(sub_depts) > 5:
                    links.append(f"... and {len(sub_depts) - 5} more")
                
                return format_html('<br>'.join(links))
            return "No sub-departments"
        return "-"
    sub_departments_display.short_description = 'Sub-departments'
    
    def head_name(self, obj):
        if obj and obj.head_of_department:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                reverse('admin:accounts_customuser_change', args=[obj.head_of_department.id]),
                obj.head_of_department.get_full_name()
            )
        return "No head assigned"
    head_name.short_description = 'Head of Department'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

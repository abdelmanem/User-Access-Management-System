from django.contrib import admin

from .models import (
    DefaultAccount,
    DefaultAccountAction,
    DefaultAccountTemplate,
)


@admin.register(DefaultAccountTemplate)
class DefaultAccountTemplateAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'get_systems_display', 'account_type', 'removal_required', 'applies_to_all')
    search_fields = ('account_name', 'systems__name', 'notes')
    list_filter = ('systems', 'account_type', 'removal_required', 'applies_to_all', 'rhg_special_account')
    
    def get_systems_display(self, obj):
        if obj.systems.exists():
            return ", ".join([s.name for s in obj.systems.all()[:3]])
        elif obj.applies_to_all:
            return "All Systems"
        return "None"
    get_systems_display.short_description = 'Systems'


class DefaultAccountActionInline(admin.TabularInline):
    model = DefaultAccountAction
    extra = 0
    readonly_fields = ('action_type', 'action_date', 'performed_by', 'evidence_reference', 'notes', 'status_applied')


@admin.register(DefaultAccount)
class DefaultAccountAdmin(admin.ModelAdmin):
    list_display = (
        'account_name',
        'system',
        'account_type',
        'status',
        'removal_required',
        'removed_from_external_system',
        'password_changed_in_external_system',
    )
    search_fields = ('account_name', 'system__name', 'remediation_notes', 'password_change_reference', 'removal_reference')
    list_filter = ('account_type', 'status', 'removal_required', 'removed_from_external_system', 'password_changed_in_external_system')
    inlines = [DefaultAccountActionInline]
    autocomplete_fields = ()

from django.contrib import admin

from .models import (
    DefaultAccount,
    DefaultAccountAction,
    DefaultAccountTemplate,
)


@admin.register(DefaultAccountTemplate)
class DefaultAccountTemplateAdmin(admin.ModelAdmin):
    list_display = ('account_name', 'system_type', 'account_type', 'removal_required', 'applies_to_all')
    search_fields = ('account_name', 'system_type', 'notes')
    list_filter = ('system_type', 'account_type', 'removal_required', 'applies_to_all', 'rhg_special_account')


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

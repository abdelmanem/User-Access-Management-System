from django.contrib import admin

from .models import AccountChangeRequest


@admin.register(AccountChangeRequest)
class AccountChangeRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "change_type",
        "user",
        "system",
        "status",
        "requested_by",
        "system_owner",
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
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__username",
        "system__name",
        "system__code",
        "business_justification",
    )
    readonly_fields = ("created_at",)



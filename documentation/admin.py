from django.contrib import admin

from .models import StandardOperatingProcedure


@admin.register(StandardOperatingProcedure)
class StandardOperatingProcedureAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "version",
        "is_active",
        "approved_by",
        "approved_date",
        "created_at",
    )
    list_filter = ("is_active", "approved_by")
    search_fields = ("title", "version", "content")
    readonly_fields = ("created_at",)



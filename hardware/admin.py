from django.contrib import admin
from .models import HardwareAsset


@admin.register(HardwareAsset)
class HardwareAssetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "asset_tag",
        "hardware_type",
        "status",
        "department",
        "primary_user",
        "location",
        "warranty_expiration",
        "is_virtual",
    )
    list_filter = (
        "hardware_type",
        "status",
        "department",
        "is_virtual",
        "requires_patch_management",
    )
    search_fields = (
        "name",
        "asset_tag",
        "serial_number",
        "manufacturer",
        "model_number",
        "mac_address",
        "ip_address",
    )
    filter_horizontal = ("assigned_users", "related_systems")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Identification",
            {
                "fields": (
                    "name",
                    "asset_tag",
                    "serial_number",
                    "hardware_type",
                    "status",
                )
            },
        ),
        (
            "Ownership & Relationships",
            {
                "fields": (
                    "department",
                    "primary_user",
                    "assigned_users",
                    "related_systems",
                )
            },
        ),
        (
            "Specifications",
            {
                "fields": (
                    "manufacturer",
                    "model_number",
                    "operating_system",
                    "cpu",
                    "memory_gb",
                    "storage_capacity_gb",
                    "is_virtual",
                    "requires_patch_management",
                )
            },
        ),
        (
            "Lifecycle & Compliance",
            {
                "fields": (
                    "purchase_date",
                    "warranty_expiration",
                    "end_of_life_date",
                    "last_inventory_check",
                    "next_inventory_check",
                )
            },
        ),
        (
            "Location & Network",
            {
                "fields": (
                    "location",
                    "ip_address",
                    "mac_address",
                )
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",),
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_by",
                    "updated_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

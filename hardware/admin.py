from django.contrib import admin
from .models import HardwareAsset, Accessory, RelatedAsset


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


@admin.register(Accessory)
class AccessoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "asset_tag",
        "accessory_type",
        "status",
        "department",
        "primary_user",
        "warranty_expiration",
    )
    list_filter = (
        "accessory_type",
        "status",
        "department",
        "purchase_date",
    )
    search_fields = (
        "name",
        "asset_tag",
        "serial_number",
        "manufacturer",
        "model_number",
    )
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            "Identification",
            {
                "fields": (
                    "name",
                    "asset_tag",
                    "serial_number",
                    "accessory_type",
                    "status",
                )
            },
        ),
        (
            "Ownership",
            {
                "fields": (
                    "department",
                    "primary_user",
                )
            },
        ),
        (
            "Specifications",
            {
                "fields": (
                    "manufacturer",
                    "model_number",
                )
            },
        ),
        (
            "Lifecycle & Compliance",
            {
                "fields": (
                    "purchase_date",
                    "warranty_expiration",
                )
            },
        ),
        (
            "Location",
            {
                "fields": ("location",)
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",)
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


@admin.register(RelatedAsset)
class RelatedAssetAdmin(admin.ModelAdmin):
    list_display = (
        "get_hardware_name",
        "get_accessory_name",
        "assignment_type",
        "assignment_date",
        "is_currently_assigned",
    )
    list_filter = (
        "assignment_type",
        "assignment_date",
        "hardware_asset__hardware_type",
        "accessory__accessory_type",
    )
    search_fields = (
        "hardware_asset__name",
        "accessory__name",
        "hardware_asset__asset_tag",
        "accessory__asset_tag",
    )
    readonly_fields = ("assignment_date", "created_at", "updated_at")
    fieldsets = (
        (
            "Assignment",
            {
                "fields": (
                    "hardware_asset",
                    "accessory",
                    "assignment_type",
                )
            },
        ),
        (
            "Timeline",
            {
                "fields": (
                    "assignment_date",
                    "removal_date",
                )
            },
        ),
        (
            "Notes",
            {
                "fields": ("notes",)
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "created_by",
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def get_hardware_name(self, obj):
        return obj.hardware_asset.name
    get_hardware_name.short_description = "Hardware Asset"

    def get_accessory_name(self, obj):
        return obj.accessory.name
    get_accessory_name.short_description = "Accessory"

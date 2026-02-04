from django import forms
from .models import HardwareAsset


class HardwareAssetForm(forms.ModelForm):
    class Meta:
        model = HardwareAsset
        fields = [
            "name",
            "asset_tag",
            "local_asset_tag",
            "tm_id",
            "serial_number",
            "hardware_type",
            "status",
            "manufacturer",
            "model_number",
            "operating_system",
            "operating_system_version",
            "cpu",
            "memory_gb",
            "storage_capacity_gb",
            "purchase_date",
            "warranty_expiration",
            "end_of_life_date",
            "location",
            "ip_address",
            "ipv4_address",
            "mac_address",
            "notes",
            "department",
            "primary_user",
            "assigned_users",
            "related_systems",
            "is_virtual",
            "is_enabled",
            "requires_patch_management",
            "last_inventory_check",
            "next_inventory_check",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "warranty_expiration": forms.DateInput(attrs={"type": "date"}),
            "end_of_life_date": forms.DateInput(attrs={"type": "date"}),
            "last_inventory_check": forms.DateInput(attrs={"type": "date"}),
            "next_inventory_check": forms.DateInput(attrs={"type": "date"}),
            "assigned_users": forms.SelectMultiple(attrs={"size": 6}),
            "related_systems": forms.SelectMultiple(attrs={"size": 6}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        primary_user = cleaned_data.get("primary_user")
        assigned_users = cleaned_data.get("assigned_users")

        if primary_user and assigned_users.filter(pk=primary_user.pk).exists():
            self.add_error(
                "assigned_users",
                "Primary user is already selected; remove from additional users.",
            )

        return cleaned_data


from django import forms
from .models import HardwareAsset, Accessory, RelatedAsset


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
            "is_sync_enabled",
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


class AccessoryForm(forms.ModelForm):
    class Meta:
        model = Accessory
        fields = [
            "name",
            "accessory_type",
            "asset_tag",
            "serial_number",
            "status",
            "manufacturer",
            "model_number",
            "purchase_date",
            "warranty_expiration",
            "location",
            "notes",
            "department",
            "primary_user",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "warranty_expiration": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }


class RelatedAssetForm(forms.ModelForm):
    class Meta:
        model = RelatedAsset
        fields = [
            "hardware_asset",
            "accessory",
            "assignment_type",
            "removal_date",
            "notes",
        ]
        widgets = {
            "removal_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean(self):
        """Validate that accessory is not already assigned to another active hardware."""
        cleaned_data = super().clean()
        accessory = cleaned_data.get('accessory')
        removal_date = cleaned_data.get('removal_date')
        
        if accessory and not removal_date:
            # Check if this accessory is already assigned to another hardware without removal date
            existing = RelatedAsset.objects.filter(
                accessory=accessory,
                removal_date__isnull=True
            ).exclude(pk=self.instance.pk)
            
            if existing.exists():
                other_hardware = existing.first().hardware_asset.name
                raise forms.ValidationError(
                    f"❌ This accessory is already assigned to '{other_hardware}'. "
                    f"You can either:\n"
                    f"• Remove it from that hardware first (set removal date)\n"
                    f"• Or set a removal date for this assignment"
                )
        
        return cleaned_data


class BulkAccessoryForm(forms.Form):
    """Form for bulk creating accessories."""
    
    ACCESSORY_TYPE_CHOICES = Accessory.ACCESSORY_TYPE_CHOICES
    STATUS_CHOICES = Accessory.STATUS_CHOICES
    
    bulk_data = forms.CharField(
        widget=forms.Textarea(attrs={
            "rows": 15,
            "placeholder": "Name\tAsset Tag\tType\tManufacturer\tModel\nMonitor 1\tMON-001\tMonitor\tDell\t27\"\nKeyboard 1\tKEY-001\tKeyboard\tLogitech\tK840",
            "style": "font-family: monospace; font-size: 12px;"
        }),
        help_text="Enter accessories as tab-separated values. Headers: Name, Asset Tag, Type, Manufacturer, Model, Serial, Status, Location (optional)"
    )
    
    default_type = forms.ChoiceField(
        choices=ACCESSORY_TYPE_CHOICES,
        initial="Monitor",
        label="Default Type (if not specified)",
        required=False
    )
    
    default_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        initial="In Service",
        label="Default Status (if not specified)",
        required=False
    )
    
    department = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Department (optional)"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from departments.models import Department
        self.fields['department'].queryset = Department.objects.all()
    
    def clean_bulk_data(self):
        bulk_data = self.cleaned_data.get('bulk_data', '').strip()
        if not bulk_data:
            raise forms.ValidationError("Please enter at least one accessory.")
        return bulk_data
    
    def parse_accessories(self):
        """Parse the bulk data and return list of accessories to create."""
        bulk_data = self.cleaned_data.get('bulk_data', '')
        accessories = []
        errors = []
        
        lines = [line.strip() for line in bulk_data.split('\n') if line.strip()]
        
        # Skip header row if it looks like headers
        if lines and lines[0].lower() in ['name\tasset tag\ttype\tmanufacturer\tmodel', 'name\tasset\ttype\tmfg\tmodel']:
            lines = lines[1:]
        
        for idx, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            parts = [p.strip() for p in line.split('\t')]
            
            # Minimum required: Name and Asset Tag
            if len(parts) < 2:
                errors.append(f"Row {idx}: Need at least Name and Asset Tag")
                continue
            
            name = parts[0]
            asset_tag = parts[1]
            accessory_type = parts[2] if len(parts) > 2 and parts[2] else self.cleaned_data.get('default_type', 'Monitor')
            manufacturer = parts[3] if len(parts) > 3 else ""
            model = parts[4] if len(parts) > 4 else ""
            serial = parts[5] if len(parts) > 5 else ""
            status = parts[6] if len(parts) > 6 and parts[6] else self.cleaned_data.get('default_status', 'In Service')
            location = parts[7] if len(parts) > 7 else ""
            
            # Validate type
            if accessory_type not in dict(self.ACCESSORY_TYPE_CHOICES):
                errors.append(f"Row {idx}: Invalid type '{accessory_type}'. Valid types: {', '.join(dict(self.ACCESSORY_TYPE_CHOICES).keys())}")
                continue
            
            # Validate status
            if status not in dict(self.STATUS_CHOICES):
                errors.append(f"Row {idx}: Invalid status '{status}'. Valid statuses: {', '.join(dict(self.STATUS_CHOICES).keys())}")
                continue
            
            # Check for duplicate asset tags in the same batch
            if any(acc['asset_tag'] == asset_tag for acc in accessories):
                errors.append(f"Row {idx}: Duplicate asset tag '{asset_tag}'")
                continue
            
            accessories.append({
                'name': name,
                'asset_tag': asset_tag,
                'accessory_type': accessory_type,
                'manufacturer': manufacturer,
                'model_number': model,
                'serial_number': serial,
                'status': status,
                'location': location,
                'department': self.cleaned_data.get('department'),
            })
        
        if errors:
            error_text = "Errors found:\n" + "\n".join(errors)
            raise forms.ValidationError(error_text)
        
        if not accessories:
            raise forms.ValidationError("No valid accessories found in the data.")
        
        return accessories

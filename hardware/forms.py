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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize the accessory field to display with serial number
        self.fields['accessory'].label_from_instance = lambda obj: (
            f"{obj.name} - {obj.asset_tag} "
            f"(SN: {obj.serial_number if obj.serial_number else 'N/A'})"
        )

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
    """Form for bulk creating accessories with individual fields."""
    
    ACCESSORY_TYPE_CHOICES = Accessory.ACCESSORY_TYPE_CHOICES
    STATUS_CHOICES = Accessory.STATUS_CHOICES
    
    name = forms.CharField(
        max_length=255,
        label="Accessory Name",
        widget=forms.TextInput(attrs={"placeholder": "e.g., Dell 27\" Monitor"})
    )
    
    asset_tag_prefix = forms.CharField(
        max_length=100,
        label="Asset Tag Prefix",
        widget=forms.TextInput(attrs={"placeholder": "e.g., MON", "help_text": "Will auto-generate with numbers"})
    )
    
    asset_tag_start = forms.IntegerField(
        initial=1,
        label="Starting Number",
        widget=forms.NumberInput(attrs={"min": "1", "placeholder": "e.g., 1"})
    )
    
    accessory_type = forms.ChoiceField(
        choices=ACCESSORY_TYPE_CHOICES,
        initial="Monitor",
        label="Type"
    )
    
    manufacturer = forms.CharField(
        max_length=100,
        label="Manufacturer",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g., Dell, Logitech"})
    )
    
    model_number = forms.CharField(
        max_length=100,
        label="Model",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g., 27\", K840"})
    )
    
    serial_number = forms.CharField(
        max_length=100,
        label="Serial Number",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g., ABC123456"})
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        initial="In Service",
        label="Status"
    )
    
    location = forms.CharField(
        max_length=255,
        label="Location",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g., Building A - Floor 2"})
    )
    
    quantity = forms.IntegerField(
        initial=1,
        label="Quantity",
        help_text="How many to create (max 100)",
        widget=forms.NumberInput(attrs={"min": "1", "max": "100"})
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
    
    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity', 1)
        
        if quantity and quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1")
        
        if quantity and quantity > 100:
            raise forms.ValidationError("Quantity cannot exceed 100")
        
        return cleaned_data
    
    def generate_accessories(self):
        """Generate accessories list with auto-incremented asset tags.
        
        Note: serial_number has a UNIQUE constraint, so only the first item
        gets the serial. Remaining items have None (NULL) for serial_number.
        """
        name = self.cleaned_data.get('name')
        prefix = self.cleaned_data.get('asset_tag_prefix')
        start_num = self.cleaned_data.get('asset_tag_start', 1)
        quantity = self.cleaned_data.get('quantity', 1)
        accessory_type = self.cleaned_data.get('accessory_type')
        manufacturer = self.cleaned_data.get('manufacturer', '')
        model = self.cleaned_data.get('model_number', '')
        serial = self.cleaned_data.get('serial_number', '')
        status = self.cleaned_data.get('status')
        location = self.cleaned_data.get('location', '')
        department = self.cleaned_data.get('department')
        
        accessories = []
        
        for i in range(quantity):
            # Generate asset tag: PREFIX-001, PREFIX-002, etc.
            num = start_num + i
            asset_tag = f"{prefix}-{str(num).zfill(3)}"
            
            # Generate name with number suffix if quantity > 1
            item_name = f"{name} {i+1}" if quantity > 1 else name
            
            # Only use serial_number for first item (unique constraint)
            # Use None (NULL) for remaining items, not empty string
            item_serial = serial if i == 0 else None
            
            accessories.append({
                'name': item_name,
                'asset_tag': asset_tag,
                'accessory_type': accessory_type,
                'manufacturer': manufacturer,
                'model_number': model,
                'serial_number': item_serial,
                'status': status,
                'location': location,
                'department': department,
            })
        
        return accessories


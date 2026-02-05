from django.db import models
from django.utils import timezone


class HardwareAsset(models.Model):
    """
    Central hardware inventory model for tracking physical and virtual assets.

    Assets can be linked to departments, systems, and one or more users.
    """

    HARDWARE_TYPE_CHOICES = [
        ("Desktop", "Desktop PC"),
        ("Laptop", "Laptop"),
        ("Server", "Server"),
        ("Virtual Server", "Virtual Server"),
        ("Network Device", "Network Device"),
        ("Peripheral", "Peripheral / Accessory"),
        ("Mobile Device", "Mobile Device / Tablet"),
        ("Storage", "Storage Device"),
        ("Other", "Other"),
    ]

    STATUS_CHOICES = [
        ("In Service", "In Service"),
        ("Provisioning", "Provisioning"),
        ("In Repair", "In Repair"),
        ("In Storage", "In Storage"),
        ("Retired", "Retired"),
        ("Disposed", "Disposed"),
    ]

    tm_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="TM ID for asset tracking (if applicable).",
    )
    local_asset_tag = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Local asset tag or secondary inventory ID.",
    )
    name = models.CharField(
        max_length=255,
        help_text="Friendly asset name (e.g., Finance-SQL01, John Doe Laptop).",
    )
    asset_tag = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique organizational asset tag or inventory ID.",
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Manufacturer serial number (if available).",
    )
    hardware_type = models.CharField(
        max_length=50,
        choices=HARDWARE_TYPE_CHOICES,
        default="Desktop",
        help_text="Primary hardware classification.",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="In Service",
        help_text="Lifecycle status for this asset.",
    )
    manufacturer = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Asset manufacturer/vendor (e.g., Dell, HP, Cisco).",
    )
    model_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Model or SKU identifier.",
    )
    operating_system = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Installed operating system (if applicable).",
    )
    operating_system_version = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Operating system version / build (e.g., 10.0.19045).",
    )
    cpu = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="CPU specification (e.g., Intel i7-1165G7).",
    )
    memory_gb = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Installed memory in GB.",
    )
    storage_capacity_gb = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Total storage capacity in GB.",
    )
    purchase_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date the asset was purchased or leased.",
    )
    warranty_expiration = models.DateField(
        blank=True,
        null=True,
        help_text="Warranty end date.",
    )
    end_of_life_date = models.DateField(
        blank=True,
        null=True,
        help_text="Planned end-of-life date for budgeting/replacement.",
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Physical location (e.g., HQ - 3rd Floor - Rack 4).",
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="Primary IP address assigned to the asset.",
    )
    ipv4_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        help_text="Primary IPv4 address (if available).",
        protocol="IPv4",
    )
    mac_address = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Primary MAC address.",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional comments, configuration details, or history.",
    )

    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        related_name="hardware_assets",
        blank=True,
        null=True,
        help_text="Owning or primary department responsible for this asset.",
    )
    primary_user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        related_name="primary_hardware_assets",
        blank=True,
        null=True,
        help_text="Primary user that the asset is assigned to.",
    )
    assigned_users = models.ManyToManyField(
        "accounts.CustomUser",
        related_name="hardware_assets",
        blank=True,
        help_text="Additional users who use or share this asset.",
    )
    related_systems = models.ManyToManyField(
        "systems.System",
        related_name="hardware_assets",
        blank=True,
        help_text="Systems or applications hosted on or associated with this asset.",
    )

    is_virtual = models.BooleanField(
        default=False,
        help_text="Indicates if the asset is virtualized (VM, container, etc.).",
    )
    is_enabled = models.BooleanField(
        default=True,
        help_text="Indicates if the associated directory/computer account is enabled.",
    )
    requires_patch_management = models.BooleanField(
        default=True,
        help_text="Whether the asset participates in patch management cycles.",
    )
    is_sync_enabled = models.BooleanField(
        default=True,
        help_text="If enabled, LDAP sync will update this asset. Disable to manually manage this asset.",
    )
    last_inventory_check = models.DateField(
        blank=True,
        null=True,
        help_text="Last date the asset was physically verified.",
    )
    next_inventory_check = models.DateField(
        blank=True,
        null=True,
        help_text="Scheduled next verification date.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hardware_created",
    )
    updated_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hardware_updated",
    )

    class Meta:
        verbose_name = "Hardware Asset"
        verbose_name_plural = "Hardware Assets"
        ordering = ["name", "asset_tag"]
        unique_together = [("name", "asset_tag", "tm_id", "local_asset_tag")]

    def __str__(self):
        return f"{self.name} [{self.asset_tag}] (TM ID: {self.tm_id or '-'}, Local Tag: {self.local_asset_tag or '-'})"

    @property
    def is_active_asset(self):
        """Return True if the asset is currently in an active lifecycle state."""
        return self.status in {"In Service", "Provisioning"}

    @property
    def days_until_warranty_expires(self):
        """Return remaining days until warranty expiration."""
        if not self.warranty_expiration:
            return None
        return (self.warranty_expiration - timezone.now().date()).days

    @property
    def lifecycle_state_color(self):
        """Provide a UI-friendly color tag for common statuses."""
        return {
            "In Service": "success",
            "Provisioning": "info",
            "In Repair": "warning",
            "In Storage": "secondary",
            "Retired": "dark",
            "Disposed": "danger",
        }.get(self.status, "secondary")

    def get_primary_user_name(self):
        """Return the name for the primary assigned user."""
        return self.primary_user.full_name if self.primary_user else None

    def get_department_name(self):
        """Return the department name if set."""
        return self.department.name if self.department else None

    def schedule_inventory_check(self, next_date):
        """Convenience method to schedule the next inventory check."""
        self.next_inventory_check = next_date
        self.save(update_fields=["next_inventory_check"])

    @property
    def warranty_overdue_days(self):
        """Return positive integer of overdue days if warranty expired."""
        days = self.days_until_warranty_expires
        if days is None or days >= 0:
            return None
        return abs(days)

    def get_assigned_user_employee_ids(self):
        """Return semicolon-separated list of assigned user employee IDs for exports."""
        return ";".join(
            filter(
                None,
                self.assigned_users.values_list("employee_id", flat=True),
            )
        )

    def get_related_system_codes(self):
        """Return semicolon-separated list of related system codes for exports."""
        return ";".join(
            filter(
                None,
                self.related_systems.values_list("code", flat=True),
            )
        )


class Accessory(models.Model):
    """
    Represents hardware accessories and peripherals like monitors, keyboards, mice, docking stations, etc.
    These can be associated with one or more HardwareAssets.
    """

    ACCESSORY_TYPE_CHOICES = [
        ("Monitor", "Monitor / Display"),
        ("Keyboard", "Keyboard"),
        ("Mouse", "Mouse / Pointing Device"),
        ("Dock", "Docking Station"),
        ("Headset", "Headset / Speakers"),
        ("Printer", "Printer"),
        ("Scanner", "Scanner"),
        ("External Storage", "External Storage / Drive"),
        ("USB Hub", "USB Hub"),
        ("Cable", "Cable / Connector"),
        ("Power Supply", "Power Supply / Adapter"),
        ("Camera", "Webcam / Camera"),
        ("Other", "Other Accessory"),
    ]

    STATUS_CHOICES = [
        ("In Service", "In Service"),
        ("In Repair", "In Repair"),
        ("In Storage", "In Storage"),
        ("Retired", "Retired"),
        ("Disposed", "Disposed"),
    ]

    name = models.CharField(
        max_length=255,
        help_text="Accessory name (e.g., Dell 27-inch Monitor, Logitech MX Master).",
    )
    accessory_type = models.CharField(
        max_length=50,
        choices=ACCESSORY_TYPE_CHOICES,
        default="Monitor",
        help_text="Type of accessory.",
    )
    asset_tag = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique asset tag or inventory ID for this accessory.",
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Manufacturer serial number (if available).",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="In Service",
        help_text="Lifecycle status for this accessory.",
    )
    manufacturer = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Manufacturer/vendor (e.g., Dell, Logitech, HP).",
    )
    model_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Model or SKU identifier.",
    )
    purchase_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date the accessory was purchased or leased.",
    )
    warranty_expiration = models.DateField(
        blank=True,
        null=True,
        help_text="Warranty end date.",
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Physical location (e.g., HQ - 3rd Floor - Desk 12).",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional comments or specifications.",
    )

    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        related_name="accessories",
        blank=True,
        null=True,
        help_text="Department responsible for this accessory.",
    )
    primary_user = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        related_name="primary_accessories",
        blank=True,
        null=True,
        help_text="Primary user assigned to this accessory.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accessories_created",
    )
    updated_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accessories_updated",
    )

    class Meta:
        verbose_name = "Accessory"
        verbose_name_plural = "Accessories"
        ordering = ["name", "asset_tag"]

    def __str__(self):
        return f"{self.name} [{self.asset_tag}]"

    @property
    def is_active_accessory(self):
        """Return True if the accessory is in an active lifecycle state."""
        return self.status == "In Service"

    @property
    def days_until_warranty_expires(self):
        """Return remaining days until warranty expiration."""
        if not self.warranty_expiration:
            return None
        return (self.warranty_expiration - timezone.now().date()).days

    @property
    def warranty_overdue_days(self):
        """Return positive integer of overdue days if warranty expired."""
        days = self.days_until_warranty_expires
        if days is None or days >= 0:
            return None
        return abs(days)

    @property
    def lifecycle_state_color(self):
        """Provide a UI-friendly color tag for common statuses."""
        return {
            "In Service": "success",
            "In Repair": "warning",
            "In Storage": "secondary",
            "Retired": "dark",
            "Disposed": "danger",
        }.get(self.status, "secondary")


class RelatedAsset(models.Model):
    """
    Links accessories (like monitors) to hardware assets (like desktop computers).
    Allows tracking which accessories are assigned to which hardware.
    """

    ASSIGNMENT_TYPE_CHOICES = [
        ("Primary", "Primary Assignment"),
        ("Shared", "Shared / Temporary"),
        ("Backup", "Backup"),
        ("Optional", "Optional / Extra"),
    ]

    hardware_asset = models.ForeignKey(
        HardwareAsset,
        on_delete=models.CASCADE,
        related_name="related_accessories",
        help_text="The hardware asset (e.g., desktop, laptop) this accessory is assigned to.",
    )
    accessory = models.ForeignKey(
        Accessory,
        on_delete=models.CASCADE,
        related_name="hardware_assignments",
        help_text="The accessory (e.g., monitor, keyboard) being assigned.",
    )
    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPE_CHOICES,
        default="Primary",
        help_text="Type of assignment relationship.",
    )
    assignment_date = models.DateField(
        auto_now_add=True,
        help_text="Date the accessory was assigned to this hardware.",
    )
    removal_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date the accessory was removed from this hardware (if applicable).",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional assignment notes or history.",
    )

    created_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_assets_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Related Asset"
        verbose_name_plural = "Related Assets"
        unique_together = [("hardware_asset", "accessory")]
        ordering = ["-assignment_date"]

    def __str__(self):
        return f"{self.hardware_asset.name} ← {self.accessory.name} ({self.assignment_type})"

    @property
    def is_currently_assigned(self):
        """Return True if the accessory is currently assigned (no removal date)."""
        return self.removal_date is None
    def clean(self):
        """Validate that accessory is not already assigned to another active hardware."""
        from django.core.exceptions import ValidationError
        
        if self.accessory and not self.removal_date:
            # Check if this accessory is already assigned to another hardware (without removal date)
            existing = RelatedAsset.objects.filter(
                accessory=self.accessory,
                removal_date__isnull=True
            ).exclude(pk=self.pk)
            
            if existing.exists():
                other_hardware = existing.first().hardware_asset.name
                raise ValidationError(
                    f"This accessory is already assigned to '{other_hardware}'. "
                    f"Please remove it from there first, or set a removal date for this assignment."
                )
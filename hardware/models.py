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
    requires_patch_management = models.BooleanField(
        default=True,
        help_text="Whether the asset participates in patch management cycles.",
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
        unique_together = [("name", "asset_tag")]

    def __str__(self):
        return f"{self.name} [{self.asset_tag}]"

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

# Hardware Accessories & Related Assets Implementation Guide

## Overview

The hardware module has been enhanced to support **Accessories** (like monitors, keyboards, and mice) and **Related Assets** to track relationships between accessories and hardware assets.

## New Models

### 1. **Accessory Model**

The `Accessory` model represents physical peripherals and accessories that can be assigned to hardware assets.

#### Accessory Types Supported:
- Monitor / Display
- Keyboard
- Mouse / Pointing Device
- Docking Station
- Headset / Speakers
- Printer
- Scanner
- External Storage / Drive
- USB Hub
- Cable / Connector
- Power Supply / Adapter
- Webcam / Camera
- Other Accessory

#### Key Fields:
- `name` - Friendly name (e.g., "Dell 27-inch UltraSharp")
- `accessory_type` - Type of accessory
- `asset_tag` - Unique asset tag for tracking
- `serial_number` - Manufacturer serial number
- `status` - Lifecycle status (In Service, In Repair, In Storage, Retired, Disposed)
- `manufacturer` - Manufacturer/vendor
- `model_number` - Model identifier
- `purchase_date` - Purchase date
- `warranty_expiration` - Warranty end date
- `location` - Physical location
- `department` - Owning department
- `primary_user` - Primary user assigned to the accessory
- `notes` - Additional information

#### Status Choices:
- **In Service** - Currently in use
- **In Repair** - Being repaired
- **In Storage** - Stored/not in use
- **Retired** - No longer in use but not disposed
- **Disposed** - Removed from inventory

### 2. **RelatedAsset Model**

The `RelatedAsset` model creates a relationship between `HardwareAsset` and `Accessory`, tracking which accessories are assigned to which hardware.

#### Key Fields:
- `hardware_asset` - The hardware asset (e.g., desktop, laptop)
- `accessory` - The accessory being assigned
- `assignment_type` - Type of assignment relationship
- `assignment_date` - Date assigned (auto-set)
- `removal_date` - Date removed (if applicable)
- `notes` - Assignment-specific notes

#### Assignment Types:
- **Primary** - Primary/permanent assignment
- **Shared** - Shared or temporary assignment
- **Backup** - Backup accessory
- **Optional** - Optional or extra accessory

#### Properties:
- `is_currently_assigned` - Returns True if the accessory is currently assigned (no removal date)

## Database Tables

Two new tables have been created:

1. **hardware_accessory** - Stores accessory inventory
2. **hardware_relatedasset** - Stores accessory-to-hardware relationships

## Admin Interface Features

### Accessory Admin
- List view displaying name, asset tag, type, status, department, user, and warranty
- Filtering by type, status, and department
- Search by name, asset tag, serial number, manufacturer, or model
- Organized fieldsets for easy data entry

### RelatedAsset Admin
- List view showing hardware name, accessory name, assignment type, and assignment date
- Filtering by assignment type, date range, hardware type, and accessory type
- Search by hardware or accessory name or asset tags
- Visual indication of currently assigned accessories

## Usage Examples

### In Django Admin

1. **Adding an Accessory:**
   - Go to Hardware → Accessories → Add Accessory
   - Fill in name, type (e.g., Monitor), asset tag, and other details
   - Save

2. **Assigning an Accessory to Hardware:**
   - Go to Hardware → Related Assets → Add Related Asset
   - Select the hardware asset (e.g., a desktop)
   - Select the accessory (e.g., a monitor)
   - Choose assignment type (Primary, Shared, Backup, or Optional)
   - Set removal date if removing the accessory later
   - Save

3. **Viewing All Accessories for a Hardware:**
   - View a hardware asset detail
   - See all related accessories through the RelatedAsset relationship

### Programmatic Usage

```python
from hardware.models import Accessory, RelatedAsset, HardwareAsset

# Create an accessory
monitor = Accessory.objects.create(
    name="Dell 27-inch UltraSharp",
    accessory_type="Monitor",
    asset_tag="MON-001",
    manufacturer="Dell",
    model_number="U2721D"
)

# Assign accessory to hardware
desktop = HardwareAsset.objects.get(name="John Doe Desktop")
assignment = RelatedAsset.objects.create(
    hardware_asset=desktop,
    accessory=monitor,
    assignment_type="Primary"
)

# Check if accessory is currently assigned
if assignment.is_currently_assigned:
    print(f"{monitor.name} is currently assigned to {desktop.name}")

# Remove accessory from hardware (set removal date)
assignment.removal_date = "2026-02-15"
assignment.save()

# Get all accessories for a hardware asset
accessories = desktop.related_accessories.filter(removal_date__isnull=True)
for rel in accessories:
    print(f"{rel.accessory.name} ({rel.assignment_type})")

# Get all hardware using a specific accessory
hardware_list = monitor.hardware_assignments.filter(removal_date__isnull=True)
for rel in hardware_list:
    print(f"Assigned to: {rel.hardware_asset.name}")
```

## Benefits

1. **Complete Asset Tracking** - Track all peripherals alongside main hardware
2. **Relationship Management** - Understand which accessories go with which hardware
3. **Lifecycle Management** - Track accessory status independently
4. **History Tracking** - Removal dates enable tracking of accessory reassignments
5. **Inventory Control** - Monitor warranty and maintenance schedules for accessories
6. **User Assignment** - Track which user is responsible for each accessory

## Migration Information

- Migration file: `hardware/migrations/0005_accessory_relatedasset.py`
- Created new models: Accessory, RelatedAsset
- No existing data was affected

## Future Enhancements

Consider adding:
- Bulk import/export of accessories
- Accessory templates for common items
- Accessory condition tracking
- Integration with hardware disposal workflows
- Accessory depreciation tracking

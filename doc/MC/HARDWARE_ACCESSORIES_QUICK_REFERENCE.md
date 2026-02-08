# Hardware Accessories - Quick Reference Card

## 📋 What Was Implemented

### ✅ Models (Database)
- **Accessory** - Physical peripherals (monitors, keyboards, etc.)
- **RelatedAsset** - Relationships between accessories and hardware

### ✅ Forms
- **AccessoryForm** - Create/edit accessories
- **RelatedAssetForm** - Assign accessories to hardware

### ✅ Templates (8 Files)
```
📁 hardware/templates/hardware/
├── accessory_list.html              ← List all accessories
├── accessory_detail.html            ← View single accessory
├── accessory_form.html              ← Create/edit form
├── accessory_confirm_delete.html    ← Delete confirmation
├── related_asset_form.html          ← Assign to hardware
├── related_asset_detail.html        ← View assignment
├── related_asset_confirm_delete.html ← Delete confirmation
└── hardware_detail.html             ← UPDATED with accessories
```

### ✅ Admin Interface
- Full Django admin support
- Filtering, searching, bulk operations

---

## 🔗 Relationships

```
Hardware Asset (Desktop/Laptop)
       ↓
   Related Assets (Assignments)
       ↓
   Accessories (Monitor/Keyboard)

Example:
"John's Desktop" → Primary → Dell 27" Monitor
"John's Desktop" → Primary → Logitech Keyboard
"John's Desktop" → Shared → Printer
```

---

## 🎯 Key Features

| Feature | Details |
|---------|---------|
| **13 Accessory Types** | Monitor, Keyboard, Mouse, Dock, Headset, Printer, Scanner, Storage, USB Hub, Cable, Power Supply, Camera, Other |
| **5 Status Options** | In Service, In Repair, In Storage, Retired, Disposed |
| **4 Assignment Types** | Primary, Shared, Backup, Optional |
| **Warranty Tracking** | Purchase date, expiration, countdown |
| **Audit Trail** | Created by/date, updated by/date, removal history |
| **Responsive Design** | Works on desktop, tablet, mobile |

---

## 🚀 Quick Start

### 1. Create an Accessory
```
Go to: Hardware → Accessories → New Accessory
Fill: Name, Type, Asset Tag, Manufacturer, Model
Add: Purchase & Warranty dates
Save: Done!
```

### 2. Assign to Hardware
```
Go to: Hardware Detail → Assigned Accessories → "Assign one"
Select: Hardware asset & Accessory
Choose: Assignment type (Primary/Shared/Backup/Optional)
Save: Complete!
```

### 3. Track It
```
Go to: Hardware → Accessories
Filter: By type or status
Search: By name, tag, serial
View: Details, assignments, warranty info
```

---

## 🗂️ File Locations

```
hardware/
├── models.py                  ← Accessory, RelatedAsset models
├── forms.py                   ← AccessoryForm, RelatedAssetForm
├── admin.py                   ← Admin interfaces
├── views.py                   ← (NEEDS VIEWS TO BE CREATED)
├── urls.py                    ← (NEEDS URL PATTERNS)
└── templates/hardware/
    ├── accessory_list.html
    ├── accessory_detail.html
    ├── accessory_form.html
    ├── accessory_confirm_delete.html
    ├── related_asset_form.html
    ├── related_asset_detail.html
    ├── related_asset_confirm_delete.html
    └── hardware_detail.html  (UPDATED)
```

---

## 📝 Accessory Types

```
Category          | Types
-----------------|------------------------------------------
Display          | Monitor / Display
Input            | Keyboard, Mouse / Pointing Device
Connectivity     | Docking Station, USB Hub, Cable / Connector
Audio            | Headset / Speakers
Peripherals      | Printer, Scanner, Webcam / Camera
Storage          | External Storage / Drive
Power            | Power Supply / Adapter
Other            | Other Accessory
```

---

## 🎨 Status Colors

```
Status                Color    Meaning
────────────────────────────────────────────────────
In Service            Green    Currently in use
In Repair             Orange   Being fixed
In Storage            Gray     Stored, not in use
Retired               Dark     No longer in use
Disposed              Red      Removed from system
```

---

## 🏷️ Assignment Types

```
Type        Color   Meaning
─────────────────────────────────────────────────────
Primary     Green   Permanently assigned
Shared      Blue    Shared or temporary
Backup      Orange  Serves as backup
Optional    Gray    Extra or optional
```

---

## 💾 Database

```
hardware_accessory
├── id, name, asset_tag (unique)
├── accessory_type, status
├── serial_number (unique, optional)
├── manufacturer, model_number
├── purchase_date, warranty_expiration
├── location, notes
├── department (FK)
├── primary_user (FK)
└── created_at, updated_at, created_by, updated_by

hardware_relatedasset
├── id
├── hardware_asset (FK)
├── accessory (FK)
├── assignment_type
├── assignment_date, removal_date
├── notes, created_by
└── UNIQUE(hardware_asset, accessory)
```

---

## ✨ Template Features

### 📊 List View
- Summary cards (Total, In Service, In Storage, Retired)
- Sticky filter bar
- Searchable table
- Sort by any column
- Bulk actions

### 🔍 Detail View
- Two-panel layout
- Left: Main information
- Right: Related items & audit trail
- Edit/Delete buttons
- Linked navigation

### 📋 Forms
- Tabbed organization
- Field grouping by category
- Required field validation
- Inline error messages
- Helper text

### 📱 Responsive
- Mobile-friendly filters
- Collapsible sections
- Readable on all devices
- Touch-friendly buttons

---

## 🔧 TODO: Next Steps

- [ ] Create view functions in `hardware/views.py`
- [ ] Add URL patterns to `hardware/urls.py`
- [ ] Update navigation menu
- [ ] Test end-to-end
- [ ] Add permissions if needed
- [ ] Consider API endpoints

---

## 📚 Documentation Files

1. **HARDWARE_ACCESSORIES_GUIDE.md**
   - Models, fields, methods
   - Database structure
   - Programmatic usage examples

2. **HARDWARE_TEMPLATES_GUIDE.md**
   - Template descriptions
   - Feature details
   - URL routing needed
   - View functions needed

3. **HARDWARE_ACCESSORIES_IMPLEMENTATION_SUMMARY.md**
   - Complete overview
   - File locations
   - Usage workflow
   - Next steps

4. **HARDWARE_ACCESSORIES_QUICK_REFERENCE.md** (This file)
   - Quick reference
   - Visual summaries
   - Getting started

---

## 🎓 Examples

### Python Usage
```python
# Create accessory
monitor = Accessory.objects.create(
    name="Dell 27-inch Monitor",
    accessory_type="Monitor",
    asset_tag="MON-001"
)

# Assign to hardware
desktop = HardwareAsset.objects.get(pk=1)
assignment = RelatedAsset.objects.create(
    hardware_asset=desktop,
    accessory=monitor,
    assignment_type="Primary"
)

# Query
currently_assigned = desktop.related_accessories.filter(removal_date__isnull=True)
```

### Template Usage
```django
<!-- Show accessories in hardware detail -->
{% for rel in asset.related_accessories.all %}
  <div>{{ rel.accessory.name }} - {{ rel.assignment_type }}</div>
{% endfor %}

<!-- Check warranty status -->
{% if accessory.warranty_overdue_days %}
  Warranty expired {{ accessory.warranty_overdue_days }} days ago
{% endif %}
```

---

## 🐛 Troubleshooting

| Error | Solution |
|-------|----------|
| "URL name not found" | Create URL patterns in `urls.py` |
| "View not found" | Create view functions in `views.py` |
| "Template not found" | Check file is in `templates/hardware/` |
| Duplicate asset tags | Asset tags must be unique |
| Assignment errors | Check both hardware_asset and accessory exist |

---

## 📞 Support

- **Models Reference:** HARDWARE_ACCESSORIES_GUIDE.md
- **Templates Guide:** HARDWARE_TEMPLATES_GUIDE.md
- **Full Summary:** HARDWARE_ACCESSORIES_IMPLEMENTATION_SUMMARY.md
- **This File:** HARDWARE_ACCESSORIES_QUICK_REFERENCE.md

---

**Status:** ✅ Implementation Complete - Ready for View/URL/Navigation Setup

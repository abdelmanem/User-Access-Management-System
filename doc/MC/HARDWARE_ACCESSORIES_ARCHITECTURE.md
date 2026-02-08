# Hardware Accessories - Architecture & Data Flow Diagram

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│  (8 HTML Templates - Fully Responsive)                          │
└────────────────┬────────────────────────────────────────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
┌─────────────┐  │  ┌──────────────────┐
│ Accessories │  │  │ Related Assets   │
│    List     │  │  │   (Assignments)  │
│  View/Form  │  │  │   View/Form      │
└─────────────┘  │  └──────────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
┌────────────────────────────────────────┐
│         Django Forms & Views            │
│  (To be created in views.py/urls.py)   │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│         Django ORM Models               │
│  ✅ Accessory Model                    │
│  ✅ RelatedAsset Model                 │
│  ✅ HardwareAsset Model (existing)     │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│         Database (SQLite)               │
│  ✅ hardware_accessory                 │
│  ✅ hardware_relatedasset              │
│  ✅ hardware_hardwareasset (existing)  │
└─────────────────────────────────────────┘
```

---

## 📊 Data Model Relationships

```
EXISTING: HardwareAsset
  ├── id (PK)
  ├── name
  ├── asset_tag
  ├── status
  ├── department (FK → Department)
  ├── primary_user (FK → User)
  └── related_accessories ──┐
                            │
                            ▼ (reverse relation)
                    RelatedAsset (M2M through)
                            │
                    ┌───────┘
                    │
NEW: Accessory ◄───┘
  ├── id (PK)
  ├── name
  ├── accessory_type
  ├── asset_tag
  ├── status
  ├── department (FK → Department)
  ├── primary_user (FK → User)
  └── hardware_assignments (reverse relation)
```

---

## 🔄 Complete Data Flow

### Creating & Managing Accessories

```
STEP 1: Create Accessory
─────────────────────────
User Input
    ↓
Form Validation (AccessoryForm)
    ↓
Create Accessory Object
    ├── name, type, asset_tag
    ├── status, manufacturer, model
    ├── purchase_date, warranty_expiration
    └── department, primary_user
    ↓
Save to Database (hardware_accessory table)
    ↓
Redirect to Detail Page
    ↓
Display Accessory with:
    ├── Specs, warranty info
    ├── All related hardware
    └── Audit trail


STEP 2: Assign to Hardware
──────────────────────────
Select Hardware Asset → Select Accessory → Choose Assignment Type
    ↓
Form Validation (RelatedAssetForm)
    ↓
Create RelatedAsset Object
    ├── hardware_asset (FK)
    ├── accessory (FK)
    ├── assignment_type
    ├── assignment_date (auto)
    └── removal_date (optional)
    ↓
Save to Database (hardware_relatedasset table)
    ↓
Shows in:
    ├── Hardware Detail Page (accessories section)
    ├── Accessory Detail Page (hardware section)
    └── RelatedAsset List (if created)


STEP 3: View & Track
────────────────────
Navigate to:
    ├── Accessories → List all
    ├── Accessories Detail → View one + assignments
    └── Hardware Detail → See assigned accessories

Filter/Search:
    ├── By type (Monitor, Keyboard, etc.)
    ├── By status (In Service, Retired, etc.)
    ├── By text (name, asset tag, serial)
    └── By warranty status

Edit:
    ├── Update accessory specs
    ├── Change assignment type
    ├── Add removal date
    └── Update notes


STEP 4: Remove/Clean Up
──────────────────────
Mark as Removed:
    ├── Set removal_date in RelatedAsset
    ├── Accessory can be reassigned
    └── History preserved

Retire Accessory:
    ├── Change status to "Retired"
    ├── Still tracked in system
    └── Shows in historical queries

Delete Accessory:
    ├── Removes all assignments
    ├── Removes from database
    └── Cannot be undone
```

---

## 🗂️ Template Navigation Map

```
┌──────────────────────────────────────────────────────┐
│              Hardware Inventory                      │
│                Main Navigation                      │
└────────────┬──────────────────────────────────────┬─┘
             │                                      │
             ▼                                      ▼
    Hardware List                        Accessories List
    (existing)                           (NEW)
        │                                    │
        ├─→ Hardware Detail                  ├─→ Accessory Detail
        │   (UPDATED with                    │   (NEW)
        │    Accessories section)            │   └─→ Related Assets
        │                                    │        (assignments)
        └─→ Create/Edit Hardware             │
            (existing)                       ├─→ Accessory Form
                                            │   (Create/Edit)
                                            │
                                            └─→ Related Asset Form
                                                (Assign to hardware)


USER WORKFLOWS
──────────────

Workflow 1: View All Accessories
  Home → Accessories List
    ↓
  [Filter/Search] → View Results Table
    ↓
  Click Accessory → Accessory Detail
    ↓
  [Show Hardware Assignments]


Workflow 2: Create & Assign Accessory
  Home → Accessories List
    ↓
  [New Accessory] → Accessory Form
    ↓
  [Fill Form] → Save
    ↓
  Redirect to Detail
    ↓
  [Go to Hardware] → Select Hardware
    ↓
  [Assign] → Related Asset Form
    ↓
  [Select Accessory] → Save
    ↓
  Appears in Hardware Detail


Workflow 3: Track Assignment
  Home → Hardware List
    ↓
  Click Hardware → Hardware Detail
    ↓
  [Scroll to Accessories Section]
    ↓
  See All Assigned Accessories
    ↓
  [Click Accessory] → Accessory Detail
    ↓
  [View All Hardware Using It]
```

---

## 📈 Request/Response Cycle

```
HTTP Request from Browser
         │
         ▼
    URL Routing (urls.py)
    [To be configured with patterns]
         │
         ▼
    View Function (views.py)
    [To be created]
         │
         ├─→ Query Database (ORM)
         │
         ├─→ Process Data
         │
         ├─→ Apply Filters/Sort
         │
         ├─→ Prepare Context
         │
         ▼
    Render Template (HTML)
    [8 templates prepared ✓]
         │
         ├─→ Inject Data into Template
         │
         ├─→ Apply CSS/Bootstrap Styling
         │
         ├─→ Add JavaScript Interactivity
         │
         ▼
    HTTP Response (HTML)
         │
         ▼
    Browser Renders Page
         │
         ▼
    User Interacts
         │
         └─→ (Cycle Repeats)
```

---

## 🎯 Key Pages & Their Purpose

### Accessory List Page
```
┌─────────────────────────────────────────┐
│  Summary Cards (4 KPIs)                 │
│  ├─ Total Accessories                  │
│  ├─ In Service                         │
│  ├─ In Storage                         │
│  └─ Retired/Disposed                   │
├─────────────────────────────────────────┤
│  Filter & Search Bar (Sticky)          │
│  ├─ Text Search                        │
│  ├─ Type Filter                        │
│  ├─ Status Filter                      │
│  └─ [Apply] [Reset]                    │
├─────────────────────────────────────────┤
│  Accessories Table                      │
│  ├─ Columns: Name, Tag, Serial, Type,  │
│  │            Manufacturer, Status,    │
│  │            User, Warranty, Actions  │
│  ├─ Sortable headers                   │
│  ├─ Responsive design                  │
│  └─ Action buttons (View/Edit/Delete)  │
├─────────────────────────────────────────┤
│  Pagination (if many items)            │
└─────────────────────────────────────────┘
```

### Accessory Detail Page
```
┌─────────────────────────────────────┐   ┌──────────────────────┐
│  Header (Hero Section)              │   │  Right Sidebar       │
│  ├─ Name & Asset Tag                │   │  ┌────────────────┐  │
│  ├─ Status Badge                    │   │  │ Hardware       │  │
│  ├─ Type Badge                      │   │  │ Assignments    │  │
│  └─ Action Buttons                  │   │  │ ┌────────────┐ │  │
├─────────────────────────────────────┤   │  │ │ Hardware 1 │ │  │
│  Left Content Area                  │   │  │ │ Hardware 2 │ │  │
│  ┌─────────────────────────────────┐│   │  │ │ ...        │ │  │
│  │ Accessory Details Card          ││   │  │ └────────────┘ │  │
│  │ ├─ Type                         ││   │  └────────────────┘  │
│  │ ├─ Department                   ││   │                      │
│  │ ├─ Primary User                 ││   │  ┌────────────────┐  │
│  │ ├─ Location                     ││   │  │ Audit Trail    │  │
│  │ ├─ Manufacturer/Model           ││   │  │ ├─ Created     │  │
│  │ ├─ Notes                        ││   │  │ ├─ Updated     │  │
│  │ └─ ...more fields...            ││   │  │ └─ By User     │  │
│  └─────────────────────────────────┘│   │  └────────────────┘  │
│  ┌─────────────────────────────────┐│   │                      │
│  │ Lifecycle Card                  ││   │                      │
│  │ ├─ Purchase Date                ││   │                      │
│  │ └─ Warranty Expiration          ││   │                      │
│  │    └─ Countdown                 ││   │                      │
│  └─────────────────────────────────┘│   │                      │
└─────────────────────────────────────┘   └──────────────────────┘
```

---

## 💾 Database Query Examples

```sql
-- Get all accessories of a specific type
SELECT * FROM hardware_accessory 
WHERE accessory_type = 'Monitor' 
ORDER BY name;

-- Get accessories currently assigned to a hardware
SELECT a.* FROM hardware_accessory a
JOIN hardware_relatedasset r ON a.id = r.accessory_id
WHERE r.hardware_asset_id = 1 
  AND r.removal_date IS NULL;

-- Get all hardware using a specific accessory
SELECT h.* FROM hardware_hardwareasset h
JOIN hardware_relatedasset r ON h.id = r.hardware_asset_id
WHERE r.accessory_id = 5 
  AND r.removal_date IS NULL;

-- Get accessories with expiring warranties
SELECT * FROM hardware_accessory 
WHERE warranty_expiration BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 30 DAY);

-- Get assignment history (including removed)
SELECT r.*, a.name as accessory_name, h.name as hardware_name
FROM hardware_relatedasset r
JOIN hardware_accessory a ON r.accessory_id = a.id
JOIN hardware_hardwareasset h ON r.hardware_asset_id = h.id
ORDER BY r.assignment_date DESC;
```

---

## 🔐 Permissions & Security

```
Expected Permission Model:
─────────────────────────

View Accessories List
  └─ Permission: hardware.view_accessory
  
View Accessory Detail
  └─ Permission: hardware.view_accessory
  
Create Accessory
  └─ Permission: hardware.add_accessory
  
Edit Accessory
  └─ Permission: hardware.change_accessory
  
Delete Accessory
  └─ Permission: hardware.delete_accessory
  
Create Assignment
  └─ Permission: hardware.add_relatedasset
  
Edit Assignment
  └─ Permission: hardware.change_relatedasset
  
Delete Assignment
  └─ Permission: hardware.delete_relatedasset


Staff Only Operations (typically):
  ├─ Create/Edit/Delete Accessories
  ├─ Create/Edit/Delete Assignments
  └─ Bulk imports

User Readable Operations:
  ├─ View Accessories List
  ├─ View Accessory Details
  └─ View Own Hardware Accessories
```

---

## 🚀 Implementation Timeline

```
Phase 1: Models & Migrations ✅ COMPLETE
  ├─ Create Accessory model
  ├─ Create RelatedAsset model
  ├─ Create migration
  └─ Apply migration

Phase 2: Forms & Admin ✅ COMPLETE
  ├─ Create AccessoryForm
  ├─ Create RelatedAssetForm
  ├─ Create AccessoryAdmin
  ├─ Create RelatedAssetAdmin
  └─ Register in admin.py

Phase 3: Templates ✅ COMPLETE
  ├─ accessory_list.html
  ├─ accessory_detail.html
  ├─ accessory_form.html
  ├─ accessory_confirm_delete.html
  ├─ related_asset_form.html
  ├─ related_asset_detail.html
  ├─ related_asset_confirm_delete.html
  └─ Update hardware_detail.html

Phase 4: Views & URLs ⏳ TODO
  ├─ Create accessory views
  ├─ Create related_asset views
  ├─ Add URL patterns
  └─ Test views

Phase 5: Integration ⏳ TODO
  ├─ Update navigation menu
  ├─ Add breadcrumbs
  ├─ Link from hardware list/detail
  └─ Test full workflow

Phase 6: Testing & Polish ⏳ TODO
  ├─ Manual testing
  ├─ Browser testing (Chrome, Firefox, Safari)
  ├─ Mobile responsive testing
  ├─ Performance testing
  └─ User acceptance testing
```

---

## 📋 Checklist for Completion

- [ ] **Models** ✅ Created and migrated
- [ ] **Forms** ✅ Created
- [ ] **Admin** ✅ Registered
- [ ] **Templates** ✅ All 8 created
- [ ] **Views** ⏳ Need to create
  - [ ] accessory_list
  - [ ] accessory_detail
  - [ ] accessory_create
  - [ ] accessory_update
  - [ ] accessory_delete
  - [ ] related_asset_create
  - [ ] related_asset_detail
  - [ ] related_asset_update
  - [ ] related_asset_delete
- [ ] **URLs** ⏳ Need to add
- [ ] **Navigation** ⏳ Need to update
- [ ] **Testing** ⏳ Need to test
- [ ] **Documentation** ✅ Complete

---

## 📞 Support Files

1. **HARDWARE_ACCESSORIES_GUIDE.md** - Models & APIs
2. **HARDWARE_TEMPLATES_GUIDE.md** - Template details
3. **HARDWARE_ACCESSORIES_IMPLEMENTATION_SUMMARY.md** - Full overview
4. **HARDWARE_ACCESSORIES_QUICK_REFERENCE.md** - Quick lookup
5. **HARDWARE_ACCESSORIES_ARCHITECTURE.md** - This file

---

**Status**: ✅ Architecture & Templates Complete → Ready for Views & URLs

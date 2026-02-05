# Hardware Accessories & Related Assets - Template Guide

## Overview

Complete HTML templates have been created for managing hardware accessories and their relationships with hardware assets. All templates follow the existing design patterns in your application.

## Templates Created

### 1. **hardware_detail.html** (UPDATED)
**Location:** `hardware/templates/hardware/hardware_detail.html`

Added a new **"Assigned Accessories"** section that displays:
- All accessories linked to the hardware asset
- Assignment type (Primary, Shared, Backup, Optional)
- Assignment and removal dates
- Links to view each accessory detail
- Quick link to assign new accessories

**Key Features:**
- Table view showing all related accessories
- Visual badges for assignment types
- Shows removal dates if accessory was removed
- "Assign one" link when no accessories are assigned

---

### 2. **accessory_list.html**
**Location:** `hardware/templates/hardware/accessory_list.html`

Main listing page for all hardware accessories in the system.

**Features:**
- Summary cards showing:
  - Total accessories count
  - In Service count
  - In Storage count
  - Retired/Disposed count
- **Filters:**
  - Text search (name, asset tag, serial, manufacturer, model)
  - Filter by type (Monitor, Keyboard, Mouse, Dock, etc.)
  - Filter by status (In Service, In Repair, In Storage, Retired, Disposed)
- **Sortable columns:**
  - Accessory name
  - Asset tag
  - Serial number
  - Type
  - Manufacturer/Model
  - Status
  - Assigned to (user)
  - Warranty expiration
- Action buttons (View, Edit, Delete) for each accessory
- Sticky filter bar for easy access

---

### 3. **accessory_detail.html**
**Location:** `hardware/templates/hardware/accessory_detail.html`

Detailed view of a single accessory with full information.

**Left Panel:**
- Accessory overview (name, asset tag, serial, type, status)
- Detailed specifications (department, primary user, location, manufacturer, model)
- Lifecycle information (purchase date, warranty expiration, warranty countdown)

**Right Panel:**
- **Hardware Assignments** section showing:
  - All hardware this accessory is assigned to
  - Assignment type
  - Currently assigned status (with visual indicators)
  - Links to view assignment details
- **Audit** information (created date, creator, last updated, updater)

**Actions:**
- Back to list
- Edit accessory
- Delete accessory
- View hardware assignments

---

### 4. **accessory_form.html**
**Location:** `hardware/templates/hardware/accessory_form.html`

Form for creating and editing hardware accessories.

**Tabs:**
1. **Identification**
   - Name (required)
   - Asset tag (required, unique)
   - Serial number
   - Accessory type (required)
   - Status
   - Location

2. **Ownership**
   - Department
   - Primary user

3. **Specifications**
   - Manufacturer
   - Model number

4. **Lifecycle**
   - Purchase date
   - Warranty expiration date

5. **Notes Section**
   - Additional notes and comments

**Validation:**
- Required fields are marked with *
- Form validation with error messages
- Unique asset tags enforced

---

### 5. **related_asset_form.html**
**Location:** `hardware/templates/hardware/related_asset_form.html`

Form for creating and editing accessory-to-hardware assignments.

**Form Fields:**
- **Hardware Asset** (required) - Dropdown to select the hardware
- **Accessory** (required) - Dropdown to select the accessory
- **Assignment Type** (required)
  - Primary: Permanently assigned
  - Shared: Shared or temporary
  - Backup: Backup accessory
  - Optional: Extra or optional
- **Removal Date** - Optional date to mark when accessory was removed
- **Notes** - Assignment-specific notes

**Help Section:**
- Visual guide to assignment types with examples
- Each type has a description and color-coded badge

---

### 6. **related_asset_detail.html**
**Location:** `hardware/templates/hardware/related_asset_detail.html`

Detailed view of a single hardware-to-accessory assignment.

**Left Panel:**
- **Assignment Details**
  - Hardware asset info with link
  - Accessory info with link
  - Assignment type with explanation
  - Current status (Active/Removed)
  - Assignment notes

- **Timeline**
  - Assigned date (always shown)
  - Removal date (if applicable)

**Right Panel:**
- **Hardware Info Card**
  - Asset tag, type, status
  - Department, primary user
  - Link to view full hardware details

- **Accessory Info Card**
  - Asset tag, type, status
  - Department, primary user
  - Link to view full accessory details

- **Audit Information**
  - Creation date and creator
  - Last updated date

**Actions:**
- View hardware details
- View accessory details
- Edit assignment
- Delete assignment

---

### 7. **accessory_confirm_delete.html**
**Location:** `hardware/templates/hardware/accessory_confirm_delete.html`

Confirmation page for deleting an accessory.

**Features:**
- Warning alert with accessory details
- Shows if accessory is assigned to hardware
- Count of assignments that will be removed
- Cancel and Delete buttons

---

### 8. **related_asset_confirm_delete.html**
**Location:** `hardware/templates/hardware/related_asset_confirm_delete.html`

Confirmation page for deleting an assignment.

**Features:**
- Warning alert showing the hardware-accessory relationship
- Assignment details (type, dates, status)
- Cancel and Delete buttons

---

## Template Features & Conventions

### Design Patterns
All templates follow your existing application conventions:
- Bootstrap 5 for styling
- Font Awesome icons for visual enhancement
- Consistent color scheme (success, info, warning, danger badges)
- Responsive design (mobile-first approach)
- Sticky headers and filter bars

### Navigation
- **Back buttons** on detail pages
- **Create buttons** on list pages
- **Breadcrumb-style navigation** through relationships
- **Quick links** between related items

### Status Indicators
- **Color-coded badges**:
  - Success (Green) - In Service, Primary assignment, Active
  - Info (Blue) - Virtual, Shared assignment
  - Warning (Orange) - In Repair, Backup assignment
  - Secondary (Gray) - In Storage, Other, Optional
  - Danger (Red) - Retired, Disposed, Removed

### Filtering & Search
- **Text search** across relevant fields
- **Dropdown filters** by type and status
- **Sticky filter bars** for easy access
- **Filter reset** buttons on all list pages
- **Active filter chips** showing current filters

### Forms
- **Tabbed organization** for better UX
- **Field grouping** by category
- **Required fields** marked with red asterisk
- **Inline error messages** with validation feedback
- **Helper text** on complex fields
- **Cancel/Save buttons** at form bottom

### Mobile Responsive
- **Collapsible filters** on mobile devices
- **Responsive table layouts** with horizontal scroll
- **Stacked card layouts** on smaller screens
- **Flexible button groups** that stack on mobile

---

## URL Routing Required

To use these templates, you'll need to define the following URL patterns in your `hardware/urls.py`:

```python
# Accessory URLs
path('accessories/', accessory_list, name='accessory_list'),
path('accessories/create/', accessory_create, name='accessory_create'),
path('accessories/<int:pk>/', accessory_detail, name='accessory_detail'),
path('accessories/<int:pk>/edit/', accessory_update, name='accessory_update'),
path('accessories/<int:pk>/delete/', accessory_delete, name='accessory_delete'),

# Related Asset (Assignment) URLs
path('assignments/', related_asset_list, name='related_asset_list'),
path('assignments/create/', related_asset_create, name='related_asset_create'),
path('assignments/<int:pk>/', related_asset_detail, name='related_asset_detail'),
path('assignments/<int:pk>/edit/', related_asset_update, name='related_asset_update'),
path('assignments/<int:pk>/delete/', related_asset_delete, name='related_asset_delete'),
```

---

## View Functions Required

Each template requires corresponding view functions. Here's a quick reference:

### Accessory Views
- `accessory_list(request)` - List all accessories with filtering
- `accessory_create(request)` - Create new accessory
- `accessory_detail(request, pk)` - Show accessory details
- `accessory_update(request, pk)` - Edit accessory
- `accessory_delete(request, pk)` - Delete accessory

### Related Asset Views
- `related_asset_list(request)` - List all assignments
- `related_asset_create(request)` - Create new assignment
- `related_asset_detail(request, pk)` - Show assignment details
- `related_asset_update(request, pk)` - Edit assignment
- `related_asset_delete(request, pk)` - Delete assignment

---

## Integration Points

### Navigation Menu
Add links to accessories in your main navigation:
```html
<li><a href="{% url 'hardware:accessory_list' %}">Accessories</a></li>
```

### Hardware Detail Page
Already integrated with:
- "Assigned Accessories" section showing all linked accessories
- Quick "Assign one" link to create new assignments

### Sidebar/Dashboard
Consider adding:
- Accessories count cards
- Recent accessories widget
- Warranty expiration alerts for accessories

---

## Customization Notes

### Modify Accessory Types
Edit the `Accessory` model's `ACCESSORY_TYPE_CHOICES` to add more types:
```python
ACCESSORY_TYPE_CHOICES = [
    ("Monitor", "Monitor / Display"),
    # Add more types here
]
```

### Add Fields
To add new fields, remember to:
1. Add the field to the `Accessory` or `RelatedAsset` model
2. Update the form to include the new field
3. Update the template to display/edit the field
4. Create a migration

### Styling
All templates use Bootstrap 5 classes. To customize:
- Edit colors in template badge classes (e.g., `bg-success`)
- Modify card layouts in template structure
- Add custom CSS in template style blocks

---

## Testing Workflow

### Manual Testing Steps
1. **Create Accessory**
   - Navigate to Accessories → New Accessory
   - Fill in form fields
   - Verify required field validation
   - Save and verify redirect to detail page

2. **View Accessories**
   - Navigate to Accessories list
   - Test filters (type, status, search)
   - Verify sorting on columns
   - Click on an accessory to view details

3. **Assign to Hardware**
   - From hardware detail page, click "Assign one" in accessories section
   - Select hardware and accessory
   - Choose assignment type
   - Save and verify appears in hardware detail

4. **Manage Assignments**
   - View assignment detail
   - Edit assignment (change type, add removal date)
   - Delete assignment
   - Verify cascading relationships

---

## Performance Considerations

- Templates use `select_related()` and `prefetch_related()` for efficiency
- Filters are sticky-positioned for better UX
- Tables have responsive designs to prevent content overflow
- Badge systems use CSS for efficient styling

---

## Accessibility Notes

- All form labels are properly associated with inputs
- Color-coded badges have text labels (not just color)
- Icons have semantic meaning with aria-labels where appropriate
- Form errors are displayed inline for clarity
- Keyboard navigation supported throughout

---

## Next Steps

1. **Create View Functions** - Implement the view functions for each template
2. **Define URL Patterns** - Add URL routes in `hardware/urls.py`
3. **Update Navigation** - Add links to accessories in your main navigation
4. **Test End-to-End** - Test the full workflow of creating and managing accessories
5. **Add Permissions** - Implement permission checks in views if needed
6. **API Endpoints** - Consider adding API endpoints for accessories management

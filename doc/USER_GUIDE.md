# User Guide
## User Access Management System (UAMS)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [User Management](#user-management)
4. [Department Management](#department-management)
5. [System Management](#system-management)
6. [Access Management](#access-management)
7. [Dashboard & Reports](#dashboard-reports)
8. [Search Functionality](#search-functionality)
9. [Data Import/Export](#data-importexport)
10. [User Roles & Permissions](#user-roles-permissions)
11. [Troubleshooting](#troubleshooting)
12. [FAQs](#faqs)

---

## Introduction

### What is UAMS?

The User Access Management System (UAMS) is a web-based application designed to help organizations:
- Document and manage employee information
- Track system access assignments
- Maintain organizational structure
- Generate reports and analytics
- Ensure compliance with access management policies

### Key Features

- **User Management**: Comprehensive employee profiles with photos
- **Department Organization**: Hierarchical department structure
- **System Tracking**: Document all systems and applications
- **Access Documentation**: Track who has access to what systems
- **Audit Trail**: Complete history of all changes
- **Search**: Quick search across all data
- **Reports**: Export data in multiple formats

---

## Getting Started

### Logging In

1. Navigate to the UAMS login page
2. Enter your **Username** and **Password**
3. Click **Login**

**Note**: If you don't have an account, contact your system administrator.

### Dashboard Overview

After logging in, you'll see the main dashboard with:
- **Statistics Cards**: Overview of users, departments, systems, and access assignments
- **Charts**: Visual representation of access trends
- **Quick Actions**: Shortcuts to common tasks
- **Recent Activity**: Latest changes in the system

### Navigation Menu

The main navigation menu provides access to:
- **Dashboard**: Home page with statistics
- **Users**: User management
- **Departments**: Department management
- **Systems**: System/application management
- **Access Management**: Access assignments
- **Search**: Global search functionality
- **Import/Export**: Data import and export tools

---

## User Management

### Viewing Users

1. Click **Users** in the navigation menu
2. You'll see a list of all users with:
   - Name and email
   - Department
   - Status (Active/Inactive)
   - Employee ID

### Filtering Users

Use the filter options at the top:
- **Search**: Search by name, email, or employee ID
- **Status**: Filter by Active/Inactive
- **Department**: Filter by department
- **Page Size**: Choose how many users per page

### Viewing User Details

1. Click on a user's name or the **View** button
2. The user detail page shows:
   - **Profile Photo**: User's profile picture (if uploaded)
   - **Personal Information**: Name, email, phone numbers
   - **Employment Information**: Employee ID, position, join date
   - **Access Assignments**: All systems the user has access to

### Creating a New User

**Required Permissions**: HR Admin or Super Admin

1. Click **Add User** button
2. Fill in the required fields:
   - **Username**: Unique username for login
   - **Email**: Work email address
   - **First Name** and **Last Name**
   - **Password**: Set initial password
   - **Department**: Select from dropdown
   - **Position**: Job title
   - **Employment Type**: Full-time, Part-time, etc.
   - **Phone**: Primary phone number
3. Optionally fill in additional fields:
   - Profile photo (max 2MB, JPG/PNG)
   - Secondary phone
   - Personal email
   - Notes
4. Click **Save**

### Editing a User

1. Navigate to the user's detail page
2. Click **Edit User** button
3. Make your changes
4. Click **Save**

### Uploading Profile Photo

1. When creating or editing a user
2. Click **Choose File** under Profile Photo
3. Select an image file (JPG or PNG, max 2MB)
4. The photo will be automatically cropped to a circle
5. Click **Save**

### Resetting User Password

**Required Permissions**: HR Admin or Super Admin

1. Go to the user's detail page
2. Click **Reset Password** button
3. Enter the new password
4. Confirm the password
5. Click **Reset Password**

### Deactivating a User

**Required Permissions**: HR Admin or Super Admin

1. Go to the user's detail page
2. Click **Delete User** button
3. Confirm the deactivation
4. The user will be marked as inactive (not deleted)

**Note**: Deactivated users are archived for audit purposes.

### Managing User Permissions

**Required Permissions**: Super Admin only

1. Go to the user's detail page
2. Click **Manage Permissions** button
3. Select/deselect permissions
4. Click **Save**

### Bulk Actions

**Required Permissions**: HR Admin or Super Admin

1. Select multiple users using checkboxes
2. Choose an action from the dropdown:
   - Activate
   - Deactivate
   - Assign Department
   - Export Selected
3. Click **Apply**

---

## Department Management

### Viewing Departments

1. Click **Departments** in the navigation menu
2. View the list of all departments with:
   - Department name
   - Description
   - Number of users
   - Status

### Creating a Department

**Required Permissions**: HR Admin or Super Admin

1. Click **Add Department** button
2. Fill in:
   - **Name**: Department name (required)
   - **Description**: Optional description
   - **Parent Department**: For sub-departments (optional)
3. Click **Save**

### Editing a Department

1. Click on a department name
2. Click **Edit** button
3. Make changes
4. Click **Save**

### Viewing Department Users

1. Click on a department name
2. View the **Users** section
3. See all users assigned to this department

---

## System Management

### Viewing Systems

1. Click **Systems** in the navigation menu
2. View all systems with:
   - System name and code
   - Category
   - Vendor
   - Status

### Creating a System

**Required Permissions**: Access Administrator or Super Admin

1. Click **Add System** button
2. Fill in required fields:
   - **Name**: System name
   - **Code**: Unique system code
   - **Category**: System category
   - **Description**: System description
3. Optionally fill in:
   - Vendor
   - URL
   - Environment (Production, Staging, etc.)
   - Support contact information
4. Click **Save**

### Editing a System

1. Click on a system name
2. Click **Edit** button
3. Make changes
4. Click **Save**

---

## Access Management

### Viewing Access Assignments

1. Click **Access Management** in the navigation menu
2. View all access assignments with:
   - User name
   - System name
   - Access type
   - Status
   - Dates

### Creating Access Assignment

**Required Permissions**: Access Administrator or Super Admin

1. Click **Add Access Assignment** button
2. Fill in:
   - **User**: Select user from dropdown
   - **System**: Select system from dropdown
   - **Access Type**: Full Access, Read Only, Admin, etc.
   - **Status**: Active, Pending, etc.
   - **Priority**: Low, Medium, High, Critical
   - **Request Type**: New Access, Renewal, etc.
   - **Start Date**: When access begins
   - **End Date**: When access expires (optional)
3. Click **Save**

### Editing Access Assignment

1. Click on an access assignment
2. Click **Edit** button
3. Make changes
4. Click **Save**

### Viewing Access History

1. Click **Access History** in the Access Management menu
2. View all access events:
   - User actions
   - System changes
   - Status changes
   - Timestamps

### Filtering Access Assignments

Use filters to find specific assignments:
- **User**: Filter by user
- **System**: Filter by system
- **Status**: Filter by status
- **Date Range**: Filter by date

---

## Dashboard & Reports

### Dashboard Overview

The dashboard provides:
- **User Statistics**: Total users, active users, new users
- **System Statistics**: Total systems, active systems
- **Access Statistics**: Total assignments, active access
- **Charts**: Visual trends over time

### Viewing Reports

1. Click **Reports** in the navigation menu
2. Select a report type:
   - User Reports
   - Department Reports
   - System Reports
   - Access Reports
3. Apply filters if needed
4. View or export the report

### Exporting Data

#### Export to Excel

1. Navigate to any list page (Users, Departments, Systems, etc.)
2. Click **Export to Excel** button
3. The file will download automatically

#### Export to PDF

1. Navigate to any list page
2. Click **Export to PDF** button
3. The file will download automatically

#### Export Selected Items

1. Select items using checkboxes
2. Click **Export Selected** from bulk actions
3. Choose format (Excel or PDF)
4. Download the file

---

## Search Functionality

### Global Search

1. Click **Search** in the navigation menu
2. Enter your search term
3. Select what to search:
   - Users
   - Departments
   - Systems
   - Access Assignments
4. Click **Search**

### Search Tips

- Search is case-insensitive
- Partial matches are supported
- Search across multiple fields:
  - Users: Name, email, employee ID
  - Departments: Name, description
  - Systems: Name, code, description
  - Access: User name, system name

---

## Data Import/Export

### Exporting Data

1. Navigate to **Data Import/Export**
2. Select what to export:
   - Users
   - Departments
   - Systems
   - Access Assignments
3. Choose format (CSV or Excel)
4. Click **Export**

### Importing Data

**Required Permissions**: HR Admin or Super Admin

1. Navigate to **Data Import/Export**
2. Select what to import
3. Download the template file (if available)
4. Fill in the template with your data
5. Upload the file
6. Review the preview
7. Click **Import**

### CSV Format Requirements

#### Users CSV
```csv
username,email,first_name,last_name,department,position,phone_primary
john.doe,john.doe@company.com,John,Doe,IT,Developer,+1234567890
```

#### Departments CSV
```csv
name,description,parent
IT Department,Information Technology,
Development,Software Development,IT Department
```

#### Systems CSV
```csv
name,code,category,description,vendor
CRM System,CRM-001,Application,Customer Management,Microsoft
```

---

## User Roles & Permissions

### Understanding Your Role

Your role determines what you can do in the system:

#### Super Admin
- Full access to all features
- Can manage all users, departments, and systems
- Can configure system settings

#### HR Admin
- Can manage users and departments
- Can import/export data
- Cannot manage system access

#### Access Administrator
- Can manage systems and access assignments
- Can view access history
- Cannot delete users

#### Department Manager
- Can view users in their department
- Can view access for their department
- Read-only for other departments

#### Viewer
- Can view all information
- Cannot make any changes
- Read-only access

### What You Can Do

Check the action buttons on each page:
- If you see **Edit**, you can modify that item
- If you see **Delete**, you can remove that item
- If buttons are missing, you don't have permission

---

## Troubleshooting

### Common Issues

#### Can't Log In

**Problem**: Login fails with incorrect credentials

**Solutions**:
- Check username and password (case-sensitive)
- Contact administrator to reset password
- Ensure account is active

#### Can't See Certain Features

**Problem**: Buttons or menu items are missing

**Solution**: Your user role may not have permission. Contact your administrator.

#### Profile Photo Not Showing

**Problem**: User photo displays as placeholder

**Solutions**:
- Check if photo was uploaded (max 2MB, JPG/PNG)
- Clear browser cache
- Contact administrator if issue persists

#### Export Not Working

**Problem**: Export button doesn't download file

**Solutions**:
- Check browser pop-up blocker settings
- Try a different browser
- Check file size (very large exports may take time)

#### Search Not Finding Results

**Problem**: Search returns no results

**Solutions**:
- Check spelling
- Try partial words
- Select correct search category
- Clear search and try again

### Getting Help

If you encounter issues:
1. Check this user guide
2. Contact your system administrator
3. Check system notifications for announcements

---

## FAQs

### General Questions

**Q: Can I change my own password?**
A: Currently, password changes must be done by an administrator. Contact your HR or IT department.

**Q: How do I upload a profile photo?**
A: Only administrators can upload profile photos when creating or editing users.

**Q: Can I delete a user?**
A: Users are deactivated, not deleted, to maintain audit trails. Only HR Admins and Super Admins can deactivate users.

**Q: What happens to access when a user is deactivated?**
A: Access assignments remain in the system for audit purposes but are marked as inactive.

**Q: Can I export my own access information?**
A: Yes, if you have export permissions. Go to Access Management and use the export feature.

**Q: How often is data updated?**
A: Data is updated in real-time when changes are made by authorized users.

**Q: Can I see who made changes?**
A: Yes, the system tracks who created and updated each record. Check the detail pages for this information.

**Q: What file formats are supported for import?**
A: CSV and Excel (.xlsx) formats are supported.

**Q: Is there a mobile app?**
A: The system is web-based and works on mobile browsers, but there is no dedicated mobile app.

**Q: How do I report a bug or request a feature?**
A: Contact your system administrator or IT support team.

---

## Best Practices

### For All Users

- Keep your information up to date
- Use the search function before creating duplicates
- Review access assignments regularly
- Report any discrepancies to administrators

### For Administrators

- Regularly review and update user information
- Document system access accurately
- Keep department structure current
- Export data regularly for backups
- Review access history for compliance

### Data Entry Tips

- Use consistent naming conventions
- Fill in all required fields
- Add descriptions where helpful
- Upload profile photos when available
- Keep notes updated

---

## Keyboard Shortcuts

While the system doesn't have specific keyboard shortcuts, you can use standard browser shortcuts:
- **Ctrl+F** (Cmd+F on Mac): Find on page
- **Ctrl+P** (Cmd+P on Mac): Print page
- **F5**: Refresh page
- **Esc**: Close modals/dialogs

---

## System Requirements

### Browser Support

The system works best with:
- **Chrome** (recommended)
- **Firefox**
- **Edge**
- **Safari**

### Screen Resolution

- Minimum: 1024x768
- Recommended: 1920x1080 or higher

---

## Contact & Support

For technical support or questions:
- Contact your system administrator
- Check system announcements
- Refer to this user guide

---

**Last Updated**: 2024
**Version**: 1.0.0


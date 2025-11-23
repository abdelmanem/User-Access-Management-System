# Getting Started

Welcome to UAMS! This guide will help you get started with the User Access Management System.

![Getting Started](../images/getting-started.png)

## First Steps

### Logging In

1. Navigate to your UAMS installation URL (e.g., `https://uams.yourdomain.com`)
2. Enter your **Username** and **Password**
3. Click **Login**

![Login Screen](../images/login-screen.png)

**Note**: If you don't have an account, contact your system administrator to create one.

### Dashboard Overview

After logging in, you'll see the main dashboard:

![Dashboard](../images/dashboard.png)

The dashboard provides:

- **Statistics Cards**: Overview of users, departments, systems, and access records
- **Charts**: Visual representation of access trends and statistics
- **Quick Actions**: Shortcuts to common tasks
- **Recent Activity**: Latest changes in the system

### Navigation Menu

The main navigation menu provides access to:

- **Dashboard**: Main overview page
- **Users**: User management
- **Departments**: Department management
- **Systems**: System catalog
- **Access Management**: Access records
- **Reports**: Generate reports
- **Search**: Global search functionality

## Basic Tasks

### Viewing Your Profile

1. Click on your username in the top-right corner
2. Select **Profile** from the dropdown
3. Review your profile information
4. Update your information if needed

**Example Profile View**:

```python
# Profile view URL
/accounts/profile/<user_id>/

# View your own profile
/accounts/profile/
```

### Managing Users

#### Viewing Users

1. Navigate to **Users** in the main menu
2. Browse the user list
3. Use search and filters to find specific users
4. Click on a user to view details

#### Creating a User

1. Navigate to **Users** → **Add User**
2. Fill in the required information:
   - Username
   - Email
   - First Name
   - Last Name
   - Department
   - Role
3. Upload a profile photo (optional)
4. Click **Save**

**Example: Creating a User via API**

```python
from accounts.models import User
from departments.models import Department

# Get department
department = Department.objects.get(name='IT Department')

# Create user
user = User.objects.create_user(
    username='jdoe',
    email='jdoe@example.com',
    first_name='John',
    last_name='Doe',
    department=department,
    role='employee'
)
```

### Managing Departments

#### Viewing Departments

1. Navigate to **Departments** in the main menu
2. View the hierarchical department structure
3. Expand/collapse departments to see sub-departments
4. Click on a department to view details

#### Creating a Department

1. Navigate to **Departments** → **Add Department**
2. Fill in the information:
   - Name
   - Description
   - Parent Department (optional)
   - Manager
3. Click **Save**

**Example: Creating a Department**

```python
from departments.models import Department

# Create top-level department
it_dept = Department.objects.create(
    name='IT Department',
    description='Information Technology',
    manager=manager_user
)

# Create sub-department
dev_team = Department.objects.create(
    name='Development Team',
    description='Software Development',
    parent=it_dept,
    manager=dev_manager_user
)
```

### Managing Systems

#### Viewing Systems

1. Navigate to **Systems** in the main menu
2. Browse the system catalog
3. Use filters to find specific systems
4. Click on a system to view details

#### Adding a System

1. Navigate to **Systems** → **Add System**
2. Fill in the system information:
   - Name
   - Description
   - System Type
   - Category
   - Access Levels
3. Click **Save**

**Example: Adding a System**

```python
from systems.models import System

system = System.objects.create(
    name='Customer Database',
    description='Primary customer management system',
    system_type='Database',
    category='Critical',
    access_levels=['Read', 'Write', 'Admin']
)
```

### Managing Access

#### Viewing Access Records

1. Navigate to **Access Management** in the main menu
2. View all access records
3. Filter by user, system, or status
4. Click on a record to view details

#### Granting Access

1. Navigate to **Access Management** → **Grant Access**
2. Select the **User**
3. Select the **System**
4. Choose the **Access Level**
5. Add **Notes** (optional)
6. Click **Grant Access**

**Example: Granting Access**

```python
from access_management.models import AccessRecord
from django.utils import timezone

access = AccessRecord.objects.create(
    user=user,
    system=system,
    access_level='Read',
    granted_date=timezone.now(),
    granted_by=request.user,
    notes='Access granted for project work'
)
```

#### Revoking Access

1. Navigate to the access record
2. Click **Revoke Access**
3. Confirm the revocation
4. Add a reason (optional)

**Example: Revoking Access**

```python
from django.utils import timezone

access.revoked_date = timezone.now()
access.revoked_by = request.user
access.revoked_reason = 'Project completed'
access.is_active = False
access.save()
```

## Search Functionality

### Global Search

1. Use the search box in the top navigation
2. Enter your search query
3. View results across:
   - Users
   - Departments
   - Systems
   - Access Records

**Example Search Queries**:

- User name: `john doe`
- Department: `IT Department`
- System: `Customer Database`
- Access: `john database`

### Advanced Search

1. Navigate to **Search** → **Advanced Search**
2. Select search categories
3. Apply filters
4. Click **Search**

## Reports

### Generating Reports

1. Navigate to **Reports** in the main menu
2. Select report type:
   - User Access Report
   - Department Report
   - System Report
   - Compliance Report
3. Apply filters
4. Click **Generate Report**
5. Export in desired format (CSV, Excel, PDF)

### Common Reports

#### User Access Summary

Shows all access for a specific user:

1. Navigate to **Reports** → **User Access Summary**
2. Select user
3. Choose date range
4. Generate report

#### Department Access Report

Shows all access for a department:

1. Navigate to **Reports** → **Department Access Report**
2. Select department
3. Generate report

## Data Import/Export

### Importing Data

#### Import Users

1. Navigate to **Data Import/Export** → **Import Users**
2. Download the template CSV file
3. Fill in user data
4. Upload the CSV file
5. Review import preview
6. Confirm import

**CSV Template Format**:

```csv
username,email,first_name,last_name,department,role
jdoe,jdoe@example.com,John,Doe,IT Department,employee
jsmith,jsmith@example.com,Jane,Smith,HR Department,manager
```

#### Import Systems

1. Navigate to **Data Import/Export** → **Import Systems**
2. Download template
3. Fill in system data
4. Upload and import

### Exporting Data

#### Export Users

1. Navigate to **Users**
2. Apply filters if needed
3. Click **Export**
4. Choose format (CSV, Excel, PDF)
5. Download file

## User Roles & Permissions

### Understanding Roles

UAMS includes several user roles:

- **Super Admin**: Full system access
- **HR Admin**: User and department management
- **Access Administrator**: Access management
- **Department Manager**: Department-specific access
- **Viewer**: Read-only access

### Role Capabilities

| Action | Super Admin | HR Admin | Access Admin | Dept Mgr | Viewer |
|--------|-------------|----------|--------------|----------|--------|
| Create Users | ✓ | ✓ | ✗ | ✗ | ✗ |
| Edit Users | ✓ | ✓ | ✗ | ✗ | ✗ |
| Delete Users | ✓ | ✓ | ✗ | ✗ | ✗ |
| Manage Departments | ✓ | ✓ | ✗ | ✗ | ✗ |
| Grant Access | ✓ | ✗ | ✓ | ✗ | ✗ |
| Revoke Access | ✓ | ✗ | ✓ | ✗ | ✗ |
| View Reports | ✓ | ✓ | ✓ | ✓ | ✓ |
| Export Data | ✓ | ✓ | ✓ | ✓ | ✗ |

## Best Practices

### Access Management

1. **Document All Access**: Document every access grant
2. **Regular Reviews**: Conduct periodic access reviews
3. **Justification**: Always document business justification
4. **Timely Revocation**: Revoke access when no longer needed
5. **Audit Trail**: Maintain complete audit history

### User Management

1. **Complete Profiles**: Fill in all user information
2. **Profile Photos**: Add profile photos for identification
3. **Department Assignment**: Assign users to correct departments
4. **Role Assignment**: Assign appropriate roles

### System Management

1. **Complete Information**: Provide detailed system descriptions
2. **Access Levels**: Define clear access levels
3. **Categorization**: Categorize systems appropriately
4. **Regular Updates**: Keep system information current

## Troubleshooting

### Common Issues

#### Cannot Log In

- Verify username and password
- Check if account is active
- Contact administrator if locked out

#### Cannot View Data

- Check user permissions
- Verify role assignments
- Contact administrator

#### Import Errors

- Check CSV format
- Verify required fields
- Review error messages
- Check data validation rules

### Getting Help

1. **Documentation**: Review relevant documentation sections
2. **FAQ**: Check [Frequently Asked Questions](#frequently-asked-questions)
3. **Administrator**: Contact your system administrator
4. **Support**: Submit a support ticket

## Frequently Asked Questions

### General Questions

**Q: What is UAMS?**
A: UAMS is a User Access Management System for documenting and managing user access to systems.

**Q: Who can use UAMS?**
A: Any authorized user in your organization can access UAMS based on their role and permissions.

**Q: Is UAMS an access request system?**
A: No, UAMS is a documentation system. Administrators document access, not request it.

### Access Management

**Q: How do I grant access to a user?**
A: Navigate to Access Management → Grant Access, select user and system, choose access level, and save.

**Q: Can I revoke access?**
A: Yes, navigate to the access record and click Revoke Access.

**Q: How do I track access history?**
A: Access history is automatically tracked. View it in the access record details.

### Data Management

**Q: Can I import users in bulk?**
A: Yes, use the Data Import/Export feature to import users from CSV files.

**Q: What formats can I export to?**
A: CSV, Excel, PDF, and JSON formats are supported.

**Q: How do I backup data?**
A: Use the export functionality or database backup tools.

## Next Steps

Now that you're familiar with the basics:

1. [Configuration](configuration.md) - Configure UAMS for your needs
2. [Best Practices](best_practices.md) - Learn recommended practices
3. [Administration](administration.md) - Administer the system
4. [Features](features.md) - Explore all features

---

For detailed information on specific features, see the [User Guide](USER_GUIDE.md) or [Features](features.md) documentation.


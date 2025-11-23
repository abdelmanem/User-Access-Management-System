# Data Model

This document describes the database schema and data model for UAMS.

![Data Model](../images/data-model.png)

## Data Model Overview

UAMS uses Django's ORM with the following main models:

- **User**: User accounts and profiles
- **Department**: Organizational structure
- **System**: Systems and applications
- **AccessRecord**: Access assignments
- **ServiceAccount**: Service account management
- **DefaultAccount**: Default account tracking

## User Model

### User (accounts.User)

Extends Django's AbstractUser model.

**Fields**:

```python
class User(AbstractUser):
    # Inherited from AbstractUser
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    # Custom fields
    department = models.ForeignKey(
        'departments.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default='employee'
    )
    employee_id = models.CharField(max_length=50, unique=True, null=True)
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
```

**Relationships**:
- `department`: ForeignKey to Department
- `accessrecord_set`: Reverse relation to AccessRecord

**Example Usage**:

```python
from accounts.models import User

# Create user
user = User.objects.create_user(
    username='jdoe',
    email='jdoe@example.com',
    first_name='John',
    last_name='Doe',
    department=department
)

# Query users
active_users = User.objects.filter(is_active=True)
users_in_department = User.objects.filter(department=department)
```

## Department Model

### Department (departments.Department)

Represents organizational departments with hierarchical structure.

**Fields**:

```python
class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    code = models.CharField(max_length=50, unique=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    manager = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
```

**Relationships**:
- `parent`: Self-referential ForeignKey for hierarchy
- `children`: Reverse relation to child departments
- `manager`: ForeignKey to User
- `user_set`: Reverse relation to Users

**Example Usage**:

```python
from departments.models import Department

# Create department
dept = Department.objects.create(
    name='IT Department',
    description='Information Technology',
    code='IT'
)

# Create sub-department
sub_dept = Department.objects.create(
    name='Development Team',
    parent=dept,
    code='IT-DEV'
)

# Get all children
children = dept.children.all()

# Get all ancestors
def get_ancestors(dept):
    ancestors = []
    current = dept.parent
    while current:
        ancestors.append(current)
        current = current.parent
    return ancestors
```

## System Model

### System (systems.System)

Represents systems and applications that users can access.

**Fields**:

```python
class System(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    system_type = models.CharField(
        max_length=50,
        choices=SYSTEM_TYPE_CHOICES
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='Standard'
    )
    access_levels = models.JSONField(
        default=list,
        help_text='Available access levels'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Optional fields
    vendor = models.CharField(max_length=100, blank=True)
    version = models.CharField(max_length=50, blank=True)
    support_contact = models.EmailField(blank=True)
    documentation_url = models.URLField(blank=True)
```

**Relationships**:
- `accessrecord_set`: Reverse relation to AccessRecord

**Example Usage**:

```python
from systems.models import System

# Create system
system = System.objects.create(
    name='Customer Database',
    description='Primary customer management system',
    system_type='Database',
    category='Critical',
    access_levels=['Read', 'Write', 'Admin']
)

# Query systems
active_systems = System.objects.filter(is_active=True)
critical_systems = System.objects.filter(category='Critical')
```

## Access Record Model

### AccessRecord (access_management.AccessRecord)

Documents user access to systems.

**Fields**:

```python
class AccessRecord(models.Model):
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='accessrecord_set'
    )
    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='accessrecord_set'
    )
    access_level = models.CharField(max_length=50)
    
    # Grant information
    granted_date = models.DateTimeField()
    granted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_access_set'
    )
    justification = models.TextField(blank=True)
    
    # Approval information
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_access_set'
    )
    approved_date = models.DateTimeField(null=True, blank=True)
    
    # Revocation information
    revoked_date = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_access_set'
    )
    revoked_reason = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Review information
    last_reviewed_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Relationships**:
- `user`: ForeignKey to User
- `system`: ForeignKey to System
- `granted_by`, `approved_by`, `revoked_by`: ForeignKey to User

**Example Usage**:

```python
from access_management.models import AccessRecord
from django.utils import timezone

# Grant access
access = AccessRecord.objects.create(
    user=user,
    system=system,
    access_level='Read',
    granted_date=timezone.now(),
    granted_by=admin_user,
    justification='Required for project work'
)

# Query active access
active_access = AccessRecord.objects.filter(is_active=True)
user_access = AccessRecord.objects.filter(user=user, is_active=True)
system_access = AccessRecord.objects.filter(system=system, is_active=True)

# Revoke access
access.revoked_date = timezone.now()
access.revoked_by = admin_user
access.revoked_reason = 'Project completed'
access.is_active = False
access.save()
```

## Service Account Model

### ServiceAccount (service_accounts.ServiceAccount)

Manages service accounts (non-human accounts).

**Fields**:

```python
class ServiceAccount(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    account_id = models.CharField(max_length=100, unique=True)
    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='service_accounts'
    )
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_service_accounts'
    )
    purpose = models.TextField()
    created_date = models.DateField()
    last_reviewed_date = models.DateField(null=True, blank=True)
    review_due_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Relationships**:
- `system`: ForeignKey to System
- `owner`: ForeignKey to User

## Default Account Model

### DefaultAccount (default_accounts.DefaultAccount)

Tracks default accounts.

**Fields**:

```python
class DefaultAccount(models.Model):
    account_name = models.CharField(max_length=100)
    system = models.ForeignKey(
        'systems.System',
        on_delete=models.CASCADE,
        related_name='default_accounts'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    last_used_date = models.DateTimeField(null=True, blank=True)
    security_controls = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

## Model Relationships

### Entity Relationship Diagram

```
User
├── department (FK → Department)
├── accessrecord_set (reverse → AccessRecord)
└── managed_departments (reverse → Department)

Department
├── parent (FK → Department, self)
├── children (reverse → Department)
├── manager (FK → User)
└── user_set (reverse → User)

System
└── accessrecord_set (reverse → AccessRecord)

AccessRecord
├── user (FK → User)
├── system (FK → System)
├── granted_by (FK → User)
├── approved_by (FK → User)
└── revoked_by (FK → User)
```

## Database Indexes

### Recommended Indexes

```python
# User model indexes
class User(AbstractUser):
    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['department']),
            models.Index(fields=['is_active']),
        ]

# AccessRecord indexes
class AccessRecord(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['system', 'is_active']),
            models.Index(fields=['granted_date']),
            models.Index(fields=['revoked_date']),
        ]
```

## Data Integrity

### Constraints

```python
# Unique constraints
class AccessRecord(models.Model):
    class Meta:
        unique_together = [['user', 'system', 'access_level']]
        # Prevent duplicate active access records
```

### Validation

```python
# Model validation
from django.core.exceptions import ValidationError

class AccessRecord(models.Model):
    def clean(self):
        if self.revoked_date and self.revoked_date < self.granted_date:
            raise ValidationError('Revoked date cannot be before granted date')
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
```

## Query Optimization

### Efficient Queries

```python
# Use select_related for ForeignKey
access_records = AccessRecord.objects.select_related(
    'user', 'system'
).filter(is_active=True)

# Use prefetch_related for reverse relations
departments = Department.objects.prefetch_related(
    'user_set', 'children'
).all()

# Use only() to limit fields
users = User.objects.only('username', 'email', 'first_name', 'last_name')
```

### Aggregation

```python
from django.db.models import Count, Q

# Count access by system
from access_management.models import AccessRecord

system_access_counts = AccessRecord.objects.filter(
    is_active=True
).values('system__name').annotate(
    count=Count('id')
).order_by('-count')

# Count users by department
from accounts.models import User

dept_user_counts = User.objects.filter(
    is_active=True
).values('department__name').annotate(
    count=Count('id')
)
```

## Migration Management

### Creating Migrations

```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate

# Show migration status
python manage.py showmigrations
```

### Data Migrations

```python
# migrations/0002_update_user_roles.py
from django.db import migrations

def update_user_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(is_staff=True).update(role='admin')

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(update_user_roles),
    ]
```

## Next Steps

- [Reference](reference.md) - API reference
- [Development](development.md) - Development guidelines
- [Administration](administration.md) - Administrative tasks

---

For API usage examples, see the [Reference](reference.md) documentation.


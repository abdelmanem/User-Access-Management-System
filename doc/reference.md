# Reference

Technical reference documentation for UAMS APIs, models, and utilities.

![Reference](../images/reference.png)

## API Reference

### REST API Endpoints

UAMS provides RESTful API endpoints for programmatic access.

#### Authentication

```python
# Session authentication (default)
# Include session cookie in requests

# Token authentication (if enabled)
headers = {
    'Authorization': 'Token your-api-token'
}
```

#### Base URL

```
https://yourdomain.com/api/
```

### User API

#### List Users

```http
GET /api/users/
```

**Response**:

```json
{
    "count": 100,
    "next": "https://yourdomain.com/api/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "jdoe",
            "email": "jdoe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "department": {
                "id": 1,
                "name": "IT Department"
            },
            "role": "employee",
            "is_active": true
        }
    ]
}
```

#### Get User

```http
GET /api/users/{id}/
```

#### Create User

```http
POST /api/users/
Content-Type: application/json

{
    "username": "jdoe",
    "email": "jdoe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "department": 1,
    "password": "secure_password"
}
```

#### Update User

```http
PATCH /api/users/{id}/
Content-Type: application/json

{
    "first_name": "Jane",
    "email": "jane@example.com"
}
```

#### Delete User

```http
DELETE /api/users/{id}/
```

### Department API

#### List Departments

```http
GET /api/departments/
```

**Response**:

```json
{
    "count": 20,
    "results": [
        {
            "id": 1,
            "name": "IT Department",
            "description": "Information Technology",
            "code": "IT",
            "parent": null,
            "manager": {
                "id": 1,
                "username": "manager"
            },
            "is_active": true
        }
    ]
}
```

#### Get Department

```http
GET /api/departments/{id}/
```

#### Create Department

```http
POST /api/departments/
Content-Type: application/json

{
    "name": "IT Department",
    "description": "Information Technology",
    "code": "IT",
    "parent": null,
    "manager": 1
}
```

### System API

#### List Systems

```http
GET /api/systems/
```

**Response**:

```json
{
    "count": 50,
    "results": [
        {
            "id": 1,
            "name": "Customer Database",
            "description": "Primary customer management system",
            "system_type": "Database",
            "category": "Critical",
            "access_levels": ["Read", "Write", "Admin"],
            "is_active": true
        }
    ]
}
```

### Access Record API

#### List Access Records

```http
GET /api/access-records/
```

**Query Parameters**:
- `user`: Filter by user ID
- `system`: Filter by system ID
- `is_active`: Filter by active status
- `access_level`: Filter by access level

**Example**:

```http
GET /api/access-records/?user=1&is_active=true
```

#### Get Access Record

```http
GET /api/access-records/{id}/
```

#### Create Access Record

```http
POST /api/access-records/
Content-Type: application/json

{
    "user": 1,
    "system": 1,
    "access_level": "Read",
    "justification": "Required for project work"
}
```

#### Revoke Access

```http
PATCH /api/access-records/{id}/
Content-Type: application/json

{
    "is_active": false,
    "revoked_reason": "Project completed"
}
```

## Model Reference

### User Model

```python
from accounts.models import User

# Fields
user.username          # str: Username
user.email            # str: Email address
user.first_name       # str: First name
user.last_name        # str: Last name
user.department       # Department: Department object
user.role             # str: User role
user.is_active        # bool: Active status
user.date_joined      # datetime: Join date

# Methods
user.get_full_name()  # str: Full name
user.get_short_name() # str: Short name
```

### Department Model

```python
from departments.models import Department

# Fields
dept.name             # str: Department name
dept.description      # str: Description
dept.code             # str: Department code
dept.parent           # Department: Parent department
dept.manager          # User: Department manager
dept.is_active        # bool: Active status

# Methods
dept.get_children()   # QuerySet: Child departments
dept.get_ancestors()  # list: Ancestor departments
```

### System Model

```python
from systems.models import System

# Fields
system.name           # str: System name
system.description    # str: Description
system.system_type    # str: System type
system.category       # str: Category
system.access_levels  # list: Available access levels
system.is_active      # bool: Active status
```

### AccessRecord Model

```python
from access_management.models import AccessRecord

# Fields
access.user           # User: User object
access.system         # System: System object
access.access_level   # str: Access level
access.granted_date   # datetime: Grant date
access.granted_by     # User: User who granted access
access.approved_by    # User: User who approved
access.revoked_date   # datetime: Revocation date
access.is_active      # bool: Active status

# Methods
access.is_revoked()   # bool: Check if revoked
access.days_active()   # int: Days since grant
```

## View Reference

### Class-Based Views

```python
from django.views.generic import ListView, DetailView, CreateView
from accounts.models import User

class UserListView(ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        # Add filtering logic
        return queryset

class UserDetailView(DetailView):
    model = User
    template_name = 'accounts/user_detail.html'
    context_object_name = 'user'

class UserCreateView(CreateView):
    model = User
    template_name = 'accounts/user_form.html'
    fields = ['username', 'email', 'first_name', 'last_name', 'department']
    
    def form_valid(self, form):
        # Custom validation logic
        return super().form_valid(form)
```

### Function-Based Views

```python
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.models import User

@login_required
def user_list(request):
    users = User.objects.filter(is_active=True)
    context = {'users': users}
    return render(request, 'accounts/user_list.html', context)

@login_required
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    context = {'user': user}
    return render(request, 'accounts/user_detail.html', context)
```

## Utility Functions

### Search Utilities

```python
from utils.search_utils import search_all, search_users, search_systems

# Global search
results = search_all(query='john', user=request.user)
# Returns: {'users': [...], 'departments': [...], 'systems': [...]}

# User search
users = search_users(query='john')

# System search
systems = search_systems(query='database')
```

### Export Utilities

```python
from utils.exporters import export_users_csv, export_access_records_excel

# Export users to CSV
response = export_users_csv(User.objects.all())

# Export access records to Excel
response = export_access_records_excel(AccessRecord.objects.filter(is_active=True))
```

### Import Utilities

```python
from utils.importers import import_users_from_csv

# Import users from CSV
results = import_users_from_csv(csv_file)
# Returns: {'created': 10, 'updated': 5, 'errors': []}
```

## Template Tags

### Custom Template Tags

```python
# templatetags/dict_extras.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
```

**Usage in templates**:

```html
{% load dict_extras %}
{{ my_dict|get_item:"key" }}
```

## Management Commands

### Available Commands

```bash
# Create superuser
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Create migrations
python manage.py makemigrations

# Collect static files
python manage.py collectstatic

# Shell access
python manage.py shell

# Database shell
python manage.py dbshell
```

### Custom Commands

```python
# management/commands/my_command.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Description of command'

    def add_arguments(self, parser):
        parser.add_argument('--option', type=str)

    def handle(self, *args, **options):
        # Command logic
        self.stdout.write(self.style.SUCCESS('Command executed'))
```

## Settings Reference

### Key Settings

```python
# settings.py

# Database
DATABASES = {...}

# Security
SECRET_KEY = '...'
DEBUG = False
ALLOWED_HOSTS = [...]

# Authentication
AUTH_USER_MODEL = 'accounts.User'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
```

## URL Patterns

### URL Configuration

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('departments/', include('departments.urls')),
    path('systems/', include('systems.urls')),
    path('access/', include('access_management.urls')),
    path('api/', include('api.urls')),
]
```

## Error Handling

### Common Exceptions

```python
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404

# Validation error
raise ValidationError('Invalid data')

# Permission denied
raise PermissionDenied('Access denied')

# Not found
raise Http404('Object not found')
```

## Next Steps

- [Development](development.md) - Development guidelines
- [Data Model](data_model.md) - Database schema
- [Administration](administration.md) - Administrative tasks

---

For implementation examples, see the [Development](development.md) documentation.


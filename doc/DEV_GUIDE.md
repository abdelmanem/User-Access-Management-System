# Developer Guide
## User Access Management System (UAMS)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Development Setup](#development-setup)
4. [Project Structure](#project-structure)
5. [Database Models](#database-models)
6. [API & Views](#api-views)
7. [Authentication & Permissions](#authentication-permissions)
8. [Templates & Frontend](#templates-frontend)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## Project Overview

The User Access Management System (UAMS) is a Django-based web application designed to document and manage:
- User/Employee information with detailed profiles
- Organizational structure (departments and sub-departments)
- System access tracking and documentation
- Access history and audit trails

**Key Principle**: This is a **DOCUMENTATION SYSTEM** - not an access request/approval workflow. Administrators directly document who has access to what systems.

### Technology Stack

- **Backend**: Django 5.2.8
- **Frontend**: HTML5, CSS3, Bootstrap 4, JavaScript, Chart.js
- **Database**: SQLite (development), PostgreSQL (production ready)
- **Authentication**: Django's built-in authentication system
- **Icons**: Font Awesome
- **Python**: 3.8+

---

## Architecture

### Application Structure

The project follows Django's app-based architecture:

```
user_access_management/     # Main project settings
├── accounts/               # User management
├── departments/            # Department management
├── systems/                # System/application management
├── access_management/      # Access assignment and history
├── dashboard/              # Dashboard and analytics
├── data_import_export/     # Import/export functionality
├── search/                 # Search functionality
├── hardware/               # Hardware asset management
└── utils/                  # Utility functions
```

### Design Patterns

- **MVC Pattern**: Django follows Model-View-Template (MVT) pattern
- **Permission-Based Access Control**: Role-based permissions using Django's permission system
- **Audit Trail**: Comprehensive logging of all changes
- **Soft Deletes**: User deactivation instead of hard deletion

---

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)
- Git

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd User-Access-Management-System
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy example file
   cp env.example .env
   
   # Generate secret key
   python generate_secret_key.py
   # Copy the generated key to .env file
   ```

5. **Configure database**
   ```bash
   # For SQLite (default)
   # No additional configuration needed
   
   # For PostgreSQL
   # Set DATABASE_URL in .env file
   # DATABASE_URL=postgres://user:password@localhost:5432/dbname
   ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Main application: http://127.0.0.1:8000/
   - Admin interface: http://127.0.0.1:8000/admin/
   - Dashboard: http://127.0.0.1:8000/dashboard/

---

## Project Structure

### Main Applications

#### accounts/
User management application
- **Models**: `CustomUser`, `UserDeactivationAudit`, `UserArchive`
- **Views**: User CRUD operations, password reset, permissions management
- **Forms**: `UserCreateForm`, `UserUpdateForm`, `UserPermissionForm`
- **URLs**: `/users/` routes

#### departments/
Department management application
- **Models**: `Department`
- **Views**: Department CRUD operations
- **Forms**: `DepartmentForm`
- **URLs**: `/departments/` routes

#### systems/
System/application management
- **Models**: `System`
- **Views**: System CRUD operations
- **Forms**: `SystemForm`
- **URLs**: `/systems/` routes

#### access_management/
Access assignment and tracking
- **Models**: `UserSystemAccess`, `AccessHistory`
- **Views**: Access assignment CRUD, history viewing
- **URLs**: `/access-management/` routes

#### dashboard/
Dashboard and analytics
- **Views**: Dashboard statistics, charts, reports
- **Templates**: Dashboard views with Chart.js
- **URLs**: `/dashboard/` routes

#### data_import_export/
Data import/export functionality
- **Utils**: CSV/Excel importers and exporters
- **Views**: Import/export interfaces
- **URLs**: `/data-import-export/` routes

#### search/
Global search functionality
- **Views**: Search across users, departments, systems
- **Utils**: Search utilities
- **URLs**: `/search/` routes

### Key Files

```
manage.py                    # Django management script
requirements.txt             # Python dependencies
env.example                  # Environment variables template
user_access_management/
  ├── settings.py           # Django settings
  ├── urls.py               # Main URL configuration
  ├── wsgi.py               # WSGI configuration
  └── asgi.py               # ASGI configuration
templates/
  ├── base.html             # Base template
  └── navigation.html       # Navigation menu
static/
  └── css/
      └── custom_admin.css  # Custom admin styles
media/
  └── profiles/             # User profile photos
```

---

## Database Models

### CustomUser Model

Extended Django user model with additional fields:

```python
# Key fields:
- employee_id (CharField, unique)
- national_id (CharField, encrypted)
- phone_primary (CharField)
- phone_secondary (CharField)
- personal_email (EmailField)
- position (CharField)
- employment_type (ChoiceField)
- employment_status (ChoiceField)
- join_date (DateField)
- department (ForeignKey to Department)
- reports_to (ForeignKey to CustomUser)
- profile_photo (ImageField)
- notes (TextField)
```

**Location**: `accounts/models.py`

### Department Model

```python
# Key fields:
- name (CharField, unique)
- description (TextField)
- parent (ForeignKey, self-referential)
- is_active (BooleanField)
```

**Location**: `departments/models.py`

### System Model

```python
# Key fields:
- name (CharField)
- code (CharField, unique)
- description (TextField)
- category (ChoiceField)
- vendor (CharField)
- url (URLField)
- is_active (BooleanField)
```

**Location**: `systems/models.py`

### UserSystemAccess Model

Junction table linking users to systems:

```python
# Key fields:
- user (ForeignKey to CustomUser)
- system (ForeignKey to System)
- access_type (ChoiceField)
- status (ChoiceField)
- priority (ChoiceField)
- request_type (ChoiceField)
- access_start_date (DateTimeField)
- access_end_date (DateTimeField)
```

**Location**: `access_management/models.py`

---

## API & Views

### View Patterns

The application uses function-based views with decorators:

```python
@login_required
@permission_required('app.permission', raise_exception=True)
def view_name(request, pk):
    # View logic
    return render(request, 'template.html', context)
```

### Common Decorators

- `@login_required`: Requires user authentication
- `@permission_required`: Checks specific permissions
- `@user_passes_test`: Custom user validation

### URL Configuration

URLs are organized by app:

```python
# Main urls.py
urlpatterns = [
    path('', include('accounts.urls')),
    path('departments/', include('departments.urls')),
    path('systems/', include('systems.urls')),
    path('access-management/', include('access_management.urls')),
    path('dashboard/', include('dashboard.urls')),
]
```

### Media Files Serving

In development, media files are served via:

```python
# urls.py
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Important**: In production, configure your web server (Nginx/Apache) to serve media files.

---

## Authentication & Permissions

### User Roles

1. **Super Admin**
   - Full system access
   - All permissions

2. **HR Admin**
   - User management
   - Department management
   - Import/export

3. **Access Administrator**
   - System management
   - Access assignment
   - Cannot delete users

4. **Department Manager**
   - View department users
   - View department access
   - Read-only for other departments

5. **Viewer**
   - Read-only access
   - No edit capabilities

### Permission System

Django's built-in permission system is used:

```python
# Check permissions in views
@permission_required('accounts.add_customuser', raise_exception=True)

# Check in templates
{% if perms.accounts.add_customuser %}
    <!-- Content -->
{% endif %}
```

### Custom Permissions

Permissions are defined in models:

```python
class Meta:
    permissions = [
        ('can_manage_access', 'Can manage system access'),
    ]
```

---

## Templates & Frontend

### Template Structure

```
templates/
├── base.html              # Base template with navigation
├── accounts/              # User templates
├── departments/           # Department templates
├── systems/               # System templates
└── access_management/    # Access templates
```

### Base Template

All templates extend `base.html`:

```django
{% extends 'base.html' %}
{% load static %}

{% block title %}Page Title{% endblock %}

{% block content %}
    <!-- Content -->
{% endblock %}
```

### Static Files

- **CSS**: Bootstrap 4, custom styles
- **JavaScript**: Chart.js, custom scripts
- **Icons**: Font Awesome

### Media Files

User profile photos are stored in:
- **Path**: `media/profiles/`
- **URL**: `/media/profiles/filename.png`
- **Settings**: `MEDIA_ROOT` and `MEDIA_URL` in settings.py

---

## Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts

# Run specific test
python manage.py test accounts.tests.UserModelTest
```

### Test Structure

Tests are located in each app's `tests.py`:

```python
from django.test import TestCase
from accounts.models import CustomUser

class UserModelTest(TestCase):
    def setUp(self):
        # Setup test data
        
    def test_user_creation(self):
        # Test logic
        pass
```

### Test Coverage

Use coverage.py to measure test coverage:

```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
coverage html  # Generate HTML report
```

---

## Deployment

### Production Checklist

1. **Environment Variables**
   - Set `DEBUG=False`
   - Set strong `SECRET_KEY`
   - Configure `ALLOWED_HOSTS`
   - Set `CSRF_TRUSTED_ORIGINS`

2. **Database**
   - Use PostgreSQL in production
   - Set up database backups
   - Configure connection pooling

3. **Static Files**
   - Run `python manage.py collectstatic`
   - Configure static file serving (Nginx/WhiteNoise)

4. **Media Files**
   - Configure web server to serve media files
   - Consider using cloud storage (S3, etc.)

5. **Security**
   - Enable HTTPS
   - Configure security headers
   - Set up logging and monitoring

### WSGI Server

Use Gunicorn or uWSGI:

```bash
# Gunicorn
gunicorn user_access_management.wsgi:application

# With systemd
# See README.md for systemd service configuration
```

### Web Server Configuration

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    location /static/ {
        alias /path/to/staticfiles/;
    }
    
    location /media/ {
        alias /path/to/media/;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. Media Files Not Loading

**Problem**: Profile photos show 404 errors

**Solution**:
- Check `MEDIA_URL` and `MEDIA_ROOT` in settings.py
- Ensure media serving is configured in urls.py (development)
- Configure web server to serve media files (production)

#### 2. Permission Denied Errors

**Problem**: Users can't access certain features

**Solution**:
- Check user permissions: `user.has_perm('app.permission')`
- Verify permission decorators on views
- Check template permission checks

#### 3. Database Migration Issues

**Problem**: Migrations fail or are out of sync

**Solution**:
```bash
# Reset migrations (development only!)
python manage.py migrate --fake accounts zero
python manage.py migrate accounts

# Or create fresh migrations
python manage.py makemigrations
python manage.py migrate
```

#### 4. Static Files Not Found

**Problem**: CSS/JS files return 404

**Solution**:
```bash
# Collect static files
python manage.py collectstatic

# Check STATIC_URL and STATIC_ROOT in settings.py
# Verify static file serving configuration
```

#### 5. Import Errors

**Problem**: Module not found errors

**Solution**:
- Ensure virtual environment is activated
- Install all requirements: `pip install -r requirements.txt`
- Check Python path and imports

### Debugging Tips

1. **Enable Debug Mode** (development only)
   ```python
   DEBUG = True
   ```

2. **Check Logs**
   ```bash
   # Django logs
   tail -f logs/django.log
   
   # Server logs
   journalctl -u uams -f
   ```

3. **Django Debug Toolbar** (development)
   ```bash
   pip install django-debug-toolbar
   # Add to INSTALLED_APPS and configure
   ```

4. **Database Queries**
   ```python
   from django.db import connection
   print(connection.queries)
   ```

---

## Additional Resources

### Django Documentation
- Official Django Docs: https://docs.djangoproject.com/
- Django Best Practices: https://docs.djangoproject.com/en/stable/misc/design-philosophies/

### Project-Specific
- See `requirements_doc.md` for detailed requirements
- See `README.md` for installation and usage

### Code Style
- Follow PEP 8 for Python code
- Use Django's coding style guidelines
- Format with Black or autopep8

---

## Contributing

### Development Workflow

1. Create a feature branch
2. Make changes
3. Write/update tests
4. Run tests and linting
5. Commit changes
6. Push and create pull request

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed

---

**Last Updated**: 2024
**Version**: 1.0.0


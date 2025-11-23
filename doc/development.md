# Development

This guide covers development practices, setup, and contribution guidelines for UAMS.

![Development](../images/development.png)

## Development Overview

UAMS is built with Django and follows Django best practices. This guide covers:

- Development environment setup
- Code structure and conventions
- Testing practices
- Contribution guidelines
- Release process

## Development Environment Setup

### Prerequisites

- Python 3.8 or higher
- pip and virtualenv
- Git
- PostgreSQL (optional, SQLite for development)
- IDE or text editor

### Setup Steps

#### 1. Clone Repository

```bash
git clone https://github.com/abdelmanem/User-Access-Management-System.git
cd User-Access-Management-System
```

#### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt

# For development, install additional packages
pip install -r requirements-dev.txt
```

#### 4. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit .env with development settings
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
```

#### 5. Run Migrations

```bash
python manage.py migrate
```

#### 6. Create Superuser

```bash
python manage.py createsuperuser
```

#### 7. Run Development Server

```bash
python manage.py runserver
```

## Project Structure

### Directory Structure

```
User-Access-Management-System/
├── accounts/              # User management app
├── departments/           # Department management app
├── systems/               # System management app
├── access_management/     # Access management app
├── dashboard/             # Dashboard app
├── data_import_export/     # Import/export functionality
├── hardware/              # Hardware management
├── service_accounts/      # Service account management
├── default_accounts/      # Default account management
├── change_management/     # Change management
├── user_access_management/ # Main project settings
├── templates/             # Project templates
├── static/                # Static files
├── media/                 # Media files
├── doc/                   # Documentation
├── tests/                 # Test files
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── README.md             # Project README
```

### App Structure

Each Django app follows this structure:

```
app_name/
├── __init__.py
├── admin.py              # Django admin configuration
├── apps.py               # App configuration
├── models.py             # Database models
├── views.py              # View functions/classes
├── urls.py               # URL routing
├── forms.py              # Form definitions
├── templates/            # App templates
│   └── app_name/
├── static/               # App static files
│   └── app_name/
├── management/           # Management commands
│   └── commands/
├── templatetags/         # Custom template tags
├── tests.py              # Test cases
└── migrations/           # Database migrations
```

## Code Style and Conventions

### Python Style

Follow PEP 8 style guide:

```python
# Use 4 spaces for indentation
# Maximum line length: 88 characters (Black formatter)
# Use descriptive variable names
# Add docstrings to functions and classes

def calculate_user_access_count(user):
    """
    Calculate the number of active access records for a user.
    
    Args:
        user: User instance
        
    Returns:
        int: Number of active access records
    """
    return AccessRecord.objects.filter(
        user=user,
        is_active=True
    ).count()
```

### Django Conventions

- Use class-based views when appropriate
- Use model forms for model-related forms
- Use Django's built-in authentication
- Follow Django naming conventions
- Use migrations for database changes

### Import Organization

```python
# Standard library imports
import os
from datetime import datetime

# Third-party imports
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Local application imports
from accounts.models import User
from access_management.models import AccessRecord
```

## Testing

### Test Structure

```python
# tests.py or tests/test_models.py
from django.test import TestCase
from accounts.models import User
from access_management.models import AccessRecord

class UserModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
    
    def test_user_creation(self):
        """Test user creation"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertTrue(self.user.is_active)
    
    def test_user_full_name(self):
        """Test user full name method"""
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.assertEqual(self.user.get_full_name(), 'John Doe')
```

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts

# Run specific test class
python manage.py test accounts.tests.UserModelTest

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Test Best Practices

1. **Isolation**: Each test should be independent
2. **Setup/Teardown**: Use setUp and tearDown methods
3. **Naming**: Use descriptive test names
4. **Coverage**: Aim for high test coverage
5. **Speed**: Keep tests fast

## Database Migrations

### Creating Migrations

```bash
# Create migrations for all apps
python manage.py makemigrations

# Create migration for specific app
python manage.py makemigrations accounts

# Create empty migration
python manage.py makemigrations --empty accounts
```

### Migration Best Practices

1. **Review Migrations**: Always review generated migrations
2. **Test Migrations**: Test migrations on development data
3. **Data Migrations**: Use data migrations for data changes
4. **Backward Compatibility**: Ensure backward compatibility
5. **Documentation**: Document complex migrations

### Data Migrations

```python
# migrations/0002_update_user_roles.py
from django.db import migrations

def update_user_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(is_staff=True).update(role='admin')

def reverse_update(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='admin').update(is_staff=True)

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
    ]
    
    operations = [
        migrations.RunPython(update_user_roles, reverse_update),
    ]
```

## Version Control

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push to remote
git push origin feature/new-feature

# Create pull request
```

### Commit Messages

Follow conventional commit format:

```
feat: Add user export functionality
fix: Fix access record deletion bug
docs: Update installation guide
refactor: Refactor user model methods
test: Add tests for access management
```

### Branch Naming

- `feature/`: New features
- `fix/`: Bug fixes
- `docs/`: Documentation updates
- `refactor/`: Code refactoring
- `test/`: Test additions/updates

## Code Review

### Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling is appropriate
- [ ] Code is well-commented

## Debugging

### Django Debug Toolbar

Install and configure Django Debug Toolbar:

```bash
pip install django-debug-toolbar
```

```python
# settings.py
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

```python
# In code
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info('Function called')
    try:
        # Code
    except Exception as e:
        logger.error(f'Error: {e}', exc_info=True)
```

## Performance Optimization

### Database Optimization

```python
# Use select_related for ForeignKey
users = User.objects.select_related('department').all()

# Use prefetch_related for reverse relations
departments = Department.objects.prefetch_related('user_set').all()

# Use only() to limit fields
users = User.objects.only('username', 'email')

# Use defer() to exclude fields
users = User.objects.defer('profile_photo')
```

### Caching

```python
from django.core.cache import cache

def get_user_access_count(user_id):
    cache_key = f'user_access_count_{user_id}'
    count = cache.get(cache_key)
    
    if count is None:
        count = AccessRecord.objects.filter(
            user_id=user_id,
            is_active=True
        ).count()
        cache.set(cache_key, count, 3600)  # Cache for 1 hour
    
    return count
```

## Security Considerations

### Input Validation

```python
from django.core.exceptions import ValidationError

def validate_email_domain(value):
    allowed_domains = ['example.com', 'company.com']
    domain = value.split('@')[1]
    if domain not in allowed_domains:
        raise ValidationError('Email domain not allowed')
```

### SQL Injection Prevention

Always use Django ORM or parameterized queries:

```python
# Good: Use ORM
users = User.objects.filter(username=username)

# Bad: Raw SQL without parameters
users = User.objects.raw(f"SELECT * FROM users WHERE username = '{username}'")
```

### XSS Prevention

Django templates automatically escape variables:

```html
<!-- Automatically escaped -->
{{ user_input }}

<!-- If you need to mark as safe -->
{{ user_input|safe }}
```

## Documentation

### Code Documentation

```python
def grant_access(user, system, access_level, granted_by):
    """
    Grant access to a user for a system.
    
    Args:
        user: User instance
        system: System instance
        access_level: Access level string
        granted_by: User who is granting access
        
    Returns:
        AccessRecord: Created access record
        
    Raises:
        ValidationError: If access already exists
    """
    # Implementation
```

### API Documentation

Document API endpoints:

```python
# api/views.py
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users.
    
    list:
    Return a list of all users.
    
    retrieve:
    Return a specific user.
    
    create:
    Create a new user.
    """
```

## Release Process

### Version Numbering

Follow semantic versioning: MAJOR.MINOR.PATCH

- **MAJOR**: Breaking changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Version number updated
- [ ] CHANGELOG updated
- [ ] Migration files reviewed
- [ ] Security review completed
- [ ] Performance tested

### Creating a Release

```bash
# Update version
# Create release branch
git checkout -b release/1.0.0

# Tag release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Next Steps

- [Reference](reference.md) - API and technical reference
- [Data Model](data_model.md) - Database schema
- [Best Practices](best_practices.md) - Recommended practices

---

For contribution guidelines, see the project's CONTRIBUTING.md file.


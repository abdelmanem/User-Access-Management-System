# Configuration

This guide covers configuring UAMS for your organization's needs.

![Configuration](../images/configuration.png)

## Configuration Overview

UAMS configuration is managed through:

- **Environment Variables**: `.env` file for settings
- **Django Settings**: `settings.py` for application configuration
- **Database**: Database records for organizational data
- **Admin Interface**: Django admin for runtime configuration

## Environment Configuration

### Environment File

UAMS uses a `.env` file for environment-specific settings. Copy `env.example` to `.env`:

```bash
cp env.example .env
```

### Required Settings

#### SECRET_KEY

Django secret key for cryptographic signing:

```env
SECRET_KEY=your-very-long-random-secret-key-here
```

**Generate a secret key**:

```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

#### DEBUG

Enable/disable debug mode:

```env
# Development
DEBUG=True

# Production
DEBUG=False
```

#### ALLOWED_HOSTS

Comma-separated list of allowed hostnames:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com,www.yourdomain.com
```

#### DATABASE_URL

Database connection string:

```env
# SQLite (development)
DATABASE_URL=sqlite:///db.sqlite3

# PostgreSQL (production)
DATABASE_URL=postgresql://user:password@localhost:5432/uams_db
```

### Optional Settings

#### CSRF_TRUSTED_ORIGINS

Trusted origins for CSRF protection:

```env
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### USE_WHITENOISE

Enable WhiteNoise for static file serving:

```env
USE_WHITENOISE=True
```

#### SENTRY_DSN

Sentry error tracking (optional):

```env
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
```

## Django Settings Configuration

### Database Configuration

Edit `user_access_management/settings.py`:

```python
# SQLite (development)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# PostgreSQL (production)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'uams_db',
        'USER': 'uams_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Static Files Configuration

```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### Email Configuration

```python
# SMTP Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'UAMS <noreply@yourdomain.com>'
```

**Environment variables**:

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=UAMS <noreply@yourdomain.com>
```

### Time Zone Configuration

```python
TIME_ZONE = 'America/New_York'
USE_TZ = True
```

### Language Configuration

```python
LANGUAGE_CODE = 'en-us'
USE_I18N = True
USE_L10N = True
```

### Logging Configuration

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'uams.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

## Application Configuration

### User Roles

Configure user roles in Django admin or via management command:

```python
from accounts.models import User

# Create role groups
from django.contrib.auth.models import Group

super_admin_group, _ = Group.objects.get_or_create(name='Super Admin')
hr_admin_group, _ = Group.objects.get_or_create(name='HR Admin')
access_admin_group, _ = Group.objects.get_or_create(name='Access Administrator')
dept_manager_group, _ = Group.objects.get_or_create(name='Department Manager')
viewer_group, _ = Group.objects.get_or_create(name='Viewer')
```

### Department Structure

Set up your organizational structure:

```python
from departments.models import Department

# Create top-level departments
it_dept = Department.objects.create(
    name='IT Department',
    description='Information Technology',
    code='IT'
)

hr_dept = Department.objects.create(
    name='HR Department',
    description='Human Resources',
    code='HR'
)

# Create sub-departments
dev_team = Department.objects.create(
    name='Development Team',
    description='Software Development',
    parent=it_dept,
    code='IT-DEV'
)
```

### System Categories

Define system categories:

```python
from systems.models import System

# System categories can be configured via choices
SYSTEM_CATEGORIES = [
    ('Critical', 'Critical'),
    ('Important', 'Important'),
    ('Standard', 'Standard'),
    ('Low', 'Low Priority'),
]

SYSTEM_TYPES = [
    ('Database', 'Database'),
    ('Application', 'Application'),
    ('Platform', 'Platform'),
    ('Service', 'Service'),
]
```

### Access Levels

Configure access levels per system:

```python
from systems.models import System

system = System.objects.create(
    name='Customer Database',
    access_levels=['Read', 'Write', 'Admin', 'Owner']
)
```

## Security Configuration

### Password Policies

Configure password requirements:

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

### Session Configuration

```python
# Session settings
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
```

### CSRF Configuration

```python
CSRF_COOKIE_SECURE = True  # HTTPS only
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
    'https://www.yourdomain.com',
]
```

### Security Headers

```python
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Performance Configuration

### Caching

Configure caching for better performance:

```python
# Redis cache (recommended for production)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Or use database cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache_table',
    }
}
```

### Database Connection Pooling

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'uams_db',
        'USER': 'uams_user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # Connection pooling
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}
```

## Integration Configuration

### Active Directory (Future)

```python
# LDAP Configuration (when implemented)
AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_LDAP_SERVER_URI = "ldap://ldap.example.com"
AUTH_LDAP_BIND_DN = "cn=admin,dc=example,dc=com"
AUTH_LDAP_BIND_PASSWORD = "password"
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=users,dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"
)
```

### Email Notifications

```python
# Notification settings
NOTIFICATION_EMAIL_ENABLED = True
NOTIFICATION_EMAIL_FROM = 'UAMS <noreply@yourdomain.com>'
NOTIFICATION_EMAIL_BCC = ['admin@yourdomain.com']
```

### API Configuration

```python
# REST Framework settings (if using API)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100
}
```

## Customization Configuration

### Custom Branding

```python
# Custom branding settings
SITE_NAME = "Your Organization UAMS"
SITE_DESCRIPTION = "User Access Management System"
LOGO_URL = "/static/images/logo.png"
FAVICON_URL = "/static/images/favicon.ico"
```

### Custom Fields

Extend models with custom fields:

```python
# In models.py
class User(AbstractUser):
    # Add custom fields
    employee_id = models.CharField(max_length=50, unique=True)
    hire_date = models.DateField(null=True, blank=True)
    custom_field_1 = models.CharField(max_length=255, blank=True)
```

### Custom Workflows

Configure custom approval workflows:

```python
# Workflow configuration
ACCESS_APPROVAL_WORKFLOW = {
    'require_manager_approval': True,
    'require_hr_approval': False,
    'auto_approve_departments': ['IT Department'],
}
```

## Backup Configuration

### Automated Backups

Configure automated backups:

```python
# Backup settings
BACKUP_ENABLED = True
BACKUP_SCHEDULE = '0 2 * * *'  # Daily at 2 AM
BACKUP_RETENTION_DAYS = 30
BACKUP_LOCATION = '/backups/uams/'
```

### Database Backup Script

```bash
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/uams"
DB_NAME="uams_db"
DB_USER="uams_user"

# Create backup
pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress
gzip $BACKUP_DIR/backup_$DATE.sql

# Remove old backups (older than 30 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

## Monitoring Configuration

### Health Check Endpoint

```python
# In urls.py
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({
        'status': 'healthy',
        'database': 'connected',
        'timestamp': timezone.now().isoformat()
    })
```

### Error Tracking

```python
# Sentry configuration
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True
    )
```

## Configuration Validation

### Settings Check

Create a management command to validate configuration:

```python
# management/commands/check_config.py
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    def handle(self, *args, **options):
        # Check required settings
        if settings.DEBUG and not settings.ALLOWED_HOSTS:
            self.stdout.write(self.style.WARNING('DEBUG is True but ALLOWED_HOSTS is empty'))
        
        # Check database connection
        from django.db import connection
        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS('Database connection OK'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database connection failed: {e}'))
```

Run validation:

```bash
python manage.py check_config
```

## Configuration Best Practices

1. **Use Environment Variables**: Never hardcode secrets
2. **Separate Environments**: Use different `.env` files for dev/staging/prod
3. **Version Control**: Keep `settings.py` in version control, not `.env`
4. **Documentation**: Document all custom configurations
5. **Testing**: Test configuration changes in staging first
6. **Backup**: Backup configuration before changes
7. **Security**: Review security settings regularly

## Next Steps

- [Customization](customization.md) - Customize UAMS further
- [Administration](administration.md) - Learn administration tasks
- [Best Practices](best_practices.md) - Recommended practices
- [Development](development.md) - Development configuration

---

For production deployment configuration, see [Installation & Upgrade](installation_upgrade.md). For customization options, see [Customization](customization.md).


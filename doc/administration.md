# Administration

This guide covers administrative tasks for managing and maintaining UAMS.

![Administration](../images/administration.png)

## Administration Overview

UAMS administration involves:

- **User Management**: Creating and managing user accounts
- **System Configuration**: Configuring system settings
- **Data Management**: Managing data and backups
- **Security**: Security administration
- **Monitoring**: System monitoring and maintenance
- **Troubleshooting**: Resolving issues

## User Administration

### Creating Users

#### Via Admin Interface

1. Navigate to Django Admin: `/admin/`
2. Go to **Accounts** → **Users**
3. Click **Add User**
4. Fill in user information:
   - Username
   - Password
   - Email
   - First Name
   - Last Name
5. Assign groups/permissions
6. Click **Save**

#### Via Management Command

```bash
python manage.py createsuperuser
```

#### Via Python Shell

```python
from accounts.models import User
from departments.models import Department

# Create user
user = User.objects.create_user(
    username='jdoe',
    email='jdoe@example.com',
    password='secure_password',
    first_name='John',
    last_name='Doe',
    department=Department.objects.get(name='IT Department')
)
```

### Managing User Roles

#### Assigning Roles

```python
from django.contrib.auth.models import Group
from accounts.models import User

# Get role groups
super_admin_group = Group.objects.get(name='Super Admin')
hr_admin_group = Group.objects.get(name='HR Admin')

# Assign role
user = User.objects.get(username='jdoe')
user.groups.add(hr_admin_group)
user.is_staff = True
user.save()
```

#### Role Permissions

```python
from django.contrib.auth.models import Permission

# Grant specific permission
permission = Permission.objects.get(codename='add_user')
user.user_permissions.add(permission)
```

### User Account Management

#### Activating/Deactivating Users

```python
# Deactivate user
user = User.objects.get(username='jdoe')
user.is_active = False
user.save()

# Activate user
user.is_active = True
user.save()
```

#### Resetting Passwords

```bash
# Via management command
python manage.py changepassword username
```

```python
# Via Python shell
from accounts.models import User

user = User.objects.get(username='jdoe')
user.set_password('new_password')
user.save()
```

## System Configuration

### Django Settings

Edit `user_access_management/settings.py` for system-wide configuration:

```python
# Database settings
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

# Security settings
SECRET_KEY = 'your-secret-key'
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

### Environment Configuration

Manage configuration via `.env` file:

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@localhost:5432/uams_db
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
```

## Data Management

### Database Backups

#### Manual Backup

```bash
# PostgreSQL
pg_dump -U uams_user uams_db > backup_$(date +%Y%m%d).sql

# SQLite
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```

#### Django Dumpdata

```bash
# Full backup
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Specific app
python manage.py dumpdata accounts > accounts_backup.json

# Exclude certain models
python manage.py dumpdata --exclude auth.permission --exclude contenttypes > backup.json
```

#### Automated Backups

Create backup script:

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/uams"
DB_NAME="uams_db"
DB_USER="uams_user"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz media/

# Remove old backups (older than 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

Schedule with cron:

```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

### Database Restoration

#### From SQL Dump

```bash
# PostgreSQL
psql -U uams_user uams_db < backup_20240101.sql

# SQLite
cp backup_20240101.sqlite3 db.sqlite3
```

#### From Django Fixture

```bash
python manage.py loaddata backup_20240101.json
```

### Data Import/Export

#### Exporting Data

```bash
# Export users
python manage.py dumpdata accounts.User > users.json

# Export access records
python manage.py dumpdata access_management.AccessRecord > access.json
```

#### Importing Data

```bash
# Import data
python manage.py loaddata users.json
```

## Security Administration

### Security Hardening

#### Password Policies

```python
# settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
]
```

#### Session Security

```python
# settings.py
SESSION_COOKIE_SECURE = True  # HTTPS only
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
```

#### CSRF Protection

```python
# settings.py
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = [
    'https://yourdomain.com',
]
```

### Security Auditing

#### Review User Access

```python
from access_management.models import AccessRecord
from django.utils import timezone
from datetime import timedelta

# Find users with excessive access
users_with_many_access = User.objects.annotate(
    access_count=Count('accessrecord')
).filter(access_count__gt=10)

# Find stale access (not reviewed in 90 days)
stale_access = AccessRecord.objects.filter(
    is_active=True,
    last_reviewed_date__lt=timezone.now().date() - timedelta(days=90)
)
```

#### Audit Log Review

```python
from django.contrib.admin.models import LogEntry

# Recent admin actions
recent_actions = LogEntry.objects.filter(
    action_time__gte=timezone.now() - timedelta(days=7)
).order_by('-action_time')
```

## Monitoring

### System Health Checks

#### Database Connection

```python
from django.db import connection

try:
    connection.ensure_connection()
    print("Database connection OK")
except Exception as e:
    print(f"Database connection failed: {e}")
```

#### Application Status

Create health check endpoint:

```python
# urls.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    status = {
        'status': 'healthy',
        'database': 'connected',
        'timestamp': timezone.now().isoformat(),
    }
    
    try:
        connection.ensure_connection()
    except:
        status['status'] = 'unhealthy'
        status['database'] = 'disconnected'
    
    return JsonResponse(status)
```

### Log Monitoring

#### View Logs

```bash
# Application logs
tail -f logs/uams.log

# Error logs
tail -f logs/error.log

# Access logs (if using Nginx)
tail -f /var/log/nginx/access.log
```

#### Log Rotation

Configure log rotation in `/etc/logrotate.d/uams`:

```
/path/to/uams/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
}
```

### Performance Monitoring

#### Database Query Analysis

```python
# Enable query logging
from django.db import connection

connection.queries_log.clear()
# ... perform operations ...
print(connection.queries)
```

#### Application Metrics

```python
# Monitor access grants
from access_management.models import AccessRecord
from django.utils import timezone
from datetime import timedelta

# Access grants in last 24 hours
recent_grants = AccessRecord.objects.filter(
    granted_date__gte=timezone.now() - timedelta(days=1)
).count()
```

## Maintenance Tasks

### Database Maintenance

#### Run Migrations

```bash
# Check migration status
python manage.py showmigrations

# Apply migrations
python manage.py migrate

# Create new migration
python manage.py makemigrations
```

#### Database Optimization

```bash
# PostgreSQL
psql -U uams_user uams_db -c "VACUUM ANALYZE;"

# SQLite
sqlite3 db.sqlite3 "VACUUM;"
```

### Static Files

#### Collect Static Files

```bash
python manage.py collectstatic --noinput
```

#### Clear Cache

```bash
# Clear Django cache
python manage.py clear_cache
```

### Cleanup Tasks

#### Remove Old Data

```python
# Remove old access history (older than 2 years)
from access_management.models import AccessRecord
from django.utils import timezone
from datetime import timedelta

old_records = AccessRecord.objects.filter(
    revoked_date__lt=timezone.now() - timedelta(days=730),
    is_active=False
)
old_records.delete()
```

## Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Check database is running
sudo systemctl status postgresql

# Test connection
python manage.py dbshell
```

#### Migration Errors

```bash
# Check migration status
python manage.py showmigrations

# Fake migration (use with caution)
python manage.py migrate --fake app_name migration_name
```

#### Static Files Not Loading

```bash
# Recollect static files
python manage.py collectstatic --noinput --clear

# Check permissions
chmod -R 755 staticfiles/
```

#### Permission Errors

```bash
# Fix file permissions
chown -R www-data:www-data /path/to/uams
chmod -R 755 /path/to/uams
```

### Debugging

#### Enable Debug Mode

```python
# settings.py (development only)
DEBUG = True
```

#### View Error Details

```python
# In views
import logging
logger = logging.getLogger(__name__)

def my_view(request):
    try:
        # ... code ...
    except Exception as e:
        logger.error(f'Error: {e}', exc_info=True)
        raise
```

## Backup and Recovery

### Backup Strategy

1. **Daily Backups**: Database and media files
2. **Weekly Backups**: Full system backup
3. **Before Upgrades**: Pre-upgrade backup
4. **Offsite Storage**: Store backups offsite

### Recovery Procedures

#### Full System Recovery

1. Restore database
2. Restore media files
3. Restore configuration
4. Verify application
5. Test functionality

#### Partial Recovery

```bash
# Restore specific app data
python manage.py loaddata accounts_backup.json
```

## Next Steps

- [Configuration](configuration.md) - System configuration
- [Best Practices](best_practices.md) - Recommended practices
- [Development](development.md) - Development guidelines
- [Reference](reference.md) - Technical reference

---

For detailed configuration options, see [Configuration](configuration.md). For security best practices, see [Best Practices](best_practices.md).


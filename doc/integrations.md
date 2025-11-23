# Integrations

This guide covers integrating UAMS with external systems and services.

![Integrations](../images/integrations.png)

## Integration Overview

UAMS can integrate with various external systems to enhance functionality and automate processes:

- **Active Directory / LDAP**: User authentication and synchronization
- **Email Systems**: Notification delivery
- **SIEM Systems**: Security event logging
- **Ticketing Systems**: Change request integration
- **Monitoring Systems**: Health checks and alerts
- **API Integrations**: RESTful API access

## Active Directory / LDAP Integration

### Overview

Active Directory integration allows UAMS to:

- Authenticate users against AD
- Synchronize user information
- Map AD groups to UAMS roles
- Auto-provision users

### Configuration

Install required packages:

```bash
pip install django-auth-ldap
```

### Settings Configuration

```python
# settings.py
import ldap
from django_auth_ldap.config import LDAPSearch, GroupOfNamesType

AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# LDAP Server Configuration
AUTH_LDAP_SERVER_URI = "ldap://ldap.example.com:389"
AUTH_LDAP_BIND_DN = "cn=admin,dc=example,dc=com"
AUTH_LDAP_BIND_PASSWORD = "password"

# User Search
AUTH_LDAP_USER_SEARCH = LDAPSearch(
    "ou=users,dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(uid=%(user)s)"
)

# User Attributes
AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

# Group Configuration
AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    "ou=groups,dc=example,dc=com",
    ldap.SCOPE_SUBTREE,
    "(objectClass=groupOfNames)"
)

AUTH_LDAP_GROUP_TYPE = GroupOfNamesType()

# Group to Role Mapping
AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_staff": "cn=staff,ou=groups,dc=example,dc=com",
    "is_superuser": "cn=admins,ou=groups,dc=example,dc=com",
}

# Role Mapping
AUTH_LDAP_MIRROR_GROUPS = True
```

### User Synchronization

Create a management command to sync users:

```python
# management/commands/sync_ldap_users.py
from django.core.management.base import BaseCommand
from django_auth_ldap.backend import LDAPBackend
from accounts.models import User

class Command(BaseCommand):
    help = 'Synchronize users from LDAP'

    def handle(self, *args, **options):
        ldap_backend = LDAPBackend()
        
        # Get all users from LDAP
        # This is a simplified example
        # In practice, you'd query LDAP directly
        
        synced = 0
        created = 0
        
        # Sync logic here
        self.stdout.write(
            self.style.SUCCESS(
                f'Synced {synced} users, created {created} new users'
            )
        )
```

## Email Integration

### SMTP Configuration

Configure SMTP for email notifications:

```python
# settings.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'UAMS <noreply@yourdomain.com>'
```

### Email Notifications

Create email notification service:

```python
# utils/notifications.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def send_access_grant_notification(access_record):
    """Send notification when access is granted"""
    subject = f'Access Granted: {access_record.system.name}'
    
    context = {
        'user': access_record.user,
        'system': access_record.system,
        'access_level': access_record.access_level,
        'granted_by': access_record.granted_by,
    }
    
    message = render_to_string('emails/access_granted.html', context)
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [access_record.user.email],
        html_message=message,
        fail_silently=False,
    )

def send_access_review_reminder(review_task):
    """Send reminder for access review"""
    subject = f'Access Review Required: {review_task.access_record.system.name}'
    
    context = {
        'review_task': review_task,
        'access_record': review_task.access_record,
    }
    
    message = render_to_string('emails/review_reminder.html', context)
    
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [review_task.assigned_to.email],
        html_message=message,
        fail_silently=False,
    )
```

### Email Templates

Create email templates:

```html
<!-- templates/emails/access_granted.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Access Granted</title>
</head>
<body>
    <h2>Access Granted</h2>
    <p>Hello {{ user.get_full_name }},</p>
    <p>You have been granted access to <strong>{{ system.name }}</strong>.</p>
    <p><strong>Access Level:</strong> {{ access_level }}</p>
    <p><strong>Granted By:</strong> {{ granted_by.get_full_name }}</p>
    <p>If you have any questions, please contact your system administrator.</p>
</body>
</html>
```

## SIEM Integration

### Overview

Integrate with Security Information and Event Management (SIEM) systems to log access events.

### Event Logging

Create SIEM event logger:

```python
# utils/siem_logger.py
import requests
import json
from django.conf import settings
from django.utils import timezone

def log_access_event(event_type, access_record, user, details=None):
    """
    Log access event to SIEM system
    """
    event = {
        'timestamp': timezone.now().isoformat(),
        'event_type': event_type,  # 'access_granted', 'access_revoked', etc.
        'user': {
            'username': user.username,
            'email': user.email,
            'department': user.department.name if user.department else None,
        },
        'system': {
            'name': access_record.system.name,
            'type': access_record.system.system_type,
        },
        'access_level': access_record.access_level,
        'details': details or {},
    }
    
    # Send to SIEM endpoint
    if hasattr(settings, 'SIEM_ENDPOINT'):
        try:
            response = requests.post(
                settings.SIEM_ENDPOINT,
                json=event,
                headers={'Authorization': f'Bearer {settings.SIEM_API_KEY}'},
                timeout=5
            )
            response.raise_for_status()
        except Exception as e:
            # Log error but don't fail the operation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'SIEM logging failed: {e}')

# Usage in views
from utils.siem_logger import log_access_event

def grant_access(request, user_id, system_id):
    # ... grant access logic ...
    log_access_event('access_granted', access_record, request.user)
```

### Configuration

```python
# settings.py
SIEM_ENDPOINT = 'https://siem.example.com/api/events'
SIEM_API_KEY = 'your-api-key-here'
```

## Ticketing System Integration

### Overview

Integrate with ticketing systems (Jira, ServiceNow, etc.) to create tickets for access requests and changes.

### Jira Integration

```python
# utils/jira_integration.py
import requests
from django.conf import settings

def create_access_request_ticket(access_request):
    """
    Create Jira ticket for access request
    """
    jira_url = f"{settings.JIRA_URL}/rest/api/2/issue"
    
    issue_data = {
        'fields': {
            'project': {'key': settings.JIRA_PROJECT_KEY},
            'summary': f'Access Request: {access_request.user.get_full_name()} - {access_request.system.name}',
            'description': f'''
            User: {access_request.user.get_full_name()}
            System: {access_request.system.name}
            Access Level: {access_request.access_level}
            Justification: {access_request.justification}
            ''',
            'issuetype': {'name': 'Access Request'},
            'priority': {'name': 'Medium'},
        }
    }
    
    response = requests.post(
        jira_url,
        json=issue_data,
        auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN),
        headers={'Content-Type': 'application/json'},
    )
    
    if response.status_code == 201:
        issue_key = response.json()['key']
        access_request.ticket_id = issue_key
        access_request.save()
        return issue_key
    
    return None
```

### Configuration

```python
# settings.py
JIRA_URL = 'https://yourcompany.atlassian.net'
JIRA_USERNAME = 'your-email@example.com'
JIRA_API_TOKEN = 'your-api-token'
JIRA_PROJECT_KEY = 'UAMS'
```

## Monitoring Integration

### Health Check Endpoint

Create health check endpoint for monitoring:

```python
# user_access_management/urls.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """Health check endpoint for monitoring"""
    status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        connection.ensure_connection()
        status['checks']['database'] = 'ok'
    except Exception as e:
        status['checks']['database'] = f'error: {str(e)}'
        status['status'] = 'unhealthy'
    
    # Add more checks as needed
    
    status_code = 200 if status['status'] == 'healthy' else 503
    return JsonResponse(status, status=status_code)
```

### Prometheus Metrics

```python
# utils/metrics.py
from prometheus_client import Counter, Histogram

access_grants_total = Counter(
    'uams_access_grants_total',
    'Total number of access grants',
    ['system', 'access_level']
)

access_revokes_total = Counter(
    'uams_access_revokes_total',
    'Total number of access revocations',
    ['system']
)

access_review_duration = Histogram(
    'uams_access_review_duration_seconds',
    'Time spent on access reviews'
)

# Usage
from utils.metrics import access_grants_total

access_grants_total.labels(
    system=system.name,
    access_level=access_level
).inc()
```

## API Integration

### REST API

UAMS can expose a REST API for programmatic access:

```python
# api/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from accounts.models import User
from access_management.models import AccessRecord

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    @action(detail=True, methods=['get'])
    def access(self, request, pk=None):
        """Get access records for a user"""
        user = self.get_object()
        access_records = AccessRecord.objects.filter(user=user)
        serializer = AccessRecordSerializer(access_records, many=True)
        return Response(serializer.data)

class AccessRecordViewSet(viewsets.ModelViewSet):
    queryset = AccessRecord.objects.all()
    serializer_class = AccessRecordSerializer
    permission_classes = [IsAuthenticated]
```

### API Authentication

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

## Webhook Integration

### Outgoing Webhooks

Send webhooks when events occur:

```python
# utils/webhooks.py
import requests
from django.conf import settings

def send_webhook(event_type, data):
    """
    Send webhook to configured endpoint
    """
    webhook_url = settings.WEBHOOK_URL
    
    payload = {
        'event_type': event_type,
        'timestamp': timezone.now().isoformat(),
        'data': data,
    }
    
    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Authorization': f'Bearer {settings.WEBHOOK_SECRET}'},
            timeout=5
        )
        response.raise_for_status()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Webhook failed: {e}')

# Usage
from utils.webhooks import send_webhook

def grant_access(request, user_id, system_id):
    # ... grant access ...
    send_webhook('access_granted', {
        'user': user.username,
        'system': system.name,
        'access_level': access_level,
    })
```

## Integration Best Practices

1. **Error Handling**: Implement robust error handling
2. **Retry Logic**: Add retry logic for transient failures
3. **Logging**: Log all integration activities
4. **Monitoring**: Monitor integration health
5. **Testing**: Test integrations thoroughly
6. **Documentation**: Document all integrations
7. **Security**: Secure integration endpoints
8. **Rate Limiting**: Implement rate limiting
9. **Timeouts**: Set appropriate timeouts
10. **Fallbacks**: Implement fallback mechanisms

## Next Steps

- [Additional Integrations](additional_integrations/integrations.md) - More integration options
- [Configuration](configuration.md) - Configure integrations
- [Development](development.md) - Development guidelines
- [Reference](reference.md) - API reference

---

For specific integration implementations, see the [Additional Integrations](additional_integrations/integrations.md) documentation.


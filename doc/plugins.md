# Plugins

This guide covers developing and using plugins to extend UAMS functionality.

![Plugins](../images/plugins.png)

## Plugin Overview

UAMS supports a plugin architecture that allows you to extend functionality without modifying core code. Plugins can add:

- Custom workflows
- Additional integrations
- Custom reports
- New features
- UI extensions

## Plugin Architecture

### Plugin Structure

A UAMS plugin is a Django app that follows a specific structure:

```
my_plugin/
├── __init__.py
├── apps.py
├── models.py
├── views.py
├── urls.py
├── templates/
│   └── my_plugin/
├── static/
│   └── my_plugin/
├── management/
│   └── commands/
└── plugin_config.py
```

### Plugin Configuration

Each plugin must have a `plugin_config.py` file:

```python
# my_plugin/plugin_config.py
PLUGIN_CONFIG = {
    'name': 'My Plugin',
    'version': '1.0.0',
    'description': 'Description of my plugin',
    'author': 'Your Name',
    'dependencies': [],  # List of required plugins
    'hooks': {
        'access_granted': 'my_plugin.hooks.on_access_granted',
        'access_revoked': 'my_plugin.hooks.on_access_revoked',
    },
    'menu_items': [
        {
            'label': 'My Plugin',
            'url': 'my_plugin:index',
            'icon': 'fa-cog',
        }
    ],
}
```

## Creating a Plugin

### Step 1: Create Plugin App

```bash
python manage.py startapp my_plugin
```

### Step 2: Configure Plugin

Create `plugin_config.py`:

```python
# my_plugin/plugin_config.py
PLUGIN_CONFIG = {
    'name': 'Custom Workflow Plugin',
    'version': '1.0.0',
    'description': 'Adds custom approval workflows',
    'author': 'Your Organization',
    'hooks': {
        'access_granted': 'my_plugin.hooks.on_access_granted',
    },
}
```

### Step 3: Register Plugin

In `my_plugin/apps.py`:

```python
# my_plugin/apps.py
from django.apps import AppConfig

class MyPluginConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_plugin'
    verbose_name = 'My Plugin'
    
    def ready(self):
        # Register plugin
        from . import plugin_config
        import uams.plugins
        uams.plugins.register(plugin_config.PLUGIN_CONFIG)
```

### Step 4: Install Plugin

Add to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'my_plugin',
]
```

## Plugin Hooks

### Available Hooks

Plugins can hook into various UAMS events:

- `access_granted`: When access is granted
- `access_revoked`: When access is revoked
- `user_created`: When a user is created
- `user_updated`: When a user is updated
- `review_completed`: When an access review is completed

### Implementing Hooks

Create `my_plugin/hooks.py`:

```python
# my_plugin/hooks.py
from django.utils import timezone
from django.core.mail import send_mail

def on_access_granted(access_record, **kwargs):
    """
    Hook called when access is granted
    """
    # Custom logic here
    send_notification(access_record)
    log_to_external_system(access_record)

def on_access_revoked(access_record, **kwargs):
    """
    Hook called when access is revoked
    """
    # Custom logic here
    cleanup_external_access(access_record)

def send_notification(access_record):
    """Send custom notification"""
    send_mail(
        subject=f'Access Granted: {access_record.system.name}',
        message=f'Access has been granted to {access_record.system.name}',
        from_email='noreply@example.com',
        recipient_list=[access_record.user.email],
    )

def log_to_external_system(access_record):
    """Log to external system"""
    # Integration logic here
    pass
```

## Plugin Views

### Creating Plugin Views

```python
# my_plugin/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

@login_required
def plugin_index(request):
    """Plugin main page"""
    context = {
        'title': 'My Plugin',
    }
    return render(request, 'my_plugin/index.html', context)

@login_required
@require_http_methods(["GET", "POST"])
def custom_action(request):
    """Custom plugin action"""
    if request.method == 'POST':
        # Handle POST
        pass
    return render(request, 'my_plugin/action.html')
```

### Plugin URLs

```python
# my_plugin/urls.py
from django.urls import path
from . import views

app_name = 'my_plugin'

urlpatterns = [
    path('', views.plugin_index, name='index'),
    path('action/', views.custom_action, name='action'),
]
```

## Plugin Templates

### Template Structure

```
my_plugin/
└── templates/
    └── my_plugin/
        ├── index.html
        ├── action.html
        └── partials/
            └── widget.html
```

### Base Template Extension

```html
<!-- my_plugin/templates/my_plugin/index.html -->
{% extends "base.html" %}
{% load static %}

{% block title %}My Plugin{% endblock %}

{% block content %}
<div class="container">
    <h1>My Plugin</h1>
    <p>Plugin content goes here</p>
</div>
{% endblock %}
```

## Plugin Models

### Custom Models

```python
# my_plugin/models.py
from django.db import models
from access_management.models import AccessRecord

class CustomAccessMetadata(models.Model):
    """Custom metadata for access records"""
    access_record = models.OneToOneField(
        AccessRecord,
        on_delete=models.CASCADE,
        related_name='custom_metadata'
    )
    custom_field_1 = models.CharField(max_length=255, blank=True)
    custom_field_2 = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Metadata for {self.access_record}"
```

## Plugin Management Commands

### Creating Commands

```python
# my_plugin/management/commands/my_plugin_command.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'My plugin management command'

    def add_arguments(self, parser):
        parser.add_argument(
            '--option',
            type=str,
            help='Command option',
        )

    def handle(self, *args, **options):
        option = options['option']
        self.stdout.write(
            self.style.SUCCESS(f'Command executed with option: {option}')
        )
```

## Plugin API

### Exposing Plugin API

```python
# my_plugin/api.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class PluginAPIViewSet(viewsets.ViewSet):
    """
    Plugin API endpoints
    """
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get plugin status"""
        return Response({
            'status': 'active',
            'version': '1.0.0',
        })
    
    @action(detail=False, methods=['post'])
    def custom_action(self, request):
        """Custom API action"""
        # Process request
        return Response({'result': 'success'})
```

## Plugin Menu Integration

### Adding Menu Items

Plugins can add items to the main navigation:

```python
# my_plugin/plugin_config.py
PLUGIN_CONFIG = {
    # ... other config ...
    'menu_items': [
        {
            'label': 'My Plugin',
            'url': 'my_plugin:index',
            'icon': 'fa-cog',
            'permission': 'my_plugin.view_plugin',
        },
        {
            'label': 'Plugin Settings',
            'url': 'my_plugin:settings',
            'icon': 'fa-gear',
            'permission': 'my_plugin.change_settings',
        }
    ],
}
```

## Plugin Permissions

### Defining Permissions

```python
# my_plugin/models.py
from django.db import models

class PluginPermission(models.Model):
    """Plugin-specific permissions"""
    class Meta:
        permissions = [
            ('view_plugin', 'Can view plugin'),
            ('use_plugin', 'Can use plugin features'),
            ('admin_plugin', 'Can administer plugin'),
        ]
```

### Checking Permissions

```python
# my_plugin/views.py
from django.contrib.auth.decorators import permission_required

@permission_required('my_plugin.view_plugin')
def plugin_view(request):
    # View logic
    pass
```

## Plugin Settings

### Plugin Configuration

```python
# my_plugin/settings.py
PLUGIN_SETTINGS = {
    'enabled': True,
    'api_key': '',
    'webhook_url': '',
    'custom_option': 'default_value',
}
```

### Settings Management

```python
# my_plugin/views.py
from django.conf import settings

def get_plugin_setting(key, default=None):
    """Get plugin setting"""
    plugin_settings = getattr(settings, 'MY_PLUGIN_SETTINGS', {})
    return plugin_settings.get(key, default)
```

## Plugin Testing

### Writing Tests

```python
# my_plugin/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from access_management.models import AccessRecord

User = get_user_model()

class PluginTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
    
    def test_plugin_hook(self):
        """Test plugin hook execution"""
        # Test hook logic
        pass
    
    def test_plugin_view(self):
        """Test plugin view"""
        self.client.force_login(self.user)
        response = self.client.get('/my_plugin/')
        self.assertEqual(response.status_code, 200)
```

## Plugin Distribution

### Packaging Plugin

Create `setup.py`:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name='uams-my-plugin',
    version='1.0.0',
    description='My UAMS Plugin',
    author='Your Name',
    packages=find_packages(),
    install_requires=[
        'Django>=3.2',
    ],
)
```

### Installing Plugin

```bash
pip install uams-my-plugin
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'my_plugin',
]
```

## Plugin Examples

### Example: Notification Plugin

```python
# notification_plugin/plugin_config.py
PLUGIN_CONFIG = {
    'name': 'Notification Plugin',
    'version': '1.0.0',
    'hooks': {
        'access_granted': 'notification_plugin.hooks.send_grant_notification',
        'access_revoked': 'notification_plugin.hooks.send_revoke_notification',
    },
}

# notification_plugin/hooks.py
from django.core.mail import send_mail

def send_grant_notification(access_record, **kwargs):
    send_mail(
        subject=f'Access Granted: {access_record.system.name}',
        message=f'You have been granted {access_record.access_level} access to {access_record.system.name}',
        from_email='noreply@example.com',
        recipient_list=[access_record.user.email],
    )
```

### Example: Reporting Plugin

```python
# reporting_plugin/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def custom_report(request):
    """Generate custom report"""
    # Report generation logic
    context = {
        'report_data': generate_report_data(),
    }
    return render(request, 'reporting_plugin/report.html', context)
```

## Plugin Best Practices

1. **Namespace**: Use unique plugin names
2. **Documentation**: Document plugin functionality
3. **Testing**: Write comprehensive tests
4. **Error Handling**: Handle errors gracefully
5. **Performance**: Optimize plugin performance
6. **Security**: Follow security best practices
7. **Compatibility**: Ensure compatibility with UAMS versions
8. **Updates**: Plan for plugin updates
9. **Dependencies**: Minimize dependencies
10. **Configuration**: Make plugins configurable

## Next Steps

- [Development](development.md) - Development guidelines
- [Customization](customization.md) - Customization options
- [Reference](reference.md) - API reference
- [Integrations](integrations.md) - Integration guides

---

For plugin development examples, see the [Development](development.md) documentation.


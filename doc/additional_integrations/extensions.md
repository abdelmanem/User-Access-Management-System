# Extensions

This guide covers creating and managing extensions for UAMS.

![Extensions](../images/extensions.png)

## Extensions Overview

Extensions allow you to extend UAMS functionality without modifying core code. Extensions can add:

- New features
- Custom workflows
- Additional integrations
- UI enhancements
- Reporting capabilities

## Extension Types

### Feature Extensions

Add new features to UAMS:

- Custom access workflows
- Additional reporting
- New data models
- Enhanced UI components

### Integration Extensions

Integrate with external systems:

- Third-party APIs
- External databases
- Cloud services
- Legacy systems

### Workflow Extensions

Customize business workflows:

- Approval processes
- Notification rules
- Automation scripts
- Scheduled tasks

## Creating Extensions

### Extension Structure

```
my_extension/
├── __init__.py
├── extension_config.py
├── models.py
├── views.py
├── urls.py
├── templates/
├── static/
└── management/
```

### Extension Configuration

```python
# extension_config.py
EXTENSION_CONFIG = {
    'name': 'My Extension',
    'version': '1.0.0',
    'description': 'Description of extension',
    'author': 'Your Name',
    'dependencies': [],
    'hooks': {
        'access_granted': 'my_extension.hooks.on_access_granted',
    },
    'menu_items': [
        {
            'label': 'My Extension',
            'url': 'my_extension:index',
        }
    ],
}
```

## Extension Development

### Basic Extension

```python
# my_extension/__init__.py
default_app_config = 'my_extension.apps.MyExtensionConfig'

# my_extension/apps.py
from django.apps import AppConfig

class MyExtensionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'my_extension'
    verbose_name = 'My Extension'
    
    def ready(self):
        # Register extension
        from . import extension_config
        import uams.extensions
        uams.extensions.register(extension_config.EXTENSION_CONFIG)
```

### Extension Views

```python
# my_extension/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def extension_index(request):
    context = {
        'title': 'My Extension',
    }
    return render(request, 'my_extension/index.html', context)
```

### Extension URLs

```python
# my_extension/urls.py
from django.urls import path
from . import views

app_name = 'my_extension'

urlpatterns = [
    path('', views.extension_index, name='index'),
]
```

## Extension Hooks

### Available Hooks

Extensions can hook into UAMS events:

- `access_granted`: When access is granted
- `access_revoked`: When access is revoked
- `user_created`: When a user is created
- `user_updated`: When a user is updated
- `review_completed`: When a review is completed

### Implementing Hooks

```python
# my_extension/hooks.py
def on_access_granted(access_record, **kwargs):
    """Handle access granted event"""
    # Extension logic here
    pass

def on_access_revoked(access_record, **kwargs):
    """Handle access revoked event"""
    # Extension logic here
    pass
```

## Extension Best Practices

1. **Namespace**: Use unique extension names
2. **Documentation**: Document extension functionality
3. **Testing**: Write comprehensive tests
4. **Error Handling**: Handle errors gracefully
5. **Performance**: Optimize extension performance
6. **Security**: Follow security best practices
7. **Compatibility**: Ensure compatibility with UAMS versions

## Extension Distribution

### Packaging

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name='uams-my-extension',
    version='1.0.0',
    description='My UAMS Extension',
    packages=find_packages(),
    install_requires=[
        'Django>=3.2',
    ],
)
```

### Installation

```bash
pip install uams-my-extension
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'my_extension',
]
```

## Next Steps

- [Plugins](../plugins.md) - Plugin development guide
- [Development](../development.md) - Development guidelines
- [Customization](../customization.md) - Customization options

---

For plugin development, see the [Plugins](../plugins.md) documentation.


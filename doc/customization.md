# Customization

This guide covers customizing UAMS to fit your organization's specific needs.

![Customization](../images/customization.png)

## Customization Overview

UAMS can be customized in several ways:

- **Templates**: Customize HTML templates
- **Styling**: Modify CSS and themes
- **Models**: Extend data models
- **Workflows**: Customize business logic
- **Integrations**: Add custom integrations
- **Branding**: Add organization branding

## Template Customization

### Overriding Templates

Django's template system allows you to override default templates. Create a `templates` directory in your project root:

```
project_root/
├── templates/
│   ├── base.html          # Override base template
│   ├── accounts/
│   │   └── user_detail.html
│   └── access_management/
│       └── access_list.html
```

### Custom Base Template

Create `templates/base.html`:

```html
{% extends "base.html" %}

{% block title %}Your Organization - UAMS{% endblock %}

{% block branding %}
<div class="navbar-brand">
    <img src="{% static 'images/your-logo.png' %}" alt="Your Organization">
    <span>UAMS</span>
</div>
{% endblock %}

{% block navigation %}
<!-- Custom navigation menu -->
<nav class="navbar">
    <ul class="nav">
        <li><a href="{% url 'dashboard' %}">Dashboard</a></li>
        <li><a href="{% url 'user_list' %}">Users</a></li>
        <!-- Add custom menu items -->
    </ul>
</nav>
{% endblock %}
```

### Custom User Profile Template

Create `templates/accounts/user_detail.html`:

```html
{% extends "base.html" %}
{% load static %}

{% block content %}
<div class="user-profile">
    <div class="profile-header">
        <img src="{{ user.profile_photo.url }}" alt="{{ user.get_full_name }}">
        <h1>{{ user.get_full_name }}</h1>
        <p>{{ user.department.name }}</p>
    </div>
    
    <div class="profile-details">
        <h2>Contact Information</h2>
        <p>Email: {{ user.email }}</p>
        <p>Phone: {{ user.phone }}</p>
        
        <!-- Add custom fields -->
        <h2>Custom Information</h2>
        <p>Employee ID: {{ user.employee_id }}</p>
        <p>Hire Date: {{ user.hire_date }}</p>
    </div>
</div>
{% endblock %}
```

## Styling Customization

### Custom CSS

Create `static/css/custom.css`:

```css
/* Custom branding colors */
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --accent-color: #e74c3c;
    --background-color: #ecf0f1;
}

/* Custom header */
.navbar {
    background-color: var(--primary-color);
    color: white;
}

.navbar-brand {
    font-size: 1.5rem;
    font-weight: bold;
}

/* Custom buttons */
.btn-primary {
    background-color: var(--secondary-color);
    border-color: var(--secondary-color);
}

.btn-primary:hover {
    background-color: #2980b9;
}

/* Custom cards */
.card {
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Custom dashboard */
.dashboard-stat {
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    padding: 20px;
    border-radius: 8px;
}
```

Include in your base template:

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/custom.css' %}">
```

### Theme Customization

Create a theme configuration file:

```python
# settings.py
THEME_CONFIG = {
    'primary_color': '#2c3e50',
    'secondary_color': '#3498db',
    'logo_url': '/static/images/logo.png',
    'favicon_url': '/static/images/favicon.ico',
    'site_name': 'Your Organization UAMS',
}
```

## Model Customization

### Extending User Model

Create custom user fields:

```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Add custom fields
    employee_id = models.CharField(max_length=50, unique=True, null=True)
    hire_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    # Custom fields
    custom_field_1 = models.CharField(max_length=255, blank=True)
    custom_field_2 = models.TextField(blank=True)
    custom_field_3 = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'accounts_user'
```

Update settings:

```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'
```

### Extending Department Model

```python
# departments/models.py
from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)
    manager = models.ForeignKey('accounts.User', null=True, blank=True, on_delete=models.SET_NULL)
    
    # Custom fields
    cost_center = models.CharField(max_length=50, blank=True)
    budget_code = models.CharField(max_length=50, blank=True)
    location = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return self.name
```

### Extending System Model

```python
# systems/models.py
from django.db import models

class System(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    system_type = models.CharField(max_length=50)
    category = models.CharField(max_length=50)
    
    # Custom fields
    vendor = models.CharField(max_length=100, blank=True)
    version = models.CharField(max_length=50, blank=True)
    support_contact = models.EmailField(blank=True)
    documentation_url = models.URLField(blank=True)
    compliance_required = models.BooleanField(default=False)
    
    def __str__(self):
        return self.name
```

## Workflow Customization

### Custom Approval Workflow

Create custom approval logic:

```python
# access_management/workflows.py
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

def custom_approval_workflow(access_record, request):
    """
    Custom approval workflow for access grants
    """
    # Check if manager approval is required
    if access_record.user.department.manager:
        if not access_record.approved_by:
            # Send notification to manager
            send_approval_notification(
                access_record.user.department.manager,
                access_record
            )
            return False  # Pending approval
    
    # Auto-approve for certain departments
    auto_approve_departments = ['IT Department', 'Security Team']
    if access_record.user.department.name in auto_approve_departments:
        access_record.approved_by = request.user
        access_record.approved_date = timezone.now()
        access_record.save()
        return True
    
    # Default: require approval
    return False

def send_approval_notification(manager, access_record):
    """Send approval notification email"""
    from django.core.mail import send_mail
    
    subject = f'Access Approval Required: {access_record.user.get_full_name()}'
    message = f'''
    Approval required for access grant:
    
    User: {access_record.user.get_full_name()}
    System: {access_record.system.name}
    Access Level: {access_record.access_level}
    
    Please review and approve at: {access_record.get_approval_url()}
    '''
    
    send_mail(
        subject,
        message,
        'noreply@yourdomain.com',
        [manager.email],
        fail_silently=False,
    )
```

### Custom Review Workflow

```python
# access_management/reviews.py
from django.utils import timezone
from datetime import timedelta

def quarterly_review_workflow():
    """
    Custom quarterly access review workflow
    """
    # Get all active access records
    from access_management.models import AccessRecord
    
    active_access = AccessRecord.objects.filter(is_active=True)
    
    for access in active_access:
        # Check if review is due
        last_review = access.last_reviewed_date or access.granted_date
        days_since_review = (timezone.now().date() - last_review).days
        
        if days_since_review >= 90:  # 90 days = quarterly
            # Create review task
            create_review_task(access)
            
def create_review_task(access_record):
    """Create a review task for an access record"""
    from access_management.models import ReviewTask
    
    ReviewTask.objects.create(
        access_record=access_record,
        assigned_to=access_record.user.department.manager,
        due_date=timezone.now().date() + timedelta(days=30),
        status='pending'
    )
```

## Integration Customization

### Custom API Endpoints

Create custom API views:

```python
# api/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    Custom user API with additional endpoints
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    @action(detail=True, methods=['get'])
    def access_summary(self, request, pk=None):
        """Get access summary for a user"""
        user = self.get_object()
        access_records = AccessRecord.objects.filter(user=user, is_active=True)
        
        summary = {
            'user': user.get_full_name(),
            'total_access': access_records.count(),
            'systems': [ar.system.name for ar in access_records],
            'by_level': {}
        }
        
        for record in access_records:
            level = record.access_level
            summary['by_level'][level] = summary['by_level'].get(level, 0) + 1
        
        return Response(summary)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update users"""
        user_ids = request.data.get('user_ids', [])
        updates = request.data.get('updates', {})
        
        updated = User.objects.filter(id__in=user_ids).update(**updates)
        
        return Response({
            'updated': updated,
            'message': f'Updated {updated} users'
        })
```

### Custom Export Formats

```python
# utils/exporters.py
import csv
import json
from django.http import HttpResponse

def export_users_custom_format(users, format='json'):
    """
    Custom export format for users
    """
    if format == 'json':
        data = []
        for user in users:
            data.append({
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'department': user.department.name if user.department else None,
                'role': user.role,
                'employee_id': user.employee_id,
            })
        
        response = HttpResponse(
            json.dumps(data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="users_export.json"'
        return response
    
    elif format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="users_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Username', 'Email', 'Full Name', 'Department', 'Role', 'Employee ID'])
        
        for user in users:
            writer.writerow([
                user.username,
                user.email,
                user.get_full_name(),
                user.department.name if user.department else '',
                user.role,
                user.employee_id,
            ])
        
        return response
```

## Branding Customization

### Logo and Favicon

1. Add logo to `static/images/logo.png`
2. Add favicon to `static/images/favicon.ico`
3. Update base template:

```html
{% load static %}
<link rel="icon" type="image/x-icon" href="{% static 'images/favicon.ico' %}">

<div class="navbar-brand">
    <img src="{% static 'images/logo.png' %}" alt="Logo" height="40">
    <span>Your Organization UAMS</span>
</div>
```

### Custom Footer

```html
<!-- templates/base.html -->
<footer class="footer">
    <div class="container">
        <p>&copy; {% now "Y" %} Your Organization. All rights reserved.</p>
        <p>
            <a href="/privacy">Privacy Policy</a> |
            <a href="/terms">Terms of Service</a> |
            <a href="/contact">Contact</a>
        </p>
    </div>
</footer>
```

## Custom Fields in Forms

### Custom User Form

```python
# accounts/forms.py
from django import forms
from .models import User

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 
                  'department', 'employee_id', 'hire_date', 'phone']
        widgets = {
            'hire_date': forms.DateInput(attrs={'type': 'date'}),
            'phone': forms.TextInput(attrs={'placeholder': '+1 (555) 123-4567'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom validation or styling
        self.fields['employee_id'].required = True
```

## Custom Reports

### Custom Report Template

```python
# reporting/custom_reports.py
from django.db.models import Count, Q
from access_management.models import AccessRecord

def generate_custom_access_report(department=None, start_date=None, end_date=None):
    """
    Generate custom access report
    """
    queryset = AccessRecord.objects.filter(is_active=True)
    
    if department:
        queryset = queryset.filter(user__department=department)
    
    if start_date:
        queryset = queryset.filter(granted_date__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(granted_date__lte=end_date)
    
    # Aggregate data
    by_system = queryset.values('system__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    by_level = queryset.values('access_level').annotate(
        count=Count('id')
    )
    
    return {
        'total_records': queryset.count(),
        'by_system': list(by_system),
        'by_level': list(by_level),
        'department': department.name if department else 'All Departments',
    }
```

## Custom Permissions

### Custom Permission Classes

```python
# accounts/permissions.py
from rest_framework import permissions

class IsDepartmentManager(permissions.BasePermission):
    """
    Custom permission to only allow department managers
    """
    def has_permission(self, request, view):
        return request.user and request.user.role == 'department_manager'
    
    def has_object_permission(self, request, view, obj):
        # Department managers can only access their department
        if hasattr(obj, 'department'):
            return obj.department == request.user.department
        return False
```

## Best Practices

1. **Version Control**: Keep all customizations in version control
2. **Documentation**: Document all customizations
3. **Testing**: Test customizations thoroughly
4. **Backup**: Backup before making changes
5. **Modularity**: Keep customizations modular and reusable
6. **Migration**: Create migrations for model changes
7. **Compatibility**: Ensure compatibility with future updates

## Next Steps

- [Configuration](configuration.md) - Configure custom settings
- [Development](development.md) - Development guidelines
- [Best Practices](best_practices.md) - Recommended practices
- [Reference](reference.md) - API and technical reference

---

For advanced customization, see the [Developer Guide](development.md) and [Reference](reference.md) documentation.


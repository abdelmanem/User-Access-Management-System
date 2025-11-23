# Introduction

The User Access Management System (UAMS) is a comprehensive Django-based web application designed to help organizations document, manage, and govern user access to various systems and applications within their infrastructure.

![UAMS Architecture](../images/architecture-overview.png)

## What is UAMS?

UAMS serves as a centralized documentation and management platform for:

- **User Access Documentation**: Track who has access to which systems
- **Organizational Management**: Manage users, departments, and organizational structure
- **Compliance & Governance**: Maintain audit trails and support compliance requirements
- **Access Reviews**: Conduct periodic access reviews and certifications
- **Service Account Governance**: Manage service accounts and default accounts

### Core Principle

UAMS is fundamentally a **documentation system** rather than an access request/approval workflow. Administrators directly document who has access to what systems, providing a clear audit trail and supporting compliance requirements.

## System Architecture

### Application Structure

UAMS follows Django's app-based architecture:

```
user_access_management/          # Main project settings
├── accounts/                     # User management
├── departments/                  # Department management
├── systems/                      # System/application management
├── access_management/            # Access assignment and history
├── dashboard/                    # Dashboard and analytics
├── data_import_export/           # Import/export functionality
├── search/                       # Search functionality
├── hardware/                     # Hardware asset management
├── service_accounts/             # Service account management
├── default_accounts/             # Default account management
└── change_management/            # Change management workflows
```

### Technology Stack

#### Backend

- **Framework**: Django 5.2.8
- **Language**: Python 3.8+
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Django's built-in authentication system
- **API**: Django REST Framework (optional)

#### Frontend

- **HTML5/CSS3**: Modern web standards
- **Bootstrap 4**: Responsive UI framework
- **JavaScript**: Interactive functionality
- **Chart.js**: Data visualization
- **Font Awesome**: Icon library

#### Deployment

- **WSGI Server**: Gunicorn
- **Web Server**: Nginx
- **Containerization**: Docker
- **Process Management**: Systemd or Supervisor

## Key Concepts

### Users

Users represent employees or individuals within your organization. Each user has:

- Profile information (name, email, photo, etc.)
- Department assignment
- Role and permissions
- Access assignments to various systems

### Departments

Departments represent organizational units. UAMS supports:

- Hierarchical department structure
- Unlimited nesting levels
- Department-specific access views
- Department manager roles

### Systems

Systems represent applications, platforms, or services that users can access:

- System name and description
- System type and category
- Access level definitions
- Integration information

### Access Management

Access records document:

- Which users have access to which systems
- Access levels and permissions
- Grant and revocation dates
- Approval and certification status
- Historical changes

### Service Accounts

Service accounts are non-human accounts used by applications:

- Service account identification
- Owner assignment
- Purpose documentation
- Review and certification cycles

## Use Cases

### Access Documentation

Document and maintain a complete record of user access to systems:

```python
# Example: Documenting user access
from access_management.models import AccessRecord

access = AccessRecord.objects.create(
    user=user,
    system=system,
    access_level='Read',
    granted_date=timezone.now(),
    granted_by=admin_user,
    notes='Access granted for project work'
)
```

### Compliance Reporting

Generate reports for compliance audits:

- Quarterly access reviews
- Administrator access certifications
- Service account inventories
- Access change history

### Organizational Management

Maintain organizational structure:

- Department hierarchy
- User assignments
- Manager relationships
- Organizational charts

### Access Reviews

Conduct periodic access reviews:

- Review user access assignments
- Certify access appropriateness
- Identify and remove unnecessary access
- Document review decisions

## System Capabilities

### Documentation Features

- **Comprehensive User Profiles**: Detailed employee information with photos
- **System Catalog**: Complete inventory of systems and applications
- **Access History**: Complete audit trail of all access changes
- **Change Tracking**: Document all modifications with timestamps

### Management Features

- **Bulk Operations**: Import/export users, departments, and access data
- **Search Functionality**: Quick search across all data
- **Dashboard Analytics**: Visual charts and statistics
- **Reporting**: Generate reports in multiple formats

### Governance Features

- **Access Reviews**: Quarterly and periodic review workflows
- **Compliance Playbooks**: Pre-defined compliance procedures
- **Policy Enforcement**: Policy drift detection and scheduling
- **Change Management**: Structured change request workflows

## Integration Points

UAMS can integrate with:

- **Active Directory**: User synchronization (future)
- **LDAP**: Authentication and user lookup
- **SIEM Systems**: Access event logging
- **Ticketing Systems**: Change request integration
- **Email Systems**: Notification delivery

See the [Integrations](integrations.md) documentation for detailed integration guides.

## Security Considerations

UAMS implements several security features:

- **Authentication**: Secure user authentication
- **Authorization**: Role-based access control
- **CSRF Protection**: Cross-site request forgery protection
- **Audit Logging**: Complete audit trail
- **Data Encryption**: Sensitive data protection

## Getting Started

To begin using UAMS:

1. Review the [Installation & Upgrade](installation_upgrade.md) guide
2. Complete the [Getting Started](getting_started.md) tutorial
3. Configure the system per [Configuration](configuration.md)
4. Review [Best Practices](best_practices.md) for recommended workflows

## Next Steps

- [Features](features.md) - Explore all UAMS features
- [Getting Started](getting_started.md) - Begin using the system
- [Configuration](configuration.md) - Configure UAMS for your organization
- [Administration](administration.md) - Learn system administration

---

For technical details, see the [Developer Guide](development.md) and [Data Model](data_model.md) documentation.


# UAMS - Quick Reference & App Overview

## System at a Glance

**User Access Management System (UAMS)** is a comprehensive Django-based platform managing user access across IT systems.

```
11 Applications | 20+ Models | 100+ Views | Full Audit Trail | GDPR Ready
```

---

## Applications Overview Table

| App | Purpose | Key Models | Key Features |
|-----|---------|-----------|--------------|
| **Accounts** 👤 | User Management | CustomUser, Profile | LDAP sync, encryption, roles, profile mgmt |
| **Departments** 🏢 | Organization | Department | Hierarchical tree, head assignment, cost tracking |
| **Systems** 🖥️ | IT Registry | System, SystemOwner | Multi-type support, risk scoring, criticality levels |
| **Access** 🔐 | Core Access Control | UserSystemAccess, AccessHistory | Request workflow, approvals, expiration, audit |
| **Change Mgmt** ✅ | Workflow & Approvals | AccountChangeRequest | Multi-level approvals, external sync, audit |
| **Dashboard** 📊 | Analytics | Dashboard, Report | Charts, trends, statistics, KPIs |
| **Import/Export** 📥 | Bulk Operations | DataFile, Import | CSV/Excel support, validation, batch ops |
| **Hardware** 🖨️ | Asset Management | Hardware, Equipment | Tracking, depreciation, assignments |
| **Service Accts** 🤖 | Credentials | ServiceAccount | Encryption, rotation, audit logging |
| **Default Accts** ⚙️ | Templates | DefaultAccount | Role-based templates, provisioning |
| **Documentation** 📚 | Help System | Document | Guides, FAQs, API docs |

---

## Architecture Layers

### Presentation Layer
```
Web UI          REST API         Admin Interface
├─ Dashboard    ├─ /api/users/   └─ /admin/
├─ Forms        ├─ /api/systems/
├─ Reports      ├─ /api/access/
└─ Templates    └─ /api/changes/
```

### Application Layer
```
Views & Logic
├─ Request handling
├─ Form processing
├─ Serialization
├─ Permission checks
└─ Business logic
```

### Business Logic
```
Services & Workflow
├─ Risk assessment
├─ Approval routing
├─ Provisioning
├─ Deprovisioning
└─ Audit logging
```

### Data Layer
```
Models (ORM)
├─ User data
├─ System registry
├─ Access assignments
├─ Change requests
└─ Audit trails
```

### Database Layer
```
SQLite (Dev) / PostgreSQL (Prod)
└─ Persistent storage
```

---

## Key Workflows Visualization

### Access Request Flow
```
User Submits → System Validates → Risk Assessment → Routing Decision
    ↓              ↓                    ↓                  ↓
  [Details]   [Rules Check]        [Score ≤25%]     [Risk Based]
              [Eligibility]         [26-60%]           ├─ Low  → Simple
                                    [61%+]            ├─ Medium → 2 Approvals
                                                      └─ High → Escalation
                                                              ↓
Manager Approves → System Owner → Provision → Audit → Active
                   Approves        Access      Log
```

### Access Lifecycle
```
PENDING → APPROVED → ACTIVE ⟷ SUSPENDED
           ↓          ↓  \
         REJECTED   EXPIRED  REVOKED
```

---

## Data Flow Architecture

```
External Users
     ↓
LDAP/Active Directory (auth, sync)
     ↓
UAMS Application
├─ Accounts App (user mgmt)
├─ Departments App (org structure)
├─ Systems App (IT registry)
├─ Access App (access control)
└─ Change Management (approvals, workflows)
     ↓
PostgreSQL Database
     ↓
External Systems (AD, SAP, Salesforce, etc.)
Email System (notifications)
Monitoring/SIEM (audit streaming)
```

---

## Core Models Relationships

```
CustomUser (Accounts)
    ├─ one-to-many: UserSystemAccess
    ├─ one-to-many: Department (as head)
    ├─ many-to-one: Department (as member)
    ├─ one-to-many: AccountChangeRequest
    ├─ one-to-many: AccessHistory
    └─ one-to-many: ServiceAccount

Department
    ├─ self-referential: many-to-one (parent_department)
    ├─ self-referential: one-to-many (sub_departments)
    ├─ one-to-many: CustomUser
    └─ many-to-one: CustomUser (head_of_department)

System
    ├─ one-to-many: UserSystemAccess
    ├─ one-to-many: AccountChangeRequest
    ├─ one-to-many: ServiceAccount
    └─ many-to-one: CustomUser (owner/system_owner)

UserSystemAccess
    ├─ many-to-one: CustomUser
    ├─ many-to-one: System
    ├─ one-to-many: AccessHistory
    └─ one-to-many: AccountChangeRequest (related)

AccountChangeRequest
    ├─ many-to-one: CustomUser (user affected)
    ├─ many-to-one: CustomUser (requested_by)
    ├─ many-to-one: CustomUser (approved_by/system_owner)
    └─ many-to-one: System

AccessHistory
    ├─ many-to-one: UserSystemAccess
    ├─ many-to-one: CustomUser (changed_by)
    └─ tracks: all changes to access
```

---

## Authentication & Authorization

### Authentication Methods
- Django built-in auth
- LDAP/Active Directory integration
- SSO (Single Sign-On) capable
- API Token authentication
- JWT support

### Authorization (RBAC)
```
Roles:
├─ Admin
├─ Security Officer
├─ System Owner
├─ Manager
└─ User

Permissions:
├─ View access
├─ Request access
├─ Approve access
├─ Manage systems
├─ Manage users
└─ View audit logs
```

---

## Integration Points Map

```
┌─────────────────────────────────────────────────────────┐
│                    UAMS (Core)                          │
└─────────────────────────────────────────────────────────┘
         ↓                                        ↓
    ┌─────────────┐                      ┌──────────────┐
    │ LDAP/AD     │                      │ Email System │
    │ Directory   │                      │ (SMTP)       │
    └─────────────┘                      └──────────────┘
         ↓                                        ↓
    • User auth                         • Notifications
    • Profile sync                      • Approvals
    • Group mgmt                        • Alerts
                                        • Reports
         ↓
    ┌──────────────────────────────────────────────────────┐
    │          External Systems (Provisioning)             │
    ├──────────────────────────────────────────────────────┤
    │ • Active Directory (user accounts, groups)           │
    │ • SAP ERP (roles, permissions)                       │
    │ • Salesforce (user profiles, access)                 │
    │ • Workday (HRIS sync, org structure)                 │
    │ • AWS IAM (cloud access, roles)                      │
    │ • GitHub (developer access, repos)                   │
    │ • ServiceNow (ticketing, CMDB)                       │
    │ • And more...                                        │
    └──────────────────────────────────────────────────────┘
         ↓
    ┌──────────────────────────────────────────────────────┐
    │    Monitoring & Compliance (SIEM, Audit Logs)        │
    ├──────────────────────────────────────────────────────┤
    │ • Sentry (error tracking)                            │
    │ • ELK Stack (log aggregation)                        │
    │ • Splunk (security monitoring)                       │
    │ • Grafana (metrics & visualization)                  │
    │ • ServiceNow (ticketing, change mgmt)                │
    └──────────────────────────────────────────────────────┘
```

---

## Request States & Transitions

```
┌─────────────────────────────────────────────────────────┐
│             ACCESS REQUEST LIFECYCLE                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  PENDING ──(Manager Approve)──→ PENDING_OWNER_REVIEW   │
│    ↓                                                    │
│  (Reject)                       (Manager Reject)        │
│    ↓                                  ↓                 │
│  REJECTED                          REJECTED             │
│                                                         │
│  PENDING_OWNER_REVIEW ──(Owner Approve)──→ APPROVED    │
│    ↓                                        ↓            │
│  (Owner Reject)                    (Provision)          │
│    ↓                                        ↓            │
│  REJECTED                            PROVISIONING       │
│                                        ↓                │
│                                     ACTIVE              │
│                                   (Confirmed            │
│                                   by user)              │
│                                        ↓                │
│                            ┌──────────┴──────────┐      │
│                            ↓                     ↓      │
│                        EXPIRED              REVOKED     │
│                     (Date passed)      (Manually removed)│
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## User Role Context

### Typical Day for Different Roles

#### End User - Sarah (Analyst)
```
Morning:
- Login to UAMS
- Check "My Access" dashboard
- See active systems: SAP, Workday, SharePoint
- Submit new request: Salesforce (for project)
- Write justification: "Need access for customer data"

Afternoon:
- Check approval status: "Pending Manager Review"
- Update project documents
- Use currently assigned systems

Auto Actions:
- Expiration reminder (60 days): "Access expires 2027-02-12"
```

#### Manager - John (Department Head)
```
Morning:
- Dashboard: "5 approvals pending"
- Review team member requests
- Approve Sarah's Salesforce request: "Valid project need"
- Reject Tim's Admin access: "Not required for role"

Mid-week:
- Quarterly review cycle starting
- Review all 12 team member accesses
- Approve continued access for 11
- Initiate revocation for 1 (employee on leave)

Monthly:
- Run department access report
- Verify compliance: 100%
- Sign off on changes
```

#### System Owner - David (SAP Admin)
```
Daily:
- Check pending SAP access approvals
- Approve 3 new requests
- Monitor system usage
- Check for policy violations

Weekly:
- Review high-risk requests
- Handle emergency access requests
- Process deprovisioning
- Update system documentation

Monthly:
- Generate usage reports
- Plan capacity
- Review user certifications
- Perform security audits
```

#### Security Officer - Alex
```
Daily:
- Monitor all high-risk access requests
- Review security alerts
- Check for policy violations
- Investigate anomalies

Weekly:
- Security audit reports
- Risk assessment reviews
- Compliance verification
- Threat analysis

Monthly:
- Generate compliance reports (SOX, GDPR, HIPAA)
- Policy updates
- Training reminder
- Security improvements
```

#### System Admin - Maria (UAMS Admin)
```
Daily:
- Monitor system health
- Process bulk operations
- Handle email/ticketing integrations
- Check backup status

Weekly:
- Database maintenance
- User account audits
- Performance optimization
- Security patching

Monthly:
- Capacity planning
- Disaster recovery testing
- Update documentation
- Config backups
```

---

## Key Features by Use Case

### For Compliance Teams
```
✓ Complete audit trail (every action logged)
✓ Change request documentation
✓ Approval chain tracking
✓ Policy enforcement
✓ Compliance reports (SOX, GDPR, HIPAA)
✓ Data export capabilities
✓ Digital signatures
✓ Immutable audit archives
```

### For Security Teams
```
✓ Risk assessment engine
✓ High-risk request escalation
✓ Anomaly detection
✓ Suspicious activity alerts
✓ Emergency access procedures
✓ Security certifications
✓ Incident response workflows
✓ SIEM integration
```

### For Operations Teams
```
✓ Automated provisioning
✓ Deprovisioning workflows
✓ Bulk user operations
✓ Data import/export
✓ External system integration
✓ Change management
✓ Performance monitoring
✓ Backup & recovery
```

### For HR/Managers
```
✓ Org structure management
✓ Team access overview
✓ Access review workflows
✓ Termination procedures
✓ Role-based templates
✓ Leave management
✓ Org reporting
✓ Budget tracking
```

### For End Users
```
✓ Easy request submission
✓ Status tracking
✓ Approval timeline visibility
✓ Self-service access
✓ Password management
✓ Profile updates
✓ Help documentation
✓ Mobile support (future)
```

---

## Technology Stack Summary

**Backend**:
- Django 5.2.8
- Python 3.8+
- PostgreSQL (production)
- Django ORM

**Frontend**:
- Bootstrap 4
- Chart.js (analytics)
- Select2 (dropdowns)
- Font Awesome (icons)
- HTML5, CSS3, JavaScript

**Security**:
- PBKDF2 password hashing
- Django-cryptography (data encryption)
- CSRF protection
- Session security
- LDAP integration

**Integration**:
- Django REST Framework (API)
- LDAP library
- Email (SMTP)
- External system APIs

**Infrastructure**:
- Docker (containerization)
- Gunicorn/uWSGI (app server)
- Nginx (reverse proxy)
- Redis (caching, optional)

---

## Getting Started Checklist

### First-Time Setup
```
☐ Installation & Dependencies
☐ Database migrations
☐ Create superuser
☐ Configure LDAP
☐ Set up email
☐ Load sample data
☐ Configure system owners
☐ Test basic workflow
☐ Set up backups
☐ Monitor health
```

### Configuration
```
☐ Set SECRET_KEY
☐ Configure ALLOWED_HOSTS
☐ LDAP server settings
☐ Email SMTP details
☐ Database connection
☐ Static files setup
☐ Log configuration
☐ SSL/TLS certificates
☐ Reverse proxy setup
☐ Monitoring integration
```

### Testing Workflows
```
☐ User registration
☐ Access request
☐ Approval process
☐ Provisioning
☐ Expiration
☐ Renewal
☐ Revocation
☐ User deletion
☐ Audit trail
☐ Report generation
```

---

## Quick Command Reference

### Django Commands
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Create test data
python manage.py loaddata fixtures/sample_data

# Generate reports
python manage.py generate_reports --format=pdf

# Check system health
python manage.py check
```

### Management Commands (Custom)
```bash
# Sync LDAP users
python manage.py sync_ldap_users

# Process pending requests
python manage.py process_pending_requests

# Expire old access
python manage.py expire_old_access

# Generate compliance report
python manage.py generate_compliance_report --date=2026-02-12

# Backup database
python manage.py dumpdata > backup_2026_02_12.json
```

---

## Performance Metrics

### Expected Performance
- Page load time: < 2 seconds
- API response: < 500ms
- Database queries: < 100ms average
- Search results: < 1 second
- Report generation: < 5 seconds

### Scaling Capacity
- Users: 10,000+
- Systems: 1,000+
- Access records: 100,000+
- Audit logs: Millions

---

## Support & Resources

### Documentation
- [Architecture Guide](ARCHITECTURE.md)
- [Architecture Diagrams](ARCHITECTURE_DIAGRAMS.md)
- [User Workflows](USER_WORKFLOWS.md)
- [README](README.md)
- [Requirements](requirements_doc.md)

### Getting Help
- System Admin: Deploy and configure
- Manager: Review and approve accesses
- User: Submit requests and confirm
- Security: Review high-risk items
- Support: Use help documentation

---

## Version Info

**Current Version**: 1.0
**Django Version**: 5.2.8
**Python Version**: 3.8+
**Database**: SQLite (dev), PostgreSQL (production)
**Last Updated**: 2026-02-12

---

**This is a comprehensive User Access Management System designed for enterprise-scale access control, approval workflows, and compliance requirements.**

# User Access Management System (UAMS) - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Application Modules](#application-modules)
4. [Data Models & Relationships](#data-models--relationships)
5. [User Workflows](#user-workflows)
6. [Integration Points](#integration-points)
7. [Technology Stack](#technology-stack)

---

## System Overview

The User Access Management System (UAMS) is a comprehensive Django-based platform designed to manage user access across multiple IT systems within an organization. It provides centralized control over user accounts, access rights, system administration, and compliance audit trails.

### Core Objectives
- **Access Control**: Manage who has access to which systems
- **Compliance**: Ensure all access changes are audited and approved
- **Governance**: Enforce access review and approval workflows
- **Scalability**: Support unlimited users, systems, and departments
- **Security**: Encrypt sensitive data, track all changes

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         User Access Management System                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Presentation Layer                         │   │
│  │  (HTML/CSS/JavaScript- Bootstrap, Chart.js, Select2)           │   │
│  │  - Dashboard Views        - Admin Interface        - Forms      │   │
│  │  - Reports & Analytics    - Data Import/Export     - API Views  │   │
│  └────────────────┬──────────────────────────────────────────────┘   │
│                   │                                                     │
│  ┌────────────────▼──────────────────────────────────────────────┐   │
│  │                   Application Layer (Django)                  │   │
│  │                                                                 │   │
│  │  ┌──────────────────────────────────────────────────────┐     │   │
│  │  │                  Core Apps                           │     │   │
│  │  │  • Accounts (User Management)                        │     │   │
│  │  │  • Departments (Organizational Structure)            │     │   │
│  │  │  • Systems (IT Systems Registry)                     │     │   │
│  │  │  • Access Management (Access Control & Tracking)     │     │   │
│  │  └──────────────────────────────────────────────────────┘     │   │
│  │                                                                 │   │
│  │  ┌──────────────────────────────────────────────────────┐     │   │
│  │  │              Supporting Apps                         │     │   │
│  │  │  • Change Management (Workflow & Approvals)          │     │   │
│  │  │  • Dashboard (Analytics & Reporting)                 │     │   │
│  │  │  • Data Import/Export (Bulk Operations)              │     │   │
│  │  │  • Hardware (Asset Management)                       │     │   │
│  │  │  • Service Accounts (Service Credential Mgmt)        │     │   │
│  │  │  • Default Accounts (Template Management)            │     │   │
│  │  │  • Documentation (Help & Guides)                     │     │   │
│  │  └──────────────────────────────────────────────────────┘     │   │
│  └────────────────┬──────────────────────────────────────────────┘   │
│                   │                                                     │
│  ┌────────────────▼──────────────────────────────────────────────┐   │
│  │               Business Logic Layer                            │   │
│  │  • Access Workflows    • Change Request Processing            │   │
│  │  • Approval Engine     • Audit Trail Management               │   │
│  │  • Risk Assessment     • Data Validation & Encryption         │   │
│  │  • Reporting Logic     • Notification Systems                 │   │
│  └────────────────┬──────────────────────────────────────────────┘   │
│                   │                                                     │
│  ┌────────────────▼──────────────────────────────────────────────┐   │
│  │                  Data Access Layer (ORM)                      │   │
│  │  Django ORM Models, Managers, QuerySets                       │   │
│  └────────────────┬──────────────────────────────────────────────┘   │
│                   │                                                     │
│  ┌────────────────▼──────────────────────────────────────────────┐   │
│  │                    Database Layer                             │   │
│  │  SQLite (Dev) / PostgreSQL (Production)                       │   │
│  │  • Users, Departments, Systems, Access Records                │   │
│  │  • Change Requests, Audit Logs, Approvals                     │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Application Modules

### 1. **Accounts App** 👤
**Purpose**: User management and authentication

**Key Models**:
- **CustomUser**: Extended Django User model with:
  - Employee ID, National ID (encrypted)
  - Employment type (Full-time, Contract, etc.)
  - Employment status (Active, Suspended, Terminated)
  - Department assignment
  - Phone numbers, personal email
  - User roles (Admin, Manager, User, Approver)
  - Photo/avatar support

**Key Features**:
- LDAP/Active Directory integration
- User registration and profile management
- Role-based access control (RBAC)
- User encryption for sensitive data
- User deletion with audit trail

**Related Files**:
- [models.py](accounts/models.py)
- [views.py](accounts/views.py)
- [encryption.py](accounts/encryption.py)

---

### 2. **Departments App** 🏢
**Purpose**: Organizational hierarchy management

**Key Models**:
- **Department**: Hierarchical department structure with:
  - Parent-child relationships (unlimited nesting)
  - Department types (Division, Team, Unit, etc.)
  - Head of department assignment
  - Cost center and budget codes
  - Office location tracking

**Key Features**:
- Tree-like organizational structure
- Department head management
- Cost center tracking
- Multiple location support

**Related Files**:
- [departments/models.py](departments/models.py)
- [departments/views.py](departments/views.py)

---

### 3. **Systems App** 🖥️
**Purpose**: IT Systems and Applications Registry

**Key Models**:
- **System**: Represents IT systems/applications with:
  - System type (Web, Desktop, Database, API, Cloud, etc.)
  - Criticality level (Critical, High, Medium, Low)
  - Environment (Production, Staging, Testing, Dev)
  - Authentication type (LDAP, SSO, OAuth, SAML, MFA, etc.)
  - Access requirements and documentation
  - System owner assignment
  - Risk assessment scores

**Key Features**:
- Comprehensive system registry
- Multiple environment support
- Risk and criticality assessment
- Access requirement definitions
- System owner/steward assignment
- Integration with external systems

**Related Files**:
- [systems/models.py](systems/models.py)
- [systems/views.py](systems/views.py)

---

### 4. **Access Management App** 🔐
**Purpose**: Core access control and tracking

**Key Models**:
- **UserSystemAccess**: Tracks user access to systems with:
  - Access types (Full Access, Read Only, Admin, etc.)
  - Status (Pending, Approved, Active, Revoked, Expired)
  - Priority levels (Low, Medium, High, Critical)
  - Request type (New, Renewal, Upgrade, Emergency)
  - Approval workflows and timestamps
  - Expiration dates and validity periods
  - Business justification

- **AccessHistory**: Audit trail of all access changes

**Key Features**:
- Request-based access management
- Multi-level approval workflows
- Automatic expiration handling
- Access renewal workflows
- Risk scoring for access requests
- Change impact analysis

**Related Files**:
- [models.py](access_management/models.py)
- [views.py](access_management/views.py)
- [reporting.py](access_management/reporting.py)

---

### 5. **Change Management App** ✅
**Purpose**: Approval workflows and change tracking

**Key Models**:
- **AccountChangeRequest**: Documents system account changes with:
  - Change types (Create, Modify, Delete, Suspend)
  - Status workflow (Pending → Approved → Completed)
  - Business justification requirement
  - Multi-level approvals
  - System owner authorization
  - Approval audit trail

**Key Features**:
- Change request workflows
- Approval routing
- Compliance audit trail
- External system integration
- Change impact tracking
- Notification system

**Related Files**:
- [models.py](change_management/models.py)
- [workflow.py](change_management/workflow.py)
- [views.py](change_management/views.py)

---

### 6. **Dashboard App** 📊
**Purpose**: Analytics and reporting

**Key Features**:
- User access statistics
- System usage analytics
- Pending approvals dashboard
- Access trends visualization
- Department-level reports
- System criticality dashboards

**Related Files**:
- [views.py](dashboard/views.py)
- [models.py](dashboard/models.py)

---

### 7. **Data Import/Export App** 📥📤
**Purpose**: Bulk data operations

**Key Features**:
- Import users from CSV/Excel
- Import departments and systems
- Export access reports
- Bulk access assignments
- Data format validation

**Related Files**:
- [views.py](data_import_export/views.py)

---

### 8. **Hardware App** 🖨️
**Purpose**: Asset and equipment management

**Key Features**:
- Hardware asset tracking
- Equipment assignment to users
- Serial number management
- Asset depreciation tracking
- Maintenance schedules

---

### 9. **Service Accounts App** 🤖
**Purpose**: Service credential management

**Key Features**:
- Service account creation
- Credential encryption and storage
- Password rotation management
- Service account access tracking
- Audit logging

---

### 10. **Default Accounts App** ⚙️
**Purpose**: Account templates and defaults

**Key Features**:
- Default account templates
- Role-based default access patterns
- Template-based access provisioning

---

### 11. **Documentation App** 📚
**Purpose**: Help and system documentation

**Key Features**:
- User guides
- System documentation
- API documentation
- Access procedures
- Troubleshooting guides

---

## Data Models & Relationships

### Entity Relationship Overview

```
CustomUser
├── has_many: system_accesses (UserSystemAccess)
├── has_many: departments_headed (Department)
├── belongs_to: department (Department)
├── has_many: account_change_requests_made (AccountChangeRequest)
├── has_many: system_owner_approvals (AccountChangeRequest)
└── has_many: access_history (AccessHistory)

Department
├── has_many: sub_departments (self)
├── belongs_to: parent_department (self)
├── belongs_to: head_of_department (CustomUser)
└── has_many: users (CustomUser)

System
├── has_many: user_accesses (UserSystemAccess)
├── has_many: account_change_requests (AccountChangeRequest)
├── belongs_to: system_owner (CustomUser)
└── has_many: default_accesses (DefaultAccountAccess)

UserSystemAccess
├── belongs_to: user (CustomUser)
├── belongs_to: system (System)
├── has_many: access_history (AccessHistory)
└── has_many: account_change_requests (AccountChangeRequest)

AccountChangeRequest
├── belongs_to: user (CustomUser)
├── belongs_to: requested_by (CustomUser)
├── belongs_to: system_owner (CustomUser)
├── belongs_to: system (System)
└── has_many: approvals (ApprovalLog)

AccessHistory
├── belongs_to: access (UserSystemAccess)
├── belongs_to: user (CustomUser)
└── belongs_to: changed_by (CustomUser)
```

---

## User Workflows

### Workflow 1: New User Access Request

```
START
  │
  ├─→ User/Manager submits access request
  │   - Selects system
  │   - Chooses access type
  │   - Provides business justification
  │   - Sets priority level
  │
  ├─→ System validates request
  │   - Checks user eligibility
  │   - Validates system access rules
  │   - Calculates risk score
  │
  ├─→ Request routed to approvers
  │   - Manager approval (if configured)
  │   - System owner approval
  │   - Security team review (if high risk)
  │
  ├─→ Approval workflow
  │   ├─→ APPROVED
  │   │   └─→ Access provisioned
  │   │       └─→ Change request created for external systems
  │   │           └─→ Audit log created
  │   │               └─→ Notification sent
  │   │
  │   └─→ REJECTED
  │       └─→ Request marked as rejected
  │           └─→ Rejection reason recorded
  │               └─→ Requester notified
  │
  ├─→ Set expiration date
  │   └─→ Automatic renewal reminders sent
  │
  └─→ END (Access Active)
```

### Workflow 2: Access Renewal

```
START (30 days before expiration)
  │
  ├─→ System detects access approaching expiration
  │   └─→ Sends renewal reminder to user
  │
  ├─→ User submits renewal request
  │   - Confirms continued business need
  │   - May update access type
  │
  ├─→ Manager reviews access
  │   └─→ Confirms user still needs access
  │
  ├─→ System owner approves
  │   └─→ Grants renewal
  │
  ├─→ Access expiration extended
  │   └─→ Audit trail updated
  │
  └─→ END (Access Renewed)
```

### Workflow 3: Access Revocation/De-provisioning

```
START (User leaves/department change)
  │
  ├─→ Manager initiates access revocation
  │   └─→ Selects access to revoke
  │
  ├─→ System validates revocation
  │   ├─→ Checks dependencies
  │   └─→ Identifies affected systems
  │
  ├─→ Creates change requests
  │   └─→ For each system with user account
  │
  ├─→ System owner approves removal
  │   └─→ Provides completion confirmation
  │
  ├─→ Access deactivated
  │   ├─→ External systems notified
  │   ├─→ Credentials invalidated
  │   └─→ Audit trail recorded
  │
  └─→ END (Access Revoked)
```

### Workflow 4: User Deletion (GDPR/Termination)

```
START (Employee termination)
  │
  ├─→ HR initiates user deletion
  │   └─→ Provides termination reason
  │
  ├─→ System revokes all active access
  │   └─→ Creates change requests for all systems
  │
  ├─→ Multi-level approvals
  │   ├─→ Department head approval
  │   ├─→ System owners approve removals
  │   └─→ Security team sign-off
  │
  ├─→ Change requests processed
  │   └─→ External system accounts deleted
  │
  ├─→ Data anonymization
  │   ├─→ User profile cleared
  │   ├─→ Sensitive data encrypted/hashed
  │   └─→ Access history preserved for audit
  │
  ├─→ Audit trail finalized
  │   └─→ Deletion logged with full context
  │
  └─→ END (User Deleted)
```

### Workflow 5: Manager Access Review

```
START (Quarterly review)
  │
  ├─→ Manager receives review notifications
  │   └─→ For all team members' access
  │
  ├─→ Manager reviews each user's access
  │   ├─→ Validates continued business need
  │   ├─→ Identifies unnecessary access
  │   └─→ Notes any concerns
  │
  ├─→ Manager takes actions
  │   ├─→ APPROVE: Access continues
  │   ├─→ REVOKE: Access marked for removal
  │   └─→ MODIFY: Changes access levels
  │
  ├─→ System generates change requests
  │   └─→ For approved modifications
  │
  ├─→ System owners finalize changes
  │   └─→ External systems updated
  │
  └─→ END (Review Complete)
```

### Workflow 6: Risk-Based Access Approval

```
START (Access request submitted)
  │
  ├─→ Risk assessment engine evaluates
  │   ├─→ User history analysis
  │   ├─→ System criticality check
  │   ├─→ Access type validation
  │   ├─→ Business justification analysis
  │   └─→ Generates risk score
  │
  ├─→ Risk-based routing
  │   │
  │   ├─→ LOW RISK (0-25%)
  │   │   └─→ Auto-approve or simple review
  │   │
  │   ├─→ MEDIUM RISK (26-60%)
  │   │   ├─→ Manager approval
  │   │   └─→ System owner approval
  │   │
  │   └─→ HIGH RISK (61%+)
  │       ├─→ Manager approval
  │       ├─→ System owner approval
  │       └─→ Security team review required
  │
  ├─→ Approval workflow executes
  │   └─→ Based on risk level
  │
  └─→ END (Approved or Rejected)
```

---

## Integration Points

### External System Integrations

```
UAMS
├─→ LDAP/Active Directory
│   ├─→ User authentication
│   ├─→ User sync (bi-directional)
│   └─→ Group management
│
├─→ Email System
│   ├─→ Notification delivery
│   ├─→ Approval requests
│   └─→ Reminder emails
│
├─→ Ticketing Systems (Optional)
│   ├─→ Change request creation
│   ├─→ Status updates
│   └─→ Closure confirmation
│
├─→ HRIS/HR Systems
│   ├─→ Employee data sync
│   ├─→ Termination notifications
│   └─→ Org structure updates
│
├─→ Cloud Services (AWS, Azure)
│   ├─→ User provisioning
│   ├─→ Access management
│   └─→ Audit log synchronization
│
├─→ Monitoring/SIEM Systems
│   ├─→ Audit event streaming
│   ├─→ Compliance reporting
│   └─→ Security alerts
│
└─→ API Access (REST/GraphQL)
    ├─→ Third-party integrations
    ├─→ Programmatic access requests
    └─→ System status queries
```

---

## Technology Stack

### Backend
- **Framework**: Django 5.2.8
- **Language**: Python 3.8+
- **ORM**: Django ORM
- **Database**: SQLite (dev), PostgreSQL (production)
- **Authentication**: Django Auth + LDAP
- **Encryption**: Django-cryptography, Django-fernet
- **Task Queue**: Celery (optional, for background tasks)
- **API**: Django REST Framework

### Frontend
- **Template Engine**: Django Templates
- **CSS Framework**: Bootstrap 4
- **JavaScript**: Vanilla JS, jQuery (optional)
- **Charts**: Chart.js
- **Data Selection**: Select2
- **Icons**: Font Awesome

### Infrastructure
- **Web Server**: Gunicorn/uWSGI
- **Reverse Proxy**: Nginx
- **Containerization**: Docker
- **Database**: PostgreSQL (production)
- **Cache**: Redis (optional)
- **Logging**: Python logging module
- **Monitoring**: Optional (Sentry, ELK, etc.)

### Security
- **Authentication**: Django Auth, LDAP/AD, SSO
- **Authorization**: Role-based access control (RBAC)
- **Encryption**: Password hashing (PBKDF2), Data encryption
- **Audit**: Comprehensive audit trail
- **Compliance**: GDPR, SOX, HIPAA ready

---

## Configuration & Deployment

### Environment Configuration
- Development: SQLite + DEBUG=True
- Production: PostgreSQL + DEBUG=False
- Reverse proxy support (Nginx, Apache)
- SSL/TLS support
- CORS configuration

### Key Settings (via .env)
```
DEBUG=False
SECRET_KEY=<generated-key>
ALLOWED_HOSTS=example.com,www.example.com
DATABASE_URL=postgresql://user:pass@host:5432/db
LDAP_SERVER=ldap://ldap.example.com
LDAP_BIND_DN=cn=admin,dc=example,dc=com
EMAIL_HOST=smtp.example.com
EMAIL_FROM_ADDRESS=noreply@example.com
```

### Deployment Architecture
```
Users (HTTPS)
    ↓
Nginx (Reverse Proxy)
    ↓
Gunicorn (Django + Python)
    ↓
PostgreSQL (Data)
LDAP (Auth)
Email (Notifications)
```

---

## Key Features by Workflow Stage

### 1. **Request Stage**
- User/Manager submissions
- Business justification capture
- Risk assessment
- Auto-routing based on risk

### 2. **Approval Stage**
- Multi-level approvals
- Role-based routing
- Approval comments/notes
- Deadline management
- Escalation workflows

### 3. **Provisioning Stage**
- Change request generation
- External system integration
- Automatic provisioning (where supported)
- Manual confirmation tracking

### 4. **Active Stage**
- Access logging
- Usage monitoring
- Expiration tracking
- Re-certification prompts

### 5. **Deprovisioning Stage**
- Access revocation
- Automatic cleanup
- External system de-provisioning
- Archive & audit

---

## Security & Compliance

### Data Protection
- Encryption of sensitive fields (national ID, passwords)
- Password hashing using PBKDF2
- Secure session management
- CSRF protection
- SQL injection prevention (Django ORM)

### Audit & Logging
- Complete audit trail of all changes
- User action logging
- Access event tracking
- Change request history
- Approval documentation

### Access Control
- Role-Based Access Control (RBAC)
- Permission-based view access
- Organizational hierarchy enforcement
- Department-level isolation (optional)

### Compliance
- GDPR: User deletion, data export
- SOX: Change control, audit trails
- HIPAA: Encryption, access logging
- Data residency support

---

## Performance Optimization

### Database
- Indexed queries for frequently searched fields
- Select_related for relationship optimization
- Pagination for large result sets
- Query caching where appropriate

### Caching
- Django cache framework
- Optional Redis integration
- Template caching
- ORM query caching

### Code Optimization
- Batch operations for bulk changes
- Asynchronous tasks (Celery optional)
- Resource pooling
- Memory-efficient queries

---

## Future Enhancements

1. **API Expansion**: GraphQL API, webhook support
2. **ML Integration**: Anomaly detection, risk prediction
3. **Advanced Reporting**: Self-service BI dashboards
4. **Mobile App**: Mobile access management
5. **Enhanced Integration**: More external systems
6. **Blockchain**: Audit trail immutability
7. **AI-Powered Approvals**: Intelligent routing
8. **Advanced Analytics**: Predictive access management

---

## Support & Documentation

- **User Guide**: See [README_DOCS.md](README_DOCS.md)
- **Technical Docs**: See [requirements_doc.md](requirements_doc.md)
- **API Docs**: Available at `/api/docs/`
- **Implementation Guide**: See [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md)

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-12  
**Maintained By**: Development Team

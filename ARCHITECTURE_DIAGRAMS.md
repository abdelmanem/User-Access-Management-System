# UAMS - Visual Architecture Diagrams

This document contains visual diagrams for the User Access Management System architecture, workflows, and data flows.

## 1. System Architecture Overview

```mermaid
graph TB
    subgraph "Client Layer"
        WEB["Web Browser<br/>Users/Admins"]
        API["API Clients<br/>External Systems"]
    end
    
    subgraph "Presentation Layer"
        VIEWS["Django Views<br/>HTML/Templates"]
        API_VIEWS["REST API Views"]
        ADMIN["Django Admin<br/>Interface"]
    end
    
    subgraph "Application Layer"
        FORMS["Forms & Validation"]
        AUTH["Authentication<br/>LDAP/SSO"]
        PERMS["Permissions<br/>Authorization"]
        VIEWS_LOGIC["Business Logic<br/>Services"]
    end
    
    subgraph "Data Layer"
        ORM["Django ORM<br/>Query Builder"]
        MODELS["Models<br/>Access/Audit"]
    end
    
    subgraph "Database Layer"
        DB["PostgreSQL<br/>SQLite Dev"]
    end
    
    subgraph "External Integrations"
        LDAP["LDAP/AD<br/>Authentication"]
        EMAIL["Email System<br/>Notifications"]
        EXT_SYS["External Systems<br/>Provisioning"]
    end
    
    WEB --> VIEWS
    API --> API_VIEWS
    WEB --> ADMIN
    
    VIEWS --> FORMS
    API_VIEWS --> FORMS
    ADMIN --> FORMS
    
    FORMS --> AUTH
    AUTH --> PERMS
    PERMS --> VIEWS_LOGIC
    
    VIEWS_LOGIC --> ORM
    ORM --> MODELS
    MODELS --> DB
    
    VIEWS_LOGIC --> LDAP
    VIEWS_LOGIC --> EMAIL
    VIEWS_LOGIC --> EXT_SYS
```

## 2. Application Modules & Dependencies

```mermaid
graph LR
    subgraph "Core Apps"
        ACCOUNTS["👤 Accounts<br/>User Management"]
        DEPTS["🏢 Departments<br/>Org Structure"]
        SYSTEMS["🖥️ Systems<br/>IT Registry"]
        ACCESS["🔐 Access Mgmt<br/>Core Logic"]
    end
    
    subgraph "Supporting Apps"
        CHANGE["✅ Change Mgmt<br/>Workflows"]
        DASHBOARD["📊 Dashboard<br/>Analytics"]
        IMPORT["📥 Import/Export<br/>Bulk Ops"]
        HARDWARE["🖨️ Hardware<br/>Assets"]
        SERVICE["🤖 Service Accts<br/>Credentials"]
        DEFAULT["⚙️ Default Accts<br/>Templates"]
        DOCS["📚 Docs<br/>Help"]
    end
    
    subgraph "Framework"
        DJANGO["Django Core<br/>ORM/Auth/Admin"]
    end
    
    ACCOUNTS -->|depends on| DJANGO
    DEPTS -->|depends on| ACCOUNTS
    SYSTEMS -->|depends on| ACCOUNTS
    ACCESS -->|depends on| ACCOUNTS
    ACCESS -->|depends on| SYSTEMS
    ACCESS -->|depends on| DEPTS
    
    CHANGE -->|depends on| ACCESS
    CHANGE -->|depends on| ACCOUNTS
    DASHBOARD -->|uses| ACCESS
    IMPORT -->|uses| ACCOUNTS
    IMPORT -->|uses| SYSTEMS
    IMPORT -->|uses| ACCESS
    HARDWARE -->|uses| ACCOUNTS
    SERVICE -->|uses| ACCOUNTS
    SERVICE -->|uses| SYSTEMS
    DEFAULT -->|uses| SYSTEMS
```

## 3. Data Model Relationships

```mermaid
graph TB
    USER["CustomUser<br/>(Accounts)"]
    DEPT["Department<br/>(Departments)"]
    SYSTEM["System<br/>(Systems)"]
    ACCESS["UserSystemAccess<br/>(Access)"]
    CHANGE["AccountChangeRequest<br/>(Change Mgmt)"]
    HISTORY["AccessHistory<br/>(Access)"]
    HARDWARE["Hardware<br/>(Hardware)"]
    SERVICE_ACC["ServiceAccount<br/>(Service Accts)"]
    
    USER -->|belongs to| DEPT
    USER -->|heads| DEPT
    DEPT -->|has many| DEPT
    
    USER -->|requests| ACCESS
    SYSTEM -->|has many| ACCESS
    ACCESS -->|creates| CHANGE
    
    USER -->|owns| SYSTEM
    USER -->|approves| CHANGE
    USER -->|created by| CHANGE
    
    ACCESS -->|has many| HISTORY
    USER -->|modified by| HISTORY
    CHANGE -->|related to| HISTORY
    
    HARDWARE -->|assigned to| USER
    SERVICE_ACC -->|belongs to| SYSTEM
    SERVICE_ACC -->|used by| USER
```

## 4. User Access Request Workflow

```mermaid
graph TD
    START[("User Initiates<br/>Access Request")] --> FORM["Fill Request Form<br/>- User/System<br/>- Access Type<br/>- Justification<br/>- Priority"]
    
    FORM --> VALIDATE["System Validates<br/>- User eligibility<br/>- System requirements<br/>- Access rules<br/>- Risk scoring"]
    
    VALIDATE --> RISK{Risk<br/>Assessment}
    
    RISK -->|LOW| APPROVE1["Auto-Approve or<br/>Simple Review"]
    RISK -->|MEDIUM| APPROVE2["Manager<br/>+ System Owner<br/>Approval"]
    RISK -->|HIGH| APPROVE3["Manager<br/>+ System Owner<br/>+ Security<br/>Review"]
    
    APPROVE1 --> DECISION{Approved?}
    APPROVE2 --> DECISION
    APPROVE3 --> DECISION
    
    DECISION -->|YES| PROVISION["Create Change Request<br/>- For external systems<br/>- For server setup"]
    DECISION -->|NO| REJECT["Mark Rejected<br/>- Record reason<br/>- Notify user"]
    
    PROVISION --> CREATE["Provision Access<br/>- Create accounts<br/>- Assign permissions<br/>- Send credentials"]
    
    CREATE --> AUDIT["Log Audit Trail<br/>- Record approval chain<br/>- Document justification<br/>- Timestamp all actions"]
    
    AUDIT --> NOTIFY["Send Notifications<br/>- User access active<br/>- Managers informed<br/>- System owner updated"]
    
    REJECT --> NOTIFY_R["Send Rejection<br/>Notification"]
    
    NOTIFY --> ACTIVE["Access ACTIVE"]
    NOTIFY_R --> END_R[("Request Complete<br/>Access Denied")]
    ACTIVE --> EXPIRE["Set Expiration<br/>- Date + Reminder<br/>- Auto-renewal setup"]
    
    EXPIRE --> END[("Request Complete<br/>Access Active")]
```

## 5. Access Renewal Workflow

```mermaid
graph TD
    CHECK["System Checks<br/>Access Expiring<br/>30 days"]
    
    CHECK --> SEND1["Send Renewal<br/>Reminder to User"]
    
    SEND1 --> REVIEW["Manager Reviews<br/>User Access<br/>- Still needed?<br/>- Update access type?"]
    
    REVIEW --> SUBMIT["User Submits<br/>Renewal Request"]
    
    SUBMIT --> OWNER["System Owner<br/>Reviews & Approves"]
    
    OWNER --> DECISION{Approved?}
    
    DECISION -->|YES| EXTEND["Extend Expiration<br/>- New end date<br/>- Re-calculate expiry"]
    DECISION -->|NO| REVOKE["Revoke Access"]
    
    EXTEND --> UPDATE["Update Audit Log<br/>- Renewal recorded<br/>- Approval noted"]
    REVOKE --> DEP["De-provision<br/>Access"]
    
    UPDATE --> SEND2["Notify User<br/>- Access renewed<br/>- New exp date"]
    DEP --> SEND3["Notify User<br/>- Access revoked"]
    
    SEND2 --> END[("Renewal Complete")]
    SEND3 --> END
```

## 6. Access Revocation Workflow

```mermaid
graph TD
    START[("Revocation Initiated<br/>- Manager request<br/>- User departure<br/>- Policy violation")] 
    
    START --> COLLECT["Identify All Access<br/>- Active accesses<br/>- Systems affected<br/>- Dependencies"]
    
    COLLECT --> CHANGE["Create Change Requests<br/>- One per system<br/>- Account deletion<br/>- Permission removal"]
    
    CHANGE --> VALIDATE["Validation<br/>- Check dependencies<br/>- Verify ownership<br/>- Confirm access"]
    
    VALIDATE --> ROUTE["Route to Approvers<br/>- System owners<br/>- Security team<br/>- Managers"]
    
    ROUTE --> APPROVALS["Gather Approvals<br/>- Review justification<br/>- Confirm removal<br/>- Acknowledge liability"]
    
    APPROVALS --> DECISION{All<br/>Approved?}
    
    DECISION -->|NO| HOLD["On Hold<br/>- Pending approval<br/>- Notify requestor"]
    DECISION -->|YES| PROVISION["De-provision Access<br/>- External systems<br/>- Reset credentials<br/>- Update accounts"]
    
    HOLD --> WAIT["Wait for<br/>Approval"]
    WAIT --> APPROVALS
    
    PROVISION --> DISABLE["Disable Access<br/>- Revoke permissions<br/>- Lock accounts<br/>- Archive configs"]
    
    DISABLE --> AUDIT["Record Audit Trail<br/>- All change details<br/>- Approvals<br/>- Timestamps"]
    
    AUDIT --> NOTIFY["Send Notifications<br/>- User notified<br/>- Managers informed<br/>- Systems updated"]
    
    NOTIFY --> END[("Revocation Complete<br/>Access Inactive")]
```

## 7. User Deletion (GDPR/Termination) Workflow

```mermaid
graph TD
    START[("Termination<br/>HR notification")] 
    
    START --> NOTIFY["Notify System<br/>- Employee ID<br/>- Termination date<br/>- Reason"]
    
    NOTIFY --> REVOKE["Revoke ALL Access<br/>- Active accesses<br/>- Pending requests<br/>- Scheduled access"]
    
    REVOKE --> CHANGES["Create Change Requests<br/>- Delete accounts<br/>- Remove from groups<br/>- Revoke licenses"]
    
    CHANGES --> LOOP["For Each System<br/>- Create request<br/>- Route to owner<br/>- Track status"]
    
    LOOP --> APPROVALS["Gather Approvals<br/>- Manager<br/>- System owner<br/>- Security team"]
    
    APPROVALS --> CONFIRM["Confirm Deletions<br/>- External systems<br/>- On-premises systems<br/>- Cloud services"]
    
    CONFIRM --> CLEAN["Data Cleanup<br/>- Archive records<br/>- Anonymize personal<br/>- Keep audit trail"]
    
    CLEAN --> HASH["Hash Sensitive Data<br/>- National ID<br/>- Phone numbers<br/>- Personal email"]
    
    HASH --> FINAL["Finalize Deletion<br/>- Mark user deleted<br/>- Preserve history<br/>- Lock record"]
    
    FINAL --> AUDIT["Create Final Audit Log<br/>- Deletion confirmation<br/>- All changes<br/>- Compliance docs"]
    
    AUDIT --> END[("User Deleted<br/>Audit Trail Preserved")]
```

## 8. Manager Quarterly Access Review

```mermaid
graph TD
    START[("Quarterly Review<br/>Cycle Starts")] 
    
    START --> NOTIFY["Managers Notified<br/>- Review required items<br/>- Due date set<br/>- Instructions sent"]
    
    NOTIFY --> ASSIGN["System Assigns<br/>Users to Review<br/>- By department<br/>- By manager"]
    
    ASSIGN --> LOOP["For Each User"]
    
    LOOP --> DISPLAY["Display Access<br/>- Active accesses<br/>- Access type<br/>- Grant date<br/>- Business justification"]
    
    DISPLAY --> REVIEW["Manager Reviews<br/>- Still needed?<br/>- Correct permissions?<br/>- Any concerns?"]
    
    REVIEW --> DECISION{Action?}
    
    DECISION -->|APPROVE| APPROVE["Mark Approved<br/>- Record review date<br/>- Manager signature"]
    DECISION -->|REVOKE| REVOKE_R["Mark for Revocation<br/>- Reason noted<br/>- Schedule removal"]
    DECISION -->|MODIFY| MODIFY["Propose Modification<br/>- New access type<br/>- Change justification"]
    
    APPROVE --> NEXT["Next User"]
    REVOKE_R --> CHANGE_R["Create Change Request<br/>for Revocation"]
    MODIFY --> CHANGE_M["Create Change Request<br/>for Modification"]
    
    CHANGE_R --> ROUTE["Route to System<br/>Owner"]
    CHANGE_M --> ROUTE
    
    NEXT --> LOOP
    
    LOOP --> COMPLETE["Review Completed<br/>- All users reviewed<br/>- Changes submitted<br/>- Audit logged"]
    
    ROUTE --> FINAL["Processing Changes<br/>- Approvals gathered<br/>- Systems updated<br/>- Users notified"]
    
    COMPLETE --> FINAL
    
    FINAL --> END[("Review Cycle<br/>Complete")]
```

## 9. Change Request Approval Workflow

```mermaid
graph TD
    CREATE[("Change Request<br/>Created")] 
    
    CREATE --> ASSIGN["Assign to System<br/>Owner"]
    
    ASSIGN --> NOTIFY["System Owner<br/>Notified<br/>- Email<br/>- Dashboard alert"]
    
    NOTIFY --> REVIEW["System Owner<br/>Reviews<br/>- Justification<br/>- Impact analysis<br/>- Risk assessment"]
    
    REVIEW --> DECISION{Decision?}
    
    DECISION -->|APPROVE| APP["Mark Approved<br/>- Record approval<br/>- Add notes<br/>- Timestamp"]
    DECISION -->|REJECT| REJ["Mark Rejected<br/>- Record reason<br/>- Notify requester<br/>- Close request"]
    DECISION -->|DEFER| DEFER["Defer Decision<br/>- Set reminder<br/>- Hold for clarification"]
    
    APP --> PROVISION["Provision in<br/>External System<br/>- Create account<br/>- Grant permissions<br/>- Set credentials"]
    
    REJ --> NOTIFY_U["Notify Requester<br/>- Rejection reason<br/>- Appeal process<br/>- Next steps"]
    
    DEFER --> WAIT["Request Information<br/>- Additional details<br/>- Clarification<br/>- Documentation"]
    
    WAIT --> RESUBMIT["Resubmit for<br/>Review"]
    
    RESUBMIT --> REVIEW
    
    PROVISION --> VERIFY["Verify Completion<br/>- Confirm setup<br/>- Test access<br/>- User confirms"]
    
    VERIFY --> CONFIRM{Success?}
    
    CONFIRM -->|YES| FINAL["Mark Completed<br/>- Record completion<br/>- Archive evidence<br/>- Close ticket"]
    CONFIRM -->|NO| TROUBLE["Troubleshoot<br/>- Identify issue<br/>- Resolve problem<br/>- Re-test"]
    
    TROUBLE --> VERIFY
    
    FINAL --> AUDIT["Update Audit Log<br/>- Document process<br/>- Record approvals<br/>- Compliance artifact"]
    
    NOTIFY_U --> END[("Change Request<br/>Complete")]
    AUDIT --> END
```

## 10. Risk-Based Request Routing

```mermaid
graph TD
    REQ[("Access Request<br/>Submitted")] 
    
    REQ --> ANALYZE["Risk Assessment<br/>Engine"]
    
    ANALYZE --> CHECK1["User History<br/>- Previous access<br/>- Approval patterns<br/>- Violations"]
    
    ANALYZE --> CHECK2["System Criticality<br/>- Business impact<br/>- Data sensitivity<br/>- Compliance level"]
    
    ANALYZE --> CHECK3["Access Type<br/>- Full access risk<br/>- Admin privilege<br/>- Data access"]
    
    ANALYZE --> CHECK4["Justification<br/>- Business need clarity<br/>- Context relevance<br/>- Language analysis"]
    
    CHECK1 --> SCORE["Calculate Risk<br/>Score"]
    CHECK2 --> SCORE
    CHECK3 --> SCORE
    CHECK4 --> SCORE
    
    SCORE --> ROUTE{Risk Level}
    
    ROUTE -->|LOW<br/>0-25%| LOW["Low Risk<br/>- Auto-approve<br/>or<br/>- Simple review<br/>- Single approver"]
    
    ROUTE -->|MEDIUM<br/>26-60%| MED["Medium Risk<br/>- Manager review<br/>- System owner<br/>- Double approval"]
    
    ROUTE -->|HIGH<br/>61%+| HIGH["High Risk<br/>- Manager review<br/>- System owner<br/>- Security review<br/>- Triple approval"]
    
    LOW --> NOTIFY_L["Notify Approvers<br/>(Fast track)"]
    MED --> NOTIFY_M["Notify Approvers<br/>(Standard)"]
    HIGH --> NOTIFY_H["Notify Approvers<br/>(Escalated)"]
    
    NOTIFY_L --> PROCESS["Begin Approval<br/>Process"]
    NOTIFY_M --> PROCESS
    NOTIFY_H --> PROCESS
    
    PROCESS --> DECISION{Approved?}
    
    DECISION -->|YES| GRANT["Grant Access"]
    DECISION -->|NO| DENY["Deny Request"]
    
    GRANT --> END1[("Access Granted")]
    DENY --> END2[("Access Denied")]
```

## 11. Database Schema Relationships

```mermaid
graph TB
    User["CustomUser<br/>- id<br/>- username<br/>- email<br/>- department_id<br/>- employee_id<br/>- employment_status<br/>- role"]
    
    Dept["Department<br/>- id<br/>- name<br/>- code<br/>- parent_id<br/>- head_id"]
    
    System["System<br/>- id<br/>- name<br/>- code<br/>- owner_id<br/>- criticality<br/>- auth_type"]
    
    Access["UserSystemAccess<br/>- id<br/>- user_id<br/>- system_id<br/>- access_type<br/>- status<br/>- priority<br/>- start_date<br/>- end_date<br/>- justification"]
    
    Change["AccountChangeRequest<br/>- id<br/>- user_id<br/>- system_id<br/>- type<br/>- status<br/>- created_by_id<br/>- approved_by_id<br/>- created_at"]
    
    History["AccessHistory<br/>- id<br/>- access_id<br/>- action<br/>- changed_by_id<br/>- change_date<br/>- old_value<br/>- new_value"]
    
    Hardware["Hardware<br/>- id<br/>- serial<br/>- type<br/>- user_id<br/>- assigned_date"]
    
    Service["ServiceAccount<br/>- id<br/>- system_id<br/>- username<br/>- password_encrypted<br/>- last_rotation"]
    
    User -->|"1 to many"| Access
    User -->|"1 to many"| Dept
    User -->|"many to 1"| Dept
    Dept -->|"1 to many"| Dept
    
    System -->|"1 to many"| Access
    System -->|"1 to many"| Change
    System -->|"1 to many"| Service
    System -->|"many to 1"| User
    
    Access -->|"1 to many"| History
    User -->|"1 to many"| History
    User -->|"1 to many"| Change
    User -->|"1 to many"| Hardware
    
    Change -->|"many to 1"| User
    Change -->|"many to 1"| System
    
    Service -->|"many to 1"| User
```

## 12. Integration Architecture

```mermaid
graph TB
    UAMS["UAMS<br/>Core System"]
    
    LDAP["LDAP/Active<br/>Directory<br/>- User auth<br/>- Group mgmt<br/>- Profile sync"]
    
    EMAIL["Email System<br/>- Notifications<br/>- Approvals<br/>- Reports"]
    
    EXT["External Systems<br/>- AD<br/>- SAP<br/>- Salesforce<br/>- GitHub<br/>- AWS IAM<br/>- etc"]
    
    TICKET["Ticketing<br/>System<br/>- Change tickets<br/>- Status updates<br/>- Closures"]
    
    HRIS["HRIS System<br/>- Employee data<br/>- Org structure<br/>- Terminations"]
    
    MONITOR["Monitoring<br/>SIEM<br/>- Audit logs<br/>- Security events<br/>- Compliance"]
    
    UAMS -->|authenticate| LDAP
    UAMS -->|sync| LDAP
    UAMS -->|send/receive| EMAIL
    UAMS -->|sync to| EXT
    UAMS -->|create/update| TICKET
    UAMS -->|pull from| HRIS
    UAMS -->|push audit to| MONITOR
    
    LDAP -->|update groups| EXT
    TICKET -->|notify| EMAIL
    MONITOR -->|alerts| EMAIL
```

## 13. Activity Statuses & Transitions

```mermaid
graph LR
    START((" ")) --> PENDING["PENDING<br/>Awaiting Approval"]
    
    PENDING --> APPROVED["APPROVED<br/>Approved by Owner"]
    PENDING --> REJECTED["REJECTED<br/>Request Denied"]
    
    APPROVED --> ACTIVE["ACTIVE<br/>Access Granted"]
    APPROVED --> SUSPENDED["SUSPENDED<br/>Temporarily Disabled"]
    
    ACTIVE --> EXPIRED["EXPIRED<br/>Date Passed"]
    ACTIVE --> REVOKED["REVOKED<br/>Manually Removed"]
    ACTIVE --> SUSPENDED
    
    SUSPENDED --> ACTIVE
    SUSPENDED --> REVOKED
    SUSPENDED --> EXPIRED
    
    EXPIRED --> REVOKED
    REJECTED --> END((" "))
    REVOKED --> END
```

## 14. API Architecture

```mermaid
graph TB
    CLIENT["API Clients<br/>- Mobile<br/>- Web<br/>- External<br/>- Integration"]
    
    API["REST API<br/>Django REST Framework"]
    
    AUTH["API Authentication<br/>- Token Auth<br/>- OAuth2<br/>- JWT"]
    
    FILTERS["Filtering<br/>django-filter"]
    
    PAGINATE["Pagination<br/>LimitOffset"]
    
    VALIDATE["Serializers<br/>Validation"]
    
    MODELS["ViewSets<br/>Models"]
    
    PERMS["Permissions<br/>RBAC"]
    
    DB[("Database")]
    
    CLIENT --> API
    
    API --> AUTH
    API --> FILTERS
    API --> PAGINATE
    API --> VALIDATE
    
    AUTH --> PERMS
    FILTERS --> MODELS
    PAGINATE --> MODELS
    VALIDATE --> MODELS
    
    PERMS --> MODELS
    MODELS --> DB
```

---

**End of Visual Diagrams**

All diagrams above have been created using Mermaid.js and show:
- System architecture and layering
- Module dependencies
- Data relationships
- Complete workflows
- Integration points
- Database schema
- Status transitions
- API structure

These diagrams provide a comprehensive visual representation of the UAMS architecture and workflows.

# Change Management System - Architecture Diagrams

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Access Management System                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Accounts App                                   │   │
│  │  • CustomUser model                                      │   │
│  │  • LDAP Sync                                             │   │
│  │  └─ Signal: User Created/Updated ──┐                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                          │                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Service Accounts App                           │   │
│  │  • ServiceAccount model                                  │   │
│  │  • Credentials management                                │   │
│  │  └─ Signal: Service Account Changed ──┐                │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                          │                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Hardware App                                   │   │
│  │  • Asset tracking                                        │   │
│  │  • Assignment workflow                                   │   │
│  │  └─ Signal: Status Changed ──┐                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Access Management App                          │   │
│  │  • System Access model                                   │   │
│  │  • Approval workflow                                     │   │
│  │  └─ Signal: Access Approved/Revoked ──┐               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
└──────────────────────────┼───────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CHANGE MANAGEMENT APP                           │
│         (Automatic Integration & Tracking)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Signal Handlers (signals.py)                           │   │
│  │  • Capture change events                                │   │
│  │  • Preserve pre-save state                              │   │
│  │  • Auto-create change requests                          │   │
│  └────────────────┬────────────────────────────────────────┘   │
│                   │                                              │
│                   ▼                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Models                                                 │   │
│  │  • AccountChangeRequest                                 │   │
│  │  • ChangeAuditLog (immutable)                          │   │
│  └────────────────┬────────────────────────────────────────┘   │
│                   │                                              │
│                   ▼                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Workflow Engine (workflow.py)                          │   │
│  │  • ChangeRequestWorkflow                                │   │
│  │  • Approval logic                                       │   │
│  │  • Notification manager                                 │   │
│  │  • Integration hooks                                    │   │
│  └────────────────┬────────────────────────────────────────┘   │
│                   │                                              │
│        ┌──────────┼──────────┬──────────┐                       │
│        │          │          │          │                       │
│        ▼          ▼          ▼          ▼                       │
│  ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐               │
│  │  Admin  │ │ REST   │ │  CLI   │ │Python  │               │
│  │Interface│ │  API   │ │Command │ │  API   │               │
│  └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘               │
│       │          │          │          │                       │
└───────┼──────────┼──────────┼──────────┼───────────────────────┘
        │          │          │          │
        └──────────┴──────────┴──────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │   PostgreSQL DB      │
        │   • Change Requests  │
        │   • Audit Logs       │
        │   • Indexes          │
        └──────────────────────┘
```

---

## Signal Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Event Triggered                          │
│            (User Created / Status Changed / etc)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────┐
        │  Django Signal Receiver        │
        │  (signal handler in signals.py)│
        └────────┬───────────────────────┘
                 │
      ┌──────────┼──────────┐
      │          │          │
      ▼          ▼          ▼
  ┌────────┐ ┌────────┐ ┌────────┐
  │ Get    │ │Capture │ │Preserve│
  │Source  │ │Event   │ │ State  │
  │Object  │ │Details │ │(Before)│
  └───┬────┘ └───┬────┘ └───┬────┘
      │          │          │
      └──────────┼──────────┘
                 │
                 ▼
    ┌────────────────────────────────┐
    │ Create AccountChangeRequest    │
    │ • change_type: TYPE            │
    │ • user: Target User            │
    │ • system: Affected System      │
    │ • status: PENDING_APPROVAL     │
    │ • business_justification: Auto │
    │ • created_at: Now              │
    │ • created_by: System/Admin     │
    └───┬─────────────────────────────┘
        │
        ▼
    ┌────────────────────────────────┐
    │ Create ChangeAuditLog          │
    │ • action: "created"            │
    │ • performed_by: User           │
    │ • old_values: {} (new request) │
    │ • new_values: {...}            │
    │ • timestamp: Now               │
    │ • ip_address: Request IP       │
    │ • user_agent: Browser Info     │
    │ • immutable: True              │
    └───┬─────────────────────────────┘
        │
        ▼
    ┌────────────────────────────────┐
    │ Notify Stakeholders            │
    │ • Email System Owner           │
    │ • Email IT Approver            │
    │ • Log Event                    │
    │ • (if configured)              │
    └────────────────────────────────┘
```

---

## Approval Workflow State Machine

```
                    ┌─────────────────────┐
                    │   CREATED           │
                    │ (Auto by Signal)    │
                    └──────────┬──────────┘
                               │
                               ▼
                ┌──────────────────────────────┐
                │ PENDING_APPROVAL             │
                │ (Awaiting System Owner)      │
                └──┬─────────────┬─────────────┘
                   │             │
         ┌─────────┘             └─────────┐
         │                                  │
         ▼ (System Owner Rejects)   (Owner Approves) ▼
    ┌─────────────┐              ┌────────────────────────┐
    │  REJECTED   │              │ PENDING_IT_APPROVAL    │
    │             │              │ (Awaiting IT Review)   │
    │ [Terminal]  │              └──┬──────────┬──────────┘
    └─────────────┘                 │          │
                        ┌───────────┘          └──────────┐
                        │                                 │
               (IT Rejects) ▼                 (IT Approves) ▼
                    ┌─────────────┐         ┌──────────────────┐
                    │  REJECTED   │         │  COMPLETED       │
                    │             │         │                  │
                    │ [Terminal]  │         │ [Terminal-Done]  │
                    └─────────────┘         └──────────────────┘

Manual Operations:
├─ Mark as Completed (bypass IT approval)
├─ Reopen (return to pending)
└─ Cancel (cancel request)
```

---

## API Endpoint Architecture

```
http://localhost:8000/
│
├─ /admin/
│  └─ Change Management > Change Requests
│     (Web UI for approvals)
│
├─ /api/
│  │
│  └─ /change-requests/
│     │
│     ├─ GET       List all changes (filtered, paginated)
│     ├─ POST      Create new change request
│     ├─ GET /{id} View specific change request
│     ├─ PUT /{id} Update change request
│     ├─ DELETE /{id} Delete change request
│     │
│     ├─ POST /{id}/approve/
│     │  └─ Approve change request
│     │
│     ├─ POST /{id}/reject/
│     │  └─ Reject change request
│     │
│     ├─ POST /{id}/mark-completed/
│     │  └─ Mark as completed
│     │
│     ├─ GET /statistics/
│     │  └─ Get system statistics
│     │
│     ├─ GET /pending-approvals/
│     │  └─ List pending approvals
│     │
│     └─ POST /bulk-action/
│        └─ Bulk operations (approve multiple, etc)
│
└─ /command-line/
   └─ python manage.py process_changes
      ├─ --list-pending
      ├─ --approve-all
      ├─ --complete-old
      ├─ --system <name>
      ├─ --statistics
      └─ --dry-run
```

---

## Data Model Relationships

```
┌─────────────────────────────────────┐
│   CustomUser (from Accounts)        │
│  ┌─────────────────────────────────┐│
│  │ • id (PK)                       ││
│  │ • username                      ││
│  │ • email                         ││
│  │ • full_name                     ││
│  │ • department                    ││
│  └──────────────┬────────────────┬─┘│
└─────────────────┼────────────────┼──┘
                  │ ↓ (FK)         │
┌─────────────────┴────────────────┴──────────────────────┐
│                AccountChangeRequest                     │
│  ┌─────────────────────────────────────────────────────┐│
│  │ • id (PK)                                           ││
│  │ • change_id (unique_id)                             ││
│  │ • user (FK) → CustomUser                            ││
│  │ • change_type (ENUM)                                ││
│  │ • system                                            ││
│  │ • status (ENUM)                                     ││
│  │ • business_justification                            ││
│  │ • system_owner_approved (boolean)                   ││
│  │ • system_owner_approved_at                          ││
│  │ • system_owner_notes                                ││
│  │ • system_owner (FK) → CustomUser                    ││
│  │ • it_approved (boolean)                             ││
│  │ • it_approved_at                                    ││
│  │ • it_approval_notes                                 ││
│  │ • it_approver (FK) → CustomUser                     ││
│  │ • completed_at                                      ││
│  │ • created_at                                        ││
│  │ • updated_at                                        ││
│  │ • created_by (FK)                                   ││
│  └──────────────┬─────────────────────────────────────┘│
└─────────────────┼──────────────────────────────────────┘
                  │ ↓ (Reverse FK)
┌─────────────────┴──────────────────────────────────────┐
│              ChangeAuditLog                            │
│  ┌──────────────────────────────────────────────────────┐
│  │ • id (PK)                                            │
│  │ • change_request (FK)                                │
│  │ • action (created/approved/rejected/completed)       │
│  │ • performed_by (FK) → CustomUser                     │
│  │ • timestamp                                          │
│  │ • old_values (JSON)                                  │
│  │ • new_values (JSON)                                  │
│  │ • ip_address                                         │
│  │ • user_agent                                         │
│  │ • notes                                              │
│  │ • immutable = True                                   │
│  └──────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────┘
```

---

## Request Flow Through System

```
┌─────────────────────────────────────────────────────────────┐
│                  Incoming Request                           │
│         (Create User / Grant Access / etc)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────────┐
            │   Django Signal Fires      │
            │   (post_save, post_delete) │
            └────────────┬───────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  Signal Handler in change_mgmt    │
        │  └─ Check if change needed        │
        │  └─ Capture old state             │
        │  └─ Prepare change data           │
        └────────────┬───────────────────────┘
                     │
                     ▼
    ┌────────────────────────────────────────┐
    │  Create AccountChangeRequest           │
    │  • Auto-filled fields                  │
    │  • Status = PENDING_APPROVAL           │
    │  • Audit trail linked                  │
    └────────────┬───────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────────────────┐
    │  Create ChangeAuditLog Entry           │
    │  • Record who/what/when/where          │
    │  • Immutable record created            │
    └────────────┬───────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────────────────┐
    │  Notify Approvers                      │
    │  • Email to System Owner               │
    │  • Email to IT Approver                │
    │  • Log entry created                   │
    └────────────┬───────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────────────────┐
    │  Return Control to Original Process    │
    │  (User/Access/Hardware creation done)  │
    └────────────────────────────────────────┘
```

---

## Technology Stack Diagram

```
┌──────────────────────────────────────────────────────┐
│                  Django 5.2.6                        │
├──────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────┐ │
│ │  Django ORM                                      │ │
│ │  • Models: AccountChangeRequest, AuditLog       │ │
│ │  • Signals: Automatic event triggering          │ │
│ │  • Admin: Custom admin interface                │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────┐ │
│ │  Django REST Framework 3.14.0                   │ │
│ │  • ViewSet: REST API endpoints                  │ │
│ │  • Serializers: JSON serialization              │ │
│ │  • Authentication: Token + Session              │ │
│ │  • Permissions: IsAuthenticated                 │ │
│ └──────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────┐ │
│ │  Django Filters 23.5                            │ │
│ │  • Filtering: Multiple field types              │ │
│ │  • Search: Full-text search                     │ │
│ │  • Ordering: Sort results                       │ │
│ └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌──────────────────────────────┐
        │    PostgreSQL Database       │
        │  • Tables for models         │
        │  • Indexes for performance   │
        │  • ACID transactions         │
        │  • Immutable audit logs      │
        └──────────────────────────────┘
```

---

## Deployment Architecture

```
Internet
   │
   └─▶ Load Balancer (HAProxy/Nginx) ──┐
                                        │
       ┌────────────────────────────────┴────────────────────┐
       │                                                      │
       ▼                              ▼                      ▼
   [App1]                         [App2]                 [App3]
   Gunicorn                        Gunicorn               Gunicorn
   Port 8000                       Port 8001              Port 8002
   (4 workers)                     (4 workers)            (4 workers)
   │                                │                      │
   └────────────────────────────────┼──────────────────────┘
                                    │
                                    ▼
                        PostgreSQL Database
                        (Replicated for HA)
                        │
                        ├─ Master (Write)
                        ├─ Replica 1 (Read)
                        └─ Replica 2 (Read)

Optional Components:
├─ Redis Cache
├─ Celery Workers (async tasks)
├─ Sentry (error tracking)
├─ ELK Stack (logging)
└─ Prometheus (monitoring)
```

---

## Code Organization

```
change_management/
│
├─ __init__.py
│
├─ models.py
│  ├─ AccountChangeRequest (main model)
│  └─ ChangeAuditLog (audit trail)
│
├─ signals.py (380 lines)
│  ├─ track_user_creation_or_modification()
│  ├─ track_service_account_change()
│  ├─ track_hardware_status_change()
│  ├─ track_system_access_change()
│  └─ preserve_pre_save_state()
│
├─ serializers.py (180 lines)
│  ├─ ChangeRequestListSerializer
│  ├─ ChangeRequestDetailSerializer
│  ├─ ChangeApprovalSerializer
│  ├─ ChangeRejectionSerializer
│  ├─ ChangeStatisticsSerializer
│  ├─ BulkActionSerializer
│  ├─ UserNestedSerializer
│  └─ SystemNestedSerializer
│
├─ workflow.py (380 lines)
│  ├─ ChangeRequestWorkflow class
│  │  ├─ create_account_change()
│  │  ├─ approve_change()
│  │  ├─ reject_change()
│  │  ├─ complete_change()
│  │  ├─ get_pending_approvals()
│  │  └─ get_overdue_approvals()
│  ├─ ChangeNotificationManager class
│  │  ├─ notify_approval_required()
│  │  ├─ notify_approved()
│  │  └─ notify_rejected()
│  └─ ChangeIntegrationHelper class
│
├─ views.py
│  ├─ Previous views (unchanged)
│  └─ AccountChangeRequestViewSet (NEW - 430+ lines)
│     ├─ list()
│     ├─ retrieve()
│     ├─ create()
│     ├─ update()
│     ├─ destroy()
│     ├─ @action approve()
│     ├─ @action reject()
│     ├─ @action mark_completed()
│     ├─ @action statistics()
│     ├─ @action pending_approvals()
│     └─ @action bulk_action()
│
├─ admin.py (Enhanced)
│  ├─ ChangeRequestAdmin class
│  │  ├─ Organized fieldsets
│  │  ├─ list_filter
│  │  ├─ search_fields
│  │  ├─ actions (bulk)
│  │  └─ readonly_fields
│  └─ ChangeAuditLogAdmin (read-only)
│
├─ admin_actions.py (120 lines)
│  ├─ approve_change_requests()
│  ├─ reject_change_requests()
│  └─ mark_changes_completed()
│
├─ urls.py (Enhanced)
│  └─ REST API router registration
│
├─ apps.py (Enhanced)
│  └─ ready() method with signal registration
│
├─ management/
│  └─ commands/
│     └─ process_changes.py (270 lines)
│        ├─ --list-pending
│        ├─ --approve-all
│        ├─ --complete-old
│        ├─ --system filter
│        ├─ --dry-run
│        └─ --statistics
│
└─ migrations/
   ├─ 0001_initial.py
   ├─ 0002_changeauditlog.py (NEW)
   └─ ...
```

---

This visual architecture provides a comprehensive understanding of how all components work together to create a fully integrated change management system.

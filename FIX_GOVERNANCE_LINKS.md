# Fix Summary: Evidence Upload and Attestation Page Not Found Error

## Problem
Users were seeing a 404 error when clicking on "Upload Evidence" and "Attestation" links in the sidebar:
```
Page not found (404)
No UserSystemAccess matches the given query.
Request URL: http://127.0.0.1:8000/access-management/assignments/0/attest/
```

## Root Cause
The navigation.html had hardcoded links with `access_id=0`:
```html
<a href="{% url 'access_management:upload_evidence' access_id=0 %}">Upload Evidence</a>
<a href="{% url 'access_management:attest_access' access_id=0 %}">Attestation</a>
```

These views require a valid `UserSystemAccess` object ID, not a placeholder value.

## Solution
Implemented a two-part fix:

### 1. Removed Hardcoded Sidebar Links (navigation.html)
- Removed the "Upload Evidence" link with `access_id=0`
- Removed the "Attestation" link with `access_id=0`
- These actions require a specific assignment context

### 2. Added Governance Action Buttons (access_assignment_detail.html)
Added a new "Governance Actions" section in the assignment detail page with four buttons:
- **Upload Evidence** - Upload evidence artifacts for this assignment
- **Evidence Gallery** - View uploaded evidence
- **Attest Access** - Create attestation for this assignment
- **Revoke Access** - Revoke this access assignment

These buttons now properly pass the current assignment ID:
```html
<a href="{% url 'access_management:upload_evidence' access_assignment.pk %}">
    Upload Evidence
</a>
<a href="{% url 'access_management:evidence_gallery' access_assignment.pk %}">
    Evidence Gallery
</a>
<a href="{% url 'access_management:attest_access' access_assignment.pk %}">
    Attest Access
</a>
<a href="{% url 'access_management:revoke_access' access_assignment.pk %}">
    Revoke Access
</a>
```

## User Workflow
1. User navigates to **Access → Access Assignments**
2. User clicks on an assignment to view details
3. Clicks on **Governance Actions** buttons to:
   - Upload evidence for the assignment
   - View evidence gallery
   - Attest to the access
   - Revoke the access

## Files Modified
- `templates/navigation.html` - Removed hardcoded evidence/attestation links
- `access_management/templates/access_management/access_assignment_detail.html` - Added governance action buttons

## Status
✅ Fixed - Evidence upload, gallery, attestation, and revocation now accessible from assignment detail pages with proper context.

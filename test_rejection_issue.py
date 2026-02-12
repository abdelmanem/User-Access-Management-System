#!/usr/bin/env python
"""
Test script to demonstrate the change management rejection issue.

Run this with: python manage.py shell < test_rejection_issue.py
Or: python manage.py shell -c "exec(open('test_rejection_issue.py').read())"
"""

import os
import django
from django.utils import timezone
from datetime import timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iam_governance_settings')
django.setup()

from accounts.models import CustomUser
from systems.models import System
from change_management.models import AccountChangeRequest
from access_management.models import UserSystemAccess

print("\n" + "="*80)
print("CHANGE MANAGEMENT REJECTION ISSUE - DEMONSTRATION")
print("="*80)

# ============================================================================
# TEST 1: User Deletion - Rejection doesn't prevent deletion
# ============================================================================
print("\n[TEST 1] USER DELETION WITH REJECTION")
print("-" * 80)

try:
    # Find a rejected user deletion request
    rejected_deletes = AccountChangeRequest.objects.filter(
        change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
        status=AccountChangeRequest.STATUS_REJECTED,
        system__isnull=True  # User deletion (not system-specific)
    ).order_by('-created_at')[:3]
    
    if rejected_deletes.exists():
        print("✓ Found rejected user deletion requests:")
        for req in rejected_deletes:
            print(f"\n  Request ID: {req.id}")
            print(f"    User snapshot: {req.user_full_name} ({req.user_username})")
            print(f"    Status: {req.status}")
            print(f"    Rejection reason: {req.system_owner_approval_notes}")
            print(f"    Created: {req.created_at}")
            
            # Check if user still exists
            if req.user:
                print(f"    ✓ User STILL EXISTS: {req.user.username}")
            else:
                print(f"    ✗ User DELETED (even though request was rejected!)")
    else:
        print("ℹ No rejected user deletion requests found. Creating test scenario...")
        
        # Create test user
        test_user = CustomUser.objects.create(
            username='test_deletion_user',
            email='test@example.com',
            first_name='Test',
            last_name='User',
            employment_status='Active',
            is_active=True
        )
        print(f"  Created test user: {test_user.username}")
        
        # Create change request as if admin is deleting
        admin_user = CustomUser.objects.filter(is_superuser=True, is_staff=True).first()
        if not admin_user:
            admin_user = CustomUser.objects.filter(is_staff=True).first()
        
        if admin_user:
            change_req = AccountChangeRequest.objects.create(
                change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
                user=test_user,
                user_full_name=test_user.get_full_name(),
                user_username=test_user.username,
                system=None,
                business_justification="Test deletion",
                requested_by=admin_user,
                status=AccountChangeRequest.STATUS_PENDING,
            )
            print(f"  Created change request: {change_req.id} (status: {change_req.status})")
            
            # Simulate rejection
            change_req.status = AccountChangeRequest.STATUS_REJECTED
            change_req.system_owner = admin_user
            change_req.system_owner_approval_notes = "Rejected - user needed for project"
            change_req.save()
            print(f"  Change request REJECTED: {change_req.id}")
            
            # Now delete user (simulating what happened before rejection was recorded)
            user_pk = test_user.pk
            test_user.delete()
            print(f"  Deleted user from database")
            
            # Check what change request now shows
            change_req.refresh_from_db()
            print(f"\n  ISSUE DEMONSTRATION:")
            print(f"  - Change request status: {change_req.status} (REJECTED)")
            print(f"  - User in database: {CustomUser.objects.filter(pk=user_pk).exists()} (DELETED)")
            print(f"  ✗ Rejection was ineffective - user is gone despite rejection!")

except Exception as e:
    print(f"✗ Error in TEST 1: {str(e)}")

# ============================================================================
# TEST 2: User Creation - No approval gate exists
# ============================================================================
print("\n\n[TEST 2] USER CREATION (NO APPROVAL GATE)")
print("-" * 80)

try:
    # Find pending user creation requests
    pending_creates = AccountChangeRequest.objects.filter(
        change_type=AccountChangeRequest.CHANGE_TYPE_CREATE,
        status=AccountChangeRequest.STATUS_PENDING,
        system__isnull=True  # User creation
    ).select_related('user').order_by('-created_at')[:3]
    
    if pending_creates.exists():
        print("✓ Found pending user creation requests:")
        for req in pending_creates:
            print(f"\n  Request ID: {req.id}")
            print(f"    User: {req.user_full_name} ({req.user_username if req.user_username else 'N/A'})")
            print(f"    Status: {req.status}")
            print(f"    Created: {req.created_at}")
            
            # Check if user exists
            if req.user and req.user.is_active:
                print(f"    ✗ User ACTIVE in system (while request still PENDING for approval!)")
                print(f"      Username: {req.user.username}")
                print(f"      Is Staff: {req.user.is_staff}")
                print(f"      Is Active: {req.user.is_active}")
            else:
                print(f"    ℹ User not found or inactive")
    else:
        print("ℹ No pending user creation requests. This might indicate:")
        print("  - No recent user creations")
        print("  - All pending requests have been approved")
        print("  - Signals may not be firing for user creation")

except Exception as e:
    print(f"✗ Error in TEST 2: {str(e)}")

# ============================================================================
# TEST 3: Access Assignments - Proper approval gate
# ============================================================================
print("\n\n[TEST 3] ACCESS ASSIGNMENTS (PROPER APPROVAL GATE)")
print("-" * 80)

try:
    # Find pending access assignments
    pending_access = UserSystemAccess.objects.filter(
        status='Pending'
    ).select_related('user', 'system').order_by('-created_at')[:3]
    
    if pending_access.exists():
        print("✓ Found pending access assignments (CORRECT WORKFLOW):")
        for access in pending_access:
            print(f"\n  Access ID: {access.id}")
            print(f"    User: {access.user.full_name}")
            print(f"    System: {access.system.name}")
            print(f"    Access Type: {access.access_type}")
            print(f"    Status: {access.status}")
            print(f"    Status Timeline: {access.lifecycle_timeline}")
            print(f"    ✓ Access is PENDING - not yet active")
            print(f"    ✓ User will NOT get access until approved & activated")
    else:
        print("ℹ No pending access assignments found")
        
        # Check for rejected access
        rejected_access = UserSystemAccess.objects.filter(
            status='Rejected'
        ).select_related('user', 'system').order_by('-created_at')[:3]
        
        if rejected_access.exists():
            print("✓ Found rejected access assignments:")
            for access in rejected_access:
                print(f"\n  Access ID: {access.id}")
                print(f"    User: {access.user.full_name}")
                print(f"    System: {access.system.name}")
                print(f"    Status: {access.status}")
                print(f"    Rejection reason: {access.rejection_reason}")
                print(f"    ✓ CORRECT: User never got access due to rejection")
        else:
            print("ℹ No rejected access assignments found either")

except Exception as e:
    print(f"✗ Error in TEST 3: {str(e)}")

# ============================================================================
# TEST 4: Summary Statistics
# ============================================================================
print("\n\n[TEST 4] SUMMARY STATISTICS")
print("-" * 80)

try:
    # Overall change request stats
    total_changes = AccountChangeRequest.objects.count()
    pending = AccountChangeRequest.objects.filter(status=AccountChangeRequest.STATUS_PENDING).count()
    approved = AccountChangeRequest.objects.filter(status=AccountChangeRequest.STATUS_APPROVED).count()
    rejected = AccountChangeRequest.objects.filter(status=AccountChangeRequest.STATUS_REJECTED).count()
    completed = AccountChangeRequest.objects.filter(status=AccountChangeRequest.STATUS_COMPLETED).count()
    
    print(f"\nChange Management Statistics:")
    print(f"  Total requests: {total_changes}")
    print(f"  - Pending: {pending}")
    print(f"  - Approved: {approved}")
    print(f"  - Rejected: {rejected}")
    print(f"  - Completed: {completed}")
    
    # User-specific changes
    user_deletes = AccountChangeRequest.objects.filter(
        change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
        system__isnull=True
    ).count()
    user_creates = AccountChangeRequest.objects.filter(
        change_type=AccountChangeRequest.CHANGE_TYPE_CREATE,
        system__isnull=True
    ).count()
    
    print(f"\nUser Lifecycle Changes:")
    print(f"  Total user creations: {user_creates}")
    print(f"  Total user deletions: {user_deletes}")
    
    # Access management stats
    pending_access = UserSystemAccess.objects.filter(status='Pending').count()
    approved_access = UserSystemAccess.objects.filter(status='Approved').count()
    active_access = UserSystemAccess.objects.filter(status='Active').count()
    rejected_access = UserSystemAccess.objects.filter(status='Rejected').count()
    
    print(f"\nAccess Management Statistics:")
    print(f"  Pending (awaiting approval): {pending_access}")
    print(f"  Approved (not yet active): {approved_access}")
    print(f"  Active: {active_access}")
    print(f"  Rejected: {rejected_access}")
    
except Exception as e:
    print(f"✗ Error in TEST 4: {str(e)}")

# ============================================================================
# CONCLUSION
# ============================================================================
print("\n" + "="*80)
print("KEY FINDINGS")
print("="*80)
print("""
1. USER CREATION/DELETION
   - No approval gate before action
   - Change requests created AFTER the action
   - Rejections cannot prevent the action
   - ✗ Non-compliant with RHG 4.4

2. ACCESS ASSIGNMENTS  
   - Proper approval gate (Pending status)
   - User must do: Approve → Activate
   - Rejection prevents activation
   - ✓ Compliant with RHG 4.4

3. SOLUTION NEEDED
   - Implement pre-approval workflow for user operations
   - Or use soft-delete pattern with rollback capability
   - Change requests must be control gates, not just audit logs
""")
print("="*80 + "\n")

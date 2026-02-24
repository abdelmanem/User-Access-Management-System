"""
Signals for automatic change management integration with other applications.

This module automatically creates AccountChangeRequest records when:
1. User accounts are created/modified/deleted in accounts app
2. Service accounts are created/modified/deleted
3. Hardware assets status changes
4. System access is approved/revoked
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist

from .models import AccountChangeRequest
from accounts.models import CustomUser
from service_accounts.models import ServiceAccount
from hardware.models import HardwareAsset
from access_management.models import UserSystemAccess
from systems.models import System

import logging

logger = logging.getLogger(__name__)

CustomUserModel = get_user_model()


# =============================================================================
# CUSTOM USER SIGNALS - Track user account changes
# =============================================================================

@receiver(post_save, sender=CustomUser)
def track_user_creation_or_modification(sender, instance, created, **kwargs):
    """
    Automatically create AccountChangeRequest when a user is created or modified.
    
    Only tracks "interesting" changes (not metadata updates).
    """
    if not instance:
        return
    
    try:
        # Skip system/admin accounts
        if instance.username in ['admin', 'system', 'anonymous']:
            return
        
        # For new users, create a PENDING account creation request
        if created:
            # Find default system (AD/LDAP)
            try:
                ad_system = System.objects.filter(
                    code__in=['AD', 'LDAP', 'ACTIVE_DIRECTORY']
                ).first()
                
                if not ad_system:
                    # Fallback to any system if AD not found
                    ad_system = System.objects.first()
                
                if ad_system:
                    AccountChangeRequest.objects.create(
                        change_type=AccountChangeRequest.CHANGE_TYPE_CREATE,
                        user=instance,
                        system=ad_system,
                        requested_by=instance,  # User requesting their own account
                        business_justification=f"New employee {instance.full_name} ({instance.employee_id}) - account provisioning",
                        status=AccountChangeRequest.STATUS_PENDING,
                    )
                    logger.info(f"Created AccountChangeRequest for new user: {instance.username}")
            except Exception as e:
                logger.error(f"Error creating change request for user {instance.username}: {str(e)}")
        
        else:
            # For modifications, track changes to critical fields
            critical_fields = [
                'employment_status', 'is_active', 'is_staff', 'is_superuser',
                'department', 'manager', 'employment_type'
            ]
            
            # Check if this is an employment status change (Terminated)
            if hasattr(instance, '_state'):
                old_status = getattr(instance, '_old_employment_status', None)
                new_status = instance.employment_status
                
                if old_status and old_status != new_status and new_status == 'Terminated':
                    try:
                        ad_system = System.objects.filter(
                            code__in=['AD', 'LDAP', 'ACTIVE_DIRECTORY']
                        ).first() or System.objects.first()
                        
                        if ad_system:
                            AccountChangeRequest.objects.create(
                                change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
                                user=instance,
                                system=ad_system,
                                business_justification=f"User {instance.full_name} terminated - account deprovisioning",
                                status=AccountChangeRequest.STATUS_PENDING,
                            )
                            logger.info(f"Created account deletion request for terminated user: {instance.username}")
                    except Exception as e:
                        logger.error(f"Error creating deletion request for user {instance.username}: {str(e)}")
    
    except Exception as e:
        logger.error(f"Signal error in track_user_creation_or_modification: {str(e)}")


@receiver(pre_save, sender=CustomUser)
def store_old_user_state(sender, instance, **kwargs):
    """Store the old state before saving to detect changes."""
    if instance.pk:  # Only for existing records
        try:
            old_instance = CustomUser.objects.get(pk=instance.pk)
            instance._old_employment_status = old_instance.employment_status
            instance._old_is_active = old_instance.is_active
        except CustomUser.DoesNotExist:
            pass


# =============================================================================
# SERVICE ACCOUNT SIGNALS - Track service account changes
# =============================================================================

@receiver(post_save, sender=ServiceAccount)
def track_service_account_change(sender, instance, created, **kwargs):
    """
    Automatically create AccountChangeRequest when service account is created/modified.
    """
    if not instance:
        return
    
    try:
        if created:
            AccountChangeRequest.objects.create(
                change_type=AccountChangeRequest.CHANGE_TYPE_CREATE,
                system=instance.system,
                requested_by=instance.owner,
                business_justification=f"Service account creation: {instance.account_name} - {instance.purpose}",
                status=AccountChangeRequest.STATUS_PENDING,
            )
            logger.info(f"Created AccountChangeRequest for new service account: {instance.account_name}")
        
        else:
            # Track if service account is being deactivated
            if hasattr(instance, '_old_is_active'):
                old_active = instance._old_is_active
                if old_active and not instance.is_active:
                    AccountChangeRequest.objects.create(
                        change_type=AccountChangeRequest.CHANGE_TYPE_SUSPEND,
                        system=instance.system,
                        requested_by=instance.owner,
                        business_justification=f"Service account suspended: {instance.account_name}",
                        status=AccountChangeRequest.STATUS_PENDING,
                    )
                    logger.info(f"Created account suspension request for service account: {instance.account_name}")
    
    except Exception as e:
        logger.error(f"Signal error in track_service_account_change: {str(e)}")


@receiver(pre_save, sender=ServiceAccount)
def store_old_service_account_state(sender, instance, **kwargs):
    """Store the old state before saving."""
    if instance.pk:
        try:
            old_instance = ServiceAccount.objects.get(pk=instance.pk)
            instance._old_is_active = old_instance.is_active
        except ServiceAccount.DoesNotExist:
            pass


@receiver(post_delete, sender=ServiceAccount)
def track_service_account_deletion(sender, instance, **kwargs):
    """Track when service accounts are deleted."""
    if not instance:
        return
    
    try:
        AccountChangeRequest.objects.create(
            change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
            system=instance.system,
            requested_by=instance.owner,
            business_justification=f"Service account deleted: {instance.account_name}",
            status=AccountChangeRequest.STATUS_COMPLETED,
        )
        logger.info(f"Recorded deletion of service account: {instance.account_name}")
    except Exception as e:
        logger.error(f"Signal error in track_service_account_deletion: {str(e)}")


# =============================================================================
# HARDWARE ASSET SIGNALS - Track hardware status changes
# =============================================================================

@receiver(post_save, sender=HardwareAsset)
def track_hardware_status_change(sender, instance, created, **kwargs):
    """
    Track significant hardware asset changes.
    
    Triggers for: status changes, assignment changes
    """
    if not instance:
        return
    
    try:
        if created:
            # New hardware asset provisioned
            logger.info(f"New hardware asset created: {instance.asset_tag} ({instance.name})")
        
        else:
            # Check for status changes (Retired, Disposed, etc.)
            if hasattr(instance, '_old_status'):
                old_status = instance._old_status
                new_status = instance.status
                
                if old_status != new_status:
                    if new_status in ['Retired', 'Disposed']:
                        # Record the asset change
                        logger.info(
                            f"Hardware asset {instance.asset_tag} status changed "
                            f"from {old_status} to {new_status}"
                        )
    
    except Exception as e:
        logger.error(f"Signal error in track_hardware_status_change: {str(e)}")


@receiver(pre_save, sender=HardwareAsset)
def store_old_hardware_state(sender, instance, **kwargs):
    """Store the old state before saving."""
    if instance.pk:
        try:
            old_instance = HardwareAsset.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except HardwareAsset.DoesNotExist:
            pass


# =============================================================================
# USER SYSTEM ACCESS SIGNALS - Track access grant/revoke
# =============================================================================

@receiver(post_save, sender=UserSystemAccess)
def track_system_access_change(sender, instance, created, **kwargs):
    """
    Track when user system access is approved or revoked.
    
    Creates AccountChangeRequest for:
    - New access grants (status changes to Active/Approved)
    - Access revocation (status changes to Revoked/Suspended)
    """
    if not instance:
        return
    
    try:
        # Track when access is activated/approved
        if instance.status in ['Active', 'Approved']:
            if created or (hasattr(instance, '_old_status') and instance._old_status == 'Pending'):
                # Check if change request already exists for this
                existing = AccountChangeRequest.objects.filter(
                    user=instance.user,
                    system=instance.system,
                    status__in=[
                        AccountChangeRequest.STATUS_PENDING,
                        AccountChangeRequest.STATUS_APPROVED
                    ]
                ).first()
                
                if not existing:
                    # Get system owner if available
                    system_owner = getattr(instance.system, 'system_owner', None)
                    
                    AccountChangeRequest.objects.create(
                        change_type=AccountChangeRequest.CHANGE_TYPE_CREATE,
                        user=instance.user,
                        system=instance.system,
                        requested_by=instance.requested_by,
                        business_justification=f"Access request approved for {instance.access_type} to {instance.system.name}",
                        status=AccountChangeRequest.STATUS_APPROVED,
                        system_owner_approved=True,
                        system_owner_approval_date=timezone.now(),
                        system_owner=system_owner,
                    )
                    logger.info(
                        f"Created AccountChangeRequest for access approval: "
                        f"{instance.user.username} -> {instance.system.name}"
                    )
        
        # Track when access is revoked or suspended
        elif instance.status in ['Revoked', 'Suspended']:
            if hasattr(instance, '_old_status') and instance._old_status not in ['Revoked', 'Suspended']:
                AccountChangeRequest.objects.create(
                    change_type=AccountChangeRequest.CHANGE_TYPE_DELETE,
                    user=instance.user,
                    system=instance.system,
                    business_justification=f"Access revoked/suspended for {instance.system.name}",
                    status=AccountChangeRequest.STATUS_COMPLETED,
                )
                logger.info(
                    f"Created access revocation request: "
                    f"{instance.user.username} <- {instance.system.name}"
                )
    
    except Exception as e:
        logger.error(f"Signal error in track_system_access_change: {str(e)}")


@receiver(pre_save, sender=UserSystemAccess)
def store_old_access_state(sender, instance, **kwargs):
    """Store the old state before saving."""
    if instance.pk:
        try:
            old_instance = UserSystemAccess.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except UserSystemAccess.DoesNotExist:
            pass


# =============================================================================
# UNIFIED APPROVAL SIGNAL - Sync change request approval to access assignment
# =============================================================================

@receiver(post_save, sender=AccountChangeRequest)
def sync_change_request_approval_to_access(sender, instance, **kwargs):
    """
    When a change request is approved or completed, automatically update all linked access assignments
    to mark them as Approved and set the approval metadata.
    
    This implements the unified approval workflow: approve in change management,
    see the result reflected in access assignments.
    """
    # Sync when change request reaches Approved or Completed status
    if not instance or instance.status not in [AccountChangeRequest.STATUS_APPROVED, AccountChangeRequest.STATUS_COMPLETED]:
        return
    
    try:
        # Find all related access assignments that are still pending and update them
        access_assignments = instance.access_assignments.filter(status='Pending')
        
        for access_assignment in access_assignments:
            # Update the access assignment to Approved status
            access_assignment.status = 'Approved'
            access_assignment.approved_by = instance.system_owner
            access_assignment.approval_date = instance.system_owner_approval_date
            access_assignment.approval_comments = instance.system_owner_approval_notes or ''
            access_assignment.updated_by = instance.requested_by
            access_assignment.save(update_fields=[
                'status', 'approved_by', 'approval_date', 'approval_comments', 'updated_by'
            ])
            
            logger.info(
                f"Auto-approved access assignment {access_assignment.pk} "
                f"for {access_assignment.user.username} -> {access_assignment.system.name} "
                f"via change request {instance.pk} (status: {instance.status})"
            )
    
    except Exception as e:
        logger.error(f"Signal error in sync_change_request_approval_to_access: {str(e)}")


@receiver(post_save, sender=AccountChangeRequest)
def sync_change_request_rejection_to_access(sender, instance, **kwargs):
    """
    When a change request is rejected, automatically update all linked access assignments
    to mark them as Rejected.
    """
    if not instance or instance.status != AccountChangeRequest.STATUS_REJECTED:
        return
    
    try:
        # Find all related pending access assignments and reject them
        access_assignments = instance.access_assignments.filter(status='Pending')
        
        for access_assignment in access_assignments:
            # Update the access assignment to Rejected status
            access_assignment.status = 'Rejected'
            access_assignment.rejection_reason = getattr(
                instance, 'rejection_notes', 
                'Change request was rejected in change management workflow'
            )
            access_assignment.updated_by = instance.requested_by
            access_assignment.save(update_fields=['status', 'rejection_reason', 'updated_by'])
            
            logger.info(
                f"Auto-rejected access assignment {access_assignment.pk} "
                f"for {access_assignment.user.username} -> {access_assignment.system.name} "
                f"via change request {instance.pk}"
            )
    
    except Exception as e:
        logger.error(f"Signal error in sync_change_request_rejection_to_access: {str(e)}")


# =============================================================================
# SIGNAL REGISTRATION
# =============================================================================

def register_change_management_signals():
    """
    Register all change management signals.
    
    Call this in apps.py ready() method to ensure signals are registered.
    """
    logger.info("Change management signals registered")

"""
Workflow utilities for change management.

Provides helper functions for managing change request workflows and integrations.
"""

from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from .models import AccountChangeRequest
from .audit import log_change_action

User = get_user_model()

import logging

logger = logging.getLogger(__name__)


class ChangeRequestWorkflow:
    """Helper class for managing change request workflows."""
    
    @staticmethod
    def create_account_change(
        change_type,
        system,
        business_justification,
        user=None,
        requested_by=None,
        system_owner=None,
    ):
        """
        Create a new account change request.
        
        Args:
            change_type: Type of change (Create, Modify, Delete, Suspend)
            system: The System object
            business_justification: Reason for the change
            user: Optional user affected by the change
            requested_by: User making the request
            system_owner: Optional system owner to auto-assign
        
        Returns:
            Created AccountChangeRequest instance
        """
        try:
            with transaction.atomic():
                change_request = AccountChangeRequest.objects.create(
                    change_type=change_type,
                    system=system,
                    business_justification=business_justification,
                    user=user,
                    requested_by=requested_by,
                    system_owner=system_owner,
                    status=AccountChangeRequest.STATUS_PENDING,
                )
                
                # Log the creation
                log_change_action(
                    change_request,
                    'created',
                    requested_by,
                    notes=f"Created {change_type} request"
                )
                
                logger.info(
                    f"Created change request {change_request.id}: "
                    f"{change_type} in {system.name}"
                )
                
                return change_request
        
        except Exception as e:
            logger.error(f"Error creating change request: {str(e)}")
            raise

    @staticmethod
    def approve_change(change_request, approved_by, approval_notes=None):
        """
        Approve a change request.
        
        Args:
            change_request: AccountChangeRequest instance
            approved_by: User approving the change
            approval_notes: Optional approval notes
        
        Returns:
            Updated AccountChangeRequest
        """
        try:
            with transaction.atomic():
                old_status = change_request.status
                
                change_request.status = AccountChangeRequest.STATUS_APPROVED
                change_request.system_owner = approved_by
                change_request.system_owner_approved = True
                change_request.system_owner_approval_date = timezone.now()
                if approval_notes:
                    change_request.system_owner_approval_notes = approval_notes
                change_request.save()
                
                # Log the approval
                log_change_action(
                    change_request,
                    'approved',
                    approved_by,
                    old_values={'status': old_status},
                    new_values={'status': AccountChangeRequest.STATUS_APPROVED},
                    notes=approval_notes,
                )
                
                logger.info(
                    f"Change request {change_request.id} approved by {approved_by.username}"
                )
                
                return change_request
        
        except Exception as e:
            logger.error(f"Error approving change request: {str(e)}")
            raise

    @staticmethod
    def reject_change(change_request, rejected_by, rejection_reason=None):
        """
        Reject a change request.
        
        Args:
            change_request: AccountChangeRequest instance
            rejected_by: User rejecting the change
            rejection_reason: Reason for rejection
        
        Returns:
            Updated AccountChangeRequest
        """
        try:
            with transaction.atomic():
                old_status = change_request.status
                
                change_request.status = AccountChangeRequest.STATUS_REJECTED
                change_request.system_owner = rejected_by
                if rejection_reason:
                    change_request.system_owner_approval_notes = rejection_reason
                change_request.save()
                
                # Log the rejection
                log_change_action(
                    change_request,
                    'rejected',
                    rejected_by,
                    old_values={'status': old_status},
                    new_values={'status': AccountChangeRequest.STATUS_REJECTED},
                    notes=rejection_reason,
                )
                
                logger.info(
                    f"Change request {change_request.id} rejected by {rejected_by.username}"
                )
                
                return change_request
        
        except Exception as e:
            logger.error(f"Error rejecting change request: {str(e)}")
            raise

    @staticmethod
    def complete_change(change_request, completed_by=None, completion_notes=None):
        """
        Mark a change as completed in the external system.
        
        Args:
            change_request: AccountChangeRequest instance
            completed_by: Optional user marking as completed
            completion_notes: Optional completion notes
        
        Returns:
            Updated AccountChangeRequest
        """
        try:
            with transaction.atomic():
                old_status = change_request.status
                
                change_request.status = AccountChangeRequest.STATUS_COMPLETED
                change_request.completed_in_external_system = True
                change_request.completed_date = timezone.now()
                if completion_notes:
                    change_request.system_owner_approval_notes = completion_notes
                change_request.save()
                
                # Log the completion
                log_change_action(
                    change_request,
                    'completed',
                    completed_by,
                    old_values={'status': old_status},
                    new_values={'status': AccountChangeRequest.STATUS_COMPLETED},
                    notes=completion_notes,
                )
                
                logger.info(
                    f"Change request {change_request.id} marked as completed"
                )
                
                return change_request
        
        except Exception as e:
            logger.error(f"Error completing change request: {str(e)}")
            raise

    @staticmethod
    def get_pending_approvals():
        """Get all pending change requests needing approval."""
        return AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_PENDING,
            system_owner_approved=False
        ).select_related('user', 'system', 'requested_by')

    @staticmethod
    def get_pending_completion():
        """Get all approved changes pending completion in external system."""
        return AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_APPROVED,
            completed_in_external_system=False
        ).select_related('user', 'system')

    @staticmethod
    def get_changes_by_system(system_id):
        """Get all changes for a specific system."""
        return AccountChangeRequest.objects.filter(
            system_id=system_id
        ).select_related('user', 'requested_by', 'system_owner')

    @staticmethod
    def get_changes_by_user(user_id):
        """Get all changes affecting a specific user."""
        return AccountChangeRequest.objects.filter(
            user_id=user_id
        ).select_related('system', 'requested_by', 'system_owner')

    @staticmethod
    def get_overdue_approvals(days=7):
        """Get pending changes not approved within the specified days."""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        
        return AccountChangeRequest.objects.filter(
            status=AccountChangeRequest.STATUS_PENDING,
            created_at__lt=cutoff_date
        ).select_related('user', 'system', 'requested_by')


class ChangeNotificationManager:
    """Manage notifications for change management events."""
    
    @staticmethod
    def notify_approval_required(change_request):
        """
        Notify system owner that approval is required.
        
        Args:
            change_request: AccountChangeRequest instance
        """
        try:
            if change_request.system_owner:
                # Could integrate with email/notification system
                logger.info(
                    f"Notification: Change {change_request.id} requires approval "
                    f"from {change_request.system_owner.email}"
                )
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")

    @staticmethod
    def notify_change_approved(change_request):
        """
        Notify requester that change is approved.
        
        Args:
            change_request: AccountChangeRequest instance
        """
        try:
            if change_request.requested_by:
                logger.info(
                    f"Notification: Change {change_request.id} approved, "
                    f"notifying {change_request.requested_by.email}"
                )
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")

    @staticmethod
    def notify_change_completed(change_request):
        """
        Notify all stakeholders that change is completed.
        
        Args:
            change_request: AccountChangeRequest instance
        """
        try:
            logger.info(
                f"Notification: Change {change_request.id} completed in {change_request.system.name}"
            )
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")


class ChangeIntegrationHelper:
    """Integration helpers for connecting change management with other systems."""
    
    @staticmethod
    def trigger_on_access_approved(access_record):
        """
        Trigger when user system access is approved.
        
        Args:
            access_record: UserSystemAccess instance
        """
        try:
            # Check if change request exists
            existing = AccountChangeRequest.objects.filter(
                user=access_record.user,
                system=access_record.system,
                status__in=[
                    AccountChangeRequest.STATUS_PENDING,
                    AccountChangeRequest.STATUS_APPROVED
                ]
            ).first()
            
            if not existing:
                # Create change request for the access grant
                ChangeRequestWorkflow.create_account_change(
                    change_type=AccountChangeRequest.CHANGE_TYPE_CREATE,
                    system=access_record.system,
                    user=access_record.user,
                    requested_by=access_record.requested_by,
                    business_justification=f"Access approval: {access_record.access_type} to {access_record.system.name}",
                )
                
                logger.info(
                    f"Created change request for access approval: "
                    f"{access_record.user.username} -> {access_record.system.name}"
                )
        
        except Exception as e:
            logger.error(f"Error in trigger_on_access_approved: {str(e)}")

    @staticmethod
    def sync_with_external_system(change_request, system_config):
        """
        Sync a change request with external system (ITSM, etc).
        
        Args:
            change_request: AccountChangeRequest instance
            system_config: External system configuration
        """
        try:
            # This would integrate with external ITSM systems
            logger.info(
                f"Syncing change request {change_request.id} with external system: "
                f"{system_config.get('name', 'Unknown')}"
            )
        except Exception as e:
            logger.error(f"Error syncing with external system: {str(e)}")

    @staticmethod
    def export_change_to_api(change_request, api_endpoint):
        """
        Export change request to external API.
        
        Args:
            change_request: AccountChangeRequest instance
            api_endpoint: URL of the API endpoint
        """
        try:
            logger.info(
                f"Exporting change request {change_request.id} to API endpoint: {api_endpoint}"
            )
        except Exception as e:
            logger.error(f"Error exporting to API: {str(e)}")

"""
Audit logging for change management operations.

Tracks all change request actions for compliance and audit purposes.
"""

import json
from django.utils import timezone
from django.db import models

import logging

logger = logging.getLogger(__name__)


# Note: ChangeAuditLog model is defined in models.py to avoid circular imports


def log_change_action(
    change_request,
    action,
    performed_by,
    old_values=None,
    new_values=None,
    notes=None,
    ip_address=None,
    user_agent=None,
):
    """
    Create an audit log entry for a change request action.
    
    Args:
        change_request: The AccountChangeRequest instance
        action: Action type (created, approved, rejected, completed, modified, viewed, exported)
        performed_by: The user who performed the action
        old_values: Dict of old field values (for modifications)
        new_values: Dict of new field values (for modifications)
        notes: Optional notes about the action
        ip_address: Optional client IP address
        user_agent: Optional user-agent string
    """
    try:
        from .models import ChangeAuditLog
        
        ChangeAuditLog.objects.create(
            change_request=change_request,
            action=action,
            performed_by=performed_by,
            old_values=old_values or {},
            new_values=new_values or {},
            notes=notes,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        logger.info(
            f"Audit log created: {change_request.id} - {action} by {performed_by}"
        )
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")


def get_change_audit_trail(change_request_id, limit=None):
    """
    Get the complete audit trail for a change request.
    
    Args:
        change_request_id: The change request ID
        limit: Maximum number of entries to return (None for all)
    
    Returns:
        QuerySet of ChangeAuditLog entries
    """
    from .models import ChangeAuditLog
    
    queryset = ChangeAuditLog.objects.filter(
        change_request_id=change_request_id
    ).select_related('performed_by')
    
    if limit:
        queryset = queryset[:limit]
    
    return queryset


def get_user_change_history(user_id, limit=50):
    """
    Get all changes performed by a specific user.
    
    Args:
        user_id: The user ID
        limit: Maximum number of entries to return
    
    Returns:
        QuerySet of ChangeAuditLog entries
    """
    from .models import ChangeAuditLog
    
    return ChangeAuditLog.objects.filter(
        performed_by_id=user_id
    ).select_related('change_request').order_by('-timestamp')[:limit]


def export_audit_logs(start_date=None, end_date=None, action_filter=None):
    """
    Export audit logs for compliance reporting.
    
    Args:
        start_date: Start date for filtering
        end_date: End date for filtering
        action_filter: Specific action to filter by
    
    Returns:
        QuerySet of audit logs matching criteria
    """
    from .models import ChangeAuditLog
    
    queryset = ChangeAuditLog.objects.all()
    
    if start_date:
        queryset = queryset.filter(timestamp__gte=start_date)
    
    if end_date:
        queryset = queryset.filter(timestamp__lte=end_date)
    
    if action_filter:
        queryset = queryset.filter(action=action_filter)
    
    return queryset.select_related('change_request', 'performed_by')

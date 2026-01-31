"""
Celery tasks for access management automation: review scheduling, audit verification, escalation, retention.
"""

from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging

from .models import (
    UserSystemAccess, AccessReviewSchedule, AuditEventLog, 
    ApprovalWorkflow, Attestation
)

logger = logging.getLogger(__name__)


@shared_task(name='access_management.check_review_schedules')
def check_review_schedules():
    """
    Hourly task: Check if reviews are due or overdue; send reminders/escalations.
    """
    now = timezone.now()
    
    # Find reviews due within 14 days
    due_soon = AccessReviewSchedule.objects.filter(
        next_review_date__lte=now + timedelta(days=14),
        next_review_date__gt=now,
        review_completed=False
    )
    
    for schedule in due_soon:
        try:
            # Send reminder email to reviewer
            reviewer = schedule.reviewed_by or schedule.user_system_access.approved_by
            if reviewer and reviewer.email:
                send_mail(
                    subject=f'Access Review Due Soon: {schedule.user_system_access.user.full_name}',
                    message=f'Please review access for {schedule.user_system_access.user.full_name} '
                            f'on {schedule.user_system_access.system.name}. Due: {schedule.next_review_date}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[reviewer.email],
                    fail_silently=True
                )
            logger.info(f"Sent reminder for review schedule {schedule.pk}")
        except Exception as e:
            logger.error(f"Error sending review reminder {schedule.pk}: {e}")
    
    # Find overdue reviews (> 180 days without review)
    overdue = AccessReviewSchedule.objects.filter(
        next_review_date__lt=now,
        review_completed=False,
        is_escalated=False
    )
    
    for schedule in overdue:
        try:
            # Mark as escalated and notify security team
            schedule.is_escalated = True
            schedule.escalated_to = 'security-team'
            schedule.escalation_date = now
            schedule.save()
            
            # Send escalation email
            security_email = getattr(settings, 'SECURITY_TEAM_EMAIL', 'security@company.com')
            send_mail(
                subject=f'ESCALATED: Overdue Access Review - {schedule.user_system_access.user.full_name}',
                message=f'Access review overdue for {schedule.user_system_access.user.full_name} '
                        f'on {schedule.user_system_access.system.name}. Overdue since: {schedule.next_review_date}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[security_email],
                fail_silently=True
            )
            logger.warning(f"Escalated overdue review {schedule.pk}")
        except Exception as e:
            logger.error(f"Error escalating review {schedule.pk}: {e}")


@shared_task(name='access_management.verify_audit_chain')
def verify_audit_chain():
    """
    Daily task: Verify integrity of audit event log chain; alert if tampering detected.
    """
    events = AuditEventLog.objects.all().order_by('created_at')
    
    tampered = []
    for event in events:
        if not event.verify_integrity():
            tampered.append(event.pk)
            logger.error(f"Audit event {event.pk} integrity check FAILED")
    
    if tampered:
        # Alert security team
        security_email = getattr(settings, 'SECURITY_TEAM_EMAIL', 'security@company.com')
        send_mail(
            subject='ALERT: Audit Log Tampering Detected',
            message=f'Audit chain integrity check failed for events: {tampered}. '
                    f'Immediate investigation required.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[security_email],
            fail_silently=True
        )
        logger.critical(f"Audit chain tampering detected: {tampered}")
    else:
        logger.info("Audit chain verification successful")


@shared_task(name='access_management.auto_revoke_overdue_reviews')
def auto_revoke_overdue_reviews():
    """
    Daily task: Auto-revoke access that has been unreviewed for 180+ days.
    """
    now = timezone.now()
    revoke_threshold = now - timedelta(days=180)
    
    to_revoke = UserSystemAccess.objects.filter(
        status='Active',
        last_review_date__lt=revoke_threshold
    )
    
    for access in to_revoke:
        try:
            access.revoke_access(reason='Auto-revoked: No review in 180+ days')
            
            # Log to audit
            AuditEventLog.objects.create(
                event_type='AccessAutoRevoked',
                event_data={'access_id': access.pk, 'reason': 'No review in 180+ days'},
                created_by=None
            )
            
            logger.warning(f"Auto-revoked access {access.pk}")
        except Exception as e:
            logger.error(f"Error auto-revoking access {access.pk}: {e}")


@shared_task(name='access_management.escalate_pending_approvals')
def escalate_pending_approvals():
    """
    Hourly task: Escalate approval workflows pending > 24 hours.
    """
    now = timezone.now()
    escalate_threshold = now - timedelta(hours=24)
    
    pending = ApprovalWorkflow.objects.filter(
        status='In Progress',
        created_at__lt=escalate_threshold,
        is_escalated=False
    )
    
    for workflow in pending:
        try:
            workflow.is_escalated = True
            workflow.escalation_date = now
            workflow.save()
            
            # Notify escalation recipients
            approver_email = getattr(settings, 'APPROVAL_ESCALATION_EMAIL', 'approvals@company.com')
            send_mail(
                subject=f'ESCALATED: Approval Pending > 24h - {workflow.user_system_access.user.full_name}',
                message=f'Access approval pending for {workflow.user_system_access.user.full_name} '
                        f'on {workflow.user_system_access.system.name}. Pending since: {workflow.created_at}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[approver_email],
                fail_silently=True
            )
            logger.warning(f"Escalated pending approval {workflow.pk}")
        except Exception as e:
            logger.error(f"Error escalating approval {workflow.pk}: {e}")


@shared_task(name='access_management.check_retention_policies')
def check_retention_policies():
    """
    Weekly task: Check soft-deleted records for retention policy enforcement; purge if eligible.
    """
    now = timezone.now()
    
    # Find soft-deleted records past retention window (e.g., 90 days)
    retention_days = getattr(settings, 'SOFT_DELETE_RETENTION_DAYS', 90)
    retention_cutoff = now - timedelta(days=retention_days)
    
    to_purge = UserSystemAccess.objects.filter(
        is_deleted=True,
        deleted_date__lt=retention_cutoff
    )
    
    count = 0
    for access in to_purge:
        try:
            # Log purge to audit before deletion
            AuditEventLog.objects.create(
                event_type='AccessPurged',
                event_data={'access_id': access.pk, 'reason': 'Retention policy enforcement'},
                created_by=None
            )
            # Physical delete
            access.delete()
            count += 1
            logger.info(f"Purged soft-deleted access {access.pk}")
        except Exception as e:
            logger.error(f"Error purging access {access.pk}: {e}")
    
    logger.info(f"Retention policy check: purged {count} records")

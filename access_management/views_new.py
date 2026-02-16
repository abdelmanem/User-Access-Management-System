"""
Additional views for new IAM workflows: Approval routing, Evidence upload, Attestation.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
import json

from .models import (
    UserSystemAccess, ApprovalWorkflow, Approval, ApprovalStep,
    EvidenceArtifact, Attestation, AuditEventLog, AccessHistory
)
from .risk import RiskScorer
from .forms_new import (
    ApprovalForm, EvidenceArtifactForm, AttestationForm,
    AccessApproveForm, RevokeAccessForm
)


@login_required
@permission_required('access_management.can_approve_access', raise_exception=True)
def approval_dashboard(request):
    """Dashboard showing pending approvals for the current user (both Change Management and Access Management)."""
    
    from change_management.models import AccountChangeRequest
    from django.db.models import Q
    
    my_approvals = []
    
    # 1. CHANGE MANAGEMENT APPROVALS
    # Get pending change requests where user is a system owner or IT approver
    pending_change_requests = AccountChangeRequest.objects.filter(
        status='Pending'
    ).select_related('user', 'system', 'system_owner', 'it_approval', 'requested_by')
    
    # Filter based on user role
    if request.user.is_superuser or request.user.is_staff:
        # Superusers/staff can see all pending change requests
        pass
    else:
        # Regular users can see if:
        # - They are the system owner
        # - They are the IT approver
        pending_change_requests = pending_change_requests.filter(
            Q(system_owner=request.user) |
            Q(it_approval=request.user)
        )
    
    # Add change requests to approvals list
    for change_req in pending_change_requests:
        can_edit_owner_section = (
            request.user.is_superuser
            or request.user.is_staff
            or (change_req.system_owner and change_req.system_owner_id == request.user.id)
        )
        can_edit_it_section = (
            request.user.is_superuser
            or request.user.is_staff
            or request.user.is_it_admin
            or (change_req.it_approval and change_req.it_approval_id == request.user.id)
        )

        my_approvals.append({
            'type': 'change_request',
            'item': change_req,
            'workflow': None,
            'step': None,
            'access': None,
            'created_at': change_req.created_at,
            'can_edit_owner_section': can_edit_owner_section,
            'can_edit_it_section': can_edit_it_section,
        })
    
    # 2. Workflow-based approvals (Access Management)
    pending_workflows = ApprovalWorkflow.objects.filter(
        status__in=['Pending', 'In Progress']
    ).select_related('user_system_access__user', 'user_system_access__system')
    
    for workflow in pending_workflows:
        for step in workflow.steps.all():
            if step.approver == request.user:
                my_approvals.append({
                    'type': 'workflow_access',
                    'item': workflow.user_system_access,
                    'workflow': workflow,
                    'step': step,
                    'access': workflow.user_system_access,
                    'created_at': workflow.created_at,
                })
    
    # 3. Simple pending access assignments (non-workflow)
    from systems.models import System
    
    # Get pending assignments where user can approve
    pending_assignments = UserSystemAccess.objects.filter(
        status='Pending'
    ).select_related('user', 'system', 'system__system_owner')
    
    # Filter based on user permissions and assignments
    if request.user.is_superuser or request.user.is_staff:
        # Superusers/staff can approve any pending assignment
        pass  # Include all pending assignments
    else:
        # Regular users can approve if:
        # - They are set as the approver (approved_by field)
        # - They are the system owner
        # - No specific approver is set (approved_by is null - general approval needed)
        pending_assignments = pending_assignments.filter(
            Q(approved_by=request.user) |
            Q(approved_by__isnull=True) |
            Q(system__system_owner=request.user)
        )
    
    # Add simple pending assignments to approvals list
    for assignment in pending_assignments:
        # Skip if already in workflow approvals
        if not any(a.get('access') and a['access'].id == assignment.id for a in my_approvals):
            is_system_owner = (
                request.user.is_superuser
                or request.user.is_staff
                or (assignment.system and getattr(assignment.system, 'system_owner_id', None) == request.user.id)
            )
            is_it_approver = (
                request.user.is_superuser
                or request.user.is_staff
                or request.user.is_it_admin
            )
            my_approvals.append({
                'type': 'direct_access',
                'item': assignment,
                'workflow': None,
                'step': None,
                'access': assignment,
                'created_at': assignment.request_date,
                'can_edit_owner_section': is_system_owner,
                'can_edit_it_section': is_it_approver,
            })
    
    # Sort by created_at descending (most recent first)
    my_approvals.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render(request, 'access_management/approval_dashboard.html', {
        'approvals': my_approvals,
        'count': len(my_approvals)
    })


@login_required
@permission_required('access_management.can_approve_access', raise_exception=True)
def approve_access_request(request, workflow_id, step_id):
    """Approve or reject a specific access request step."""
    
    workflow = get_object_or_404(ApprovalWorkflow, pk=workflow_id)
    step = get_object_or_404(ApprovalStep, pk=step_id, workflow=workflow)
    
    # Check if current user is assigned to this step
    if step.approver != request.user:
        return HttpResponseForbidden('You are not assigned to this approval step.')
    
    if request.method == 'POST':
        form = ApprovalForm(request.POST, instance=step, workflow=workflow)
        if form.is_valid():
            approval = form.save(commit=False)
            approval.approver = request.user
            approval.save()
            
            # Log to audit
            AuditEventLog.objects.create(
                event_type='AccessApprovalStep',
                event_data={
                    'workflow_id': workflow.pk,
                    'step_number': step.step_number,
                    'approved': approval.approved,
                    'approver': request.user.pk
                },
                created_by=request.user
            )
            
            # Check if all steps approved
            all_approvals = Approval.objects.filter(step__workflow=workflow)
            if all_approvals.count() == step.step_number:
                # All steps completed
                if all(a.approved for a in all_approvals):
                    workflow.status = 'Completed'
                    workflow.user_system_access.activate_access()
                    messages.success(request, 'Access request approved and activated!')
                else:
                    workflow.status = 'Rejected'
                    workflow.user_system_access.reject_access(request.user, 'Rejected by approver')
                    messages.warning(request, 'Access request rejected.')
                workflow.save()
            
            return redirect('approval_dashboard')
    else:
        form = ApprovalForm(instance=step, workflow=workflow)
    
    return render(request, 'access_management/approve_access_request.html', {
        'form': form,
        'workflow': workflow,
        'step': step,
        'access': workflow.user_system_access
    })


@login_required
@permission_required('access_management.can_upload_evidence', raise_exception=True)
def upload_evidence(request, access_id):
    """Upload evidence (screenshots, documents) for an access assignment."""
    
    access = get_object_or_404(UserSystemAccess, pk=access_id)
    
    if request.method == 'POST':
        form = EvidenceArtifactForm(request.POST, request.FILES)
        if form.is_valid():
            artifact = form.save(commit=False)
            artifact.user_system_access = access
            artifact.created_by = request.user
            artifact.save()
            
            messages.success(request, f'Evidence uploaded: {artifact.artifact_type}')
            
            # Log to audit
            AuditEventLog.objects.create(
                event_type='EvidenceUploaded',
                event_data={
                    'access_id': access.pk,
                    'artifact_type': artifact.artifact_type,
                    'artifact_id': artifact.pk
                },
                created_by=request.user
            )
            
            return redirect('access_management:access_assignment_detail', pk=access_id)
    else:
        form = EvidenceArtifactForm()
    
    return render(request, 'access_management/upload_evidence.html', {
        'form': form,
        'access': access
    })


@login_required
def attest_access(request, access_id):
    """Create formal attestation for an access assignment."""
    
    access = get_object_or_404(UserSystemAccess, pk=access_id)
    
    # Allow the owner, staff/superusers, or users with explicit permission
    if not (
        access.user == request.user
        or request.user.is_staff
        or request.user.is_superuser
        or request.user.has_perm('access_management.can_attest_any')
    ):
        return HttpResponseForbidden('You can only attest for your own access.')
    
    # Build standard attestation statement
    statement = f"""I hereby attest that:
1. I have received access to {access.system.name} with {access.access_type} permission level.
2. The access is necessary for my business role and responsibilities.
3. I have read and understand the security requirements and compliance obligations.
4. I will use this access responsibly and only for authorized business purposes.
5. I understand that unauthorized use may result in disciplinary action.
"""
    
    if request.method == 'POST':
        form = AttestationForm(request.POST, statement_text=statement)
        if form.is_valid():
            attestation = form.save(commit=False)
            attestation.user_system_access = access
            attestation.attested_by = request.user
            attestation.ip_address = get_client_ip(request)
            attestation.user_agent = request.META.get('HTTP_USER_AGENT', '')
            attestation.statement = statement
            attestation.save()
            
            # Finalize with signing key if available
            from django.conf import settings
            signing_key = getattr(settings, 'ATTESTATION_SIGNING_KEY', None)
            if signing_key:
                attestation.finalize(signing_key=signing_key)
            
            messages.success(request, 'Attestation recorded successfully.')
            
            # Log to audit
            AuditEventLog.objects.create(
                event_type='AccessAttested',
                event_data={
                    'access_id': access.pk,
                    'attested_by': request.user.pk,
                    'attestation_id': attestation.pk
                },
                created_by=request.user
            )
            
            return redirect('access_management:access_assignment_detail', pk=access_id)
    else:
        form = AttestationForm(statement_text=statement)
    
    return render(request, 'access_management/attest_access.html', {
        'form': form,
        'access': access,
        'statement': statement
    })


@login_required
@require_http_methods(['POST'])
def revoke_access_view(request, access_id):
    """Revoke an access assignment with audit trail."""
    
    access = get_object_or_404(UserSystemAccess, pk=access_id)
    
    form = RevokeAccessForm(request.POST)
    if form.is_valid():
        reason = f"{form.cleaned_data['reason']}: {form.cleaned_data['details']}"
        
        try:
            # Soft-delete or revoke
            access.revoke_access(reason=reason)
            
            # Log to audit
            AuditEventLog.objects.create(
                event_type='AccessRevoked',
                event_data={
                    'access_id': access.pk,
                    'revoked_by': request.user.pk,
                    'reason': reason,
                    'verified': form.cleaned_data.get('verified_removal', False)
                },
                created_by=request.user
            )
            
            # Create access history entry
            AccessHistory.objects.create(
                user=access.user,
                system=access.system,
                user_system_access=access,
                action='Revoked',
                action_description=f"Access revoked: {reason}",
                success=True,
                created_by=request.user
            )
            
            messages.success(request, f'Access revoked for {access.user.full_name}')
            return redirect('access_management:access_assignment_list')
        except Exception as e:
            messages.error(request, f'Failed to revoke access: {str(e)}')
            return redirect('access_management:access_assignment_detail', pk=access_id)
    
    return render(request, 'access_management/revoke_confirm.html', {
        'form': form,
        'access': access
    })


@login_required
def revoke_access_confirm(request, access_id):
    """Show a confirmation page before revoking an access assignment."""

    access = get_object_or_404(UserSystemAccess, pk=access_id)

    # Check if access can be revoked
    if access.status not in ['Active', 'Suspended', 'Approved']:
        messages.error(request, f'Cannot revoke access with status: {access.status}')
        return redirect('access_management:access_assignment_detail', pk=access_id)

    # Permission: owner, staff/superuser, or has revoke permission
    if not (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.has_perm('access_management.can_revoke_any')
        or access.user == request.user
    ):
        return HttpResponseForbidden('You do not have permission to revoke this access.')

    form = RevokeAccessForm()
    return render(request, 'access_management/revoke_confirm.html', {
        'form': form,
        'access': access
    })


@login_required
def activate_access_confirm(request, access_id):
    """Show a confirmation page before activating a revoked access assignment."""

    access = get_object_or_404(UserSystemAccess, pk=access_id)

    # Only allow activation when status is Revoked
    if access.status != 'Revoked':
        messages.error(request, f'Cannot activate access with status: {access.status}')
        return redirect('access_management:access_assignment_detail', pk=access_id)

    # Permission: staff/superuser or explicit activate permission
    if not (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.has_perm('access_management.activate_access')
    ):
        return HttpResponseForbidden('You do not have permission to activate this access.')

    return render(request, 'access_management/activate_confirm.html', {
        'access': access
    })


@login_required
@require_http_methods(['POST'])
def activate_access_view(request, access_id):
    """Activate a revoked access assignment by resetting to Pending for re-approval."""

    access = get_object_or_404(UserSystemAccess, pk=access_id)

    if access.status != 'Revoked':
        messages.error(request, f'Cannot reactivate access with status: {access.status}')
        return redirect('access_management:access_assignment_detail', pk=access_id)

    if not (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.has_perm('access_management.activate_access')
    ):
        return HttpResponseForbidden('You do not have permission to reactivate this access.')

    try:
        # Reset to Pending status to require approval again
        now = timezone.now()
        original_status = access.status
        access.status = 'Pending'
        access.status_changed_by = request.user
        access.status_changed_at = now
        access.lifecycle_timeline = (access.lifecycle_timeline or []) + [{
            'from': original_status,
            'to': 'Pending',
            'by': request.user.pk if request.user else None,
            'at': now.isoformat(),
            'reason': 'Reactivation requested - requires approval'
        }]
        access.save()

        # Log to audit
        try:
            AuditEventLog.objects.create(
                event_type='AccessReactivationRequested',
                event_data={'access_id': access.pk, 'requested_by': request.user.pk},
                created_by=request.user
            )
        except Exception:
            pass

        # Create access history entry
        AccessHistory.objects.create(
            user=access.user,
            system=access.system,
            user_system_access=access,
            action='ReactivationRequested',
            action_description=f"Reactivation requested by {request.user.get_full_name()} - awaiting approval",
            success=True,
            created_by=request.user
        )

        messages.success(request, f'Reactivation requested for {access.user.full_name}. This request is now pending approval.')
        return redirect('access_management:access_assignment_detail', pk=access_id)
    except Exception as e:
        messages.error(request, f'Failed to request reactivation: {str(e)}')
        return redirect('access_management:access_assignment_detail', pk=access_id)


@login_required
def evidence_gallery(request, access_id):
    """Display all evidence artifacts for an access assignment."""
    
    access = get_object_or_404(UserSystemAccess, pk=access_id)
    artifacts = access.evidence_artifacts.all().order_by('-created_at')
    
    return render(request, 'access_management/evidence_gallery.html', {
        'access': access,
        'artifacts': artifacts
    })


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

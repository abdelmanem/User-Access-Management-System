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
    EvidenceArtifact, Attestation, AuditEventLog
)
from .risk import RiskScorer
from .forms_new import (
    ApprovalForm, EvidenceArtifactForm, AttestationForm,
    AccessApproveForm, RevokeAccessForm
)


@login_required
@permission_required('access_management.can_approve_access', raise_exception=True)
def approval_dashboard(request):
    """Dashboard showing pending approvals for the current user."""
    
    pending_workflows = ApprovalWorkflow.objects.filter(
        status__in=['Pending', 'In Progress']
    ).select_related('user_system_access__user', 'user_system_access__system')
    
    # Filter to only those assigned to current user
    my_approvals = []
    for workflow in pending_workflows:
        for step in workflow.steps.all():
            if step.approver == request.user:
                my_approvals.append({
                    'workflow': workflow,
                    'step': step,
                    'access': workflow.user_system_access
                })
    
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
        
        messages.success(request, f'Access revoked for {access.user.full_name}')
        return redirect('access_assignment_list')
    
    return render(request, 'access_management/revoke_access.html', {
        'form': form,
        'access': access
    })


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

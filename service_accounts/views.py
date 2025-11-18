from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta
from io import BytesIO
from openpyxl import Workbook

from django import forms
from .models import (
    ServiceAccount,
    ServiceAccountPasswordHistory,
    ServiceAccountAttestation,
)
from .forms import (
    ServiceAccountForm,
    ServiceAccountPasswordHistoryForm,
    ServiceAccountAttestationForm,
)
from systems.models import System
from accounts.models import CustomUser


@login_required
def service_account_list(request):
    """List all service accounts with filtering and search"""
    service_accounts = ServiceAccount.objects.select_related(
        'system',
        'owner',
        'password_policy_verified_by',
        'admin_user',
        'last_attested_by',
    ).all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        service_accounts = service_accounts.filter(
            Q(account_name__icontains=search_query) |
            Q(system__name__icontains=search_query) |
            Q(purpose__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Filter by system
    system_filter = request.GET.get('system', '')
    if system_filter:
        service_accounts = service_accounts.filter(system_id=system_filter)
    
    # Filter by account type
    account_type_filter = request.GET.get('account_type', '')
    if account_type_filter:
        service_accounts = service_accounts.filter(account_type=account_type_filter)
    
    # Filter by compliance status
    compliance_filter = request.GET.get('compliance', '')
    if compliance_filter == 'compliant':
        service_accounts = service_accounts.filter(
            password_complies_with_policy=True,
            password_policy_verified_date__isnull=False
        )
    elif compliance_filter == 'non_compliant':
        service_accounts = service_accounts.filter(
            Q(password_complies_with_policy=False) |
            Q(password_policy_verified_date__isnull=True)
        )
    elif compliance_filter == 'expired':
        service_accounts = service_accounts.filter(
            password_expires_on__lt=timezone.now()
        )
    elif compliance_filter == 'expiring_soon':
        thirty_days = timezone.now() + timedelta(days=30)
        service_accounts = service_accounts.filter(
            password_expires_on__lte=thirty_days,
            password_expires_on__gt=timezone.now()
        )
    
    # Governance filter (attestation/privileged)
    governance_filter = request.GET.get('governance', '')
    if governance_filter == 'privileged':
        service_accounts = service_accounts.filter(is_privileged=True)
    elif governance_filter == 'attestation_overdue':
        ninety_days_ago = timezone.now() - timedelta(days=90)
        service_accounts = service_accounts.filter(
            Q(last_attested_at__lt=ninety_days_ago) | Q(last_attested_at__isnull=True),
            is_active=True,
        )
    elif governance_filter == 'missing_change_refs':
        service_accounts = service_accounts.filter(
            Q(change_request_id__exact='') |
            Q(sop_reference__exact='') |
            Q(password_storage_location__exact='')
        )

    # Filter by active status
    active_filter = request.GET.get('active', '')
    if active_filter == 'true':
        service_accounts = service_accounts.filter(is_active=True)
    elif active_filter == 'false':
        service_accounts = service_accounts.filter(is_active=False)
    
    # Ordering
    ordering = request.GET.get('ordering', '-created_at')
    service_accounts = service_accounts.order_by(ordering)
    
    # Pagination
    paginator = Paginator(service_accounts, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_qs = ServiceAccount.objects.all()
    total_count = total_qs.count()
    active_count = total_qs.filter(is_active=True).count()
    compliant_count = total_qs.filter(
        password_complies_with_policy=True,
        password_policy_verified_date__isnull=False
    ).count()
    expired_count = total_qs.filter(password_expires_on__lt=timezone.now()).count()
    privileged_count = total_qs.filter(is_privileged=True, is_active=True).count()
    attestation_overdue_count = total_qs.filter(
        Q(last_attested_at__isnull=True) |
        Q(last_attested_at__lt=timezone.now() - timedelta(days=90)),
        is_active=True,
    ).count()
    
    # Get all systems for filter dropdown
    systems = System.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'service_accounts': page_obj,
        'total_count': total_count,
        'active_count': active_count,
        'compliant_count': compliant_count,
        'expired_count': expired_count,
        'systems': systems,
        'search_query': search_query,
        'system_filter': system_filter,
        'account_type_filter': account_type_filter,
        'compliance_filter': compliance_filter,
        'active_filter': active_filter,
        'governance_filter': governance_filter,
        'ordering': ordering,
        'privileged_count': privileged_count,
        'attestation_overdue_count': attestation_overdue_count,
    }
    return render(request, 'service_accounts/service_account_list.html', context)


@login_required
def service_account_detail(request, pk):
    """View service account details"""
    service_account = get_object_or_404(
        ServiceAccount.objects.select_related(
            'system',
            'owner',
            'password_policy_verified_by',
            'created_by',
            'updated_by',
            'admin_user',
            'last_attested_by',
        ),
        pk=pk
    )
    
    # Get password history
    password_history = service_account.password_history.select_related('changed_by').order_by('-password_changed_date')[:10]
    
    attestations = service_account.attestations.select_related('attested_by').order_by('-attested_at')[:10]

    context = {
        'service_account': service_account,
        'password_history': password_history,
        'attestations': attestations,
        'attestation_form': ServiceAccountAttestationForm(),
    }
    return render(request, 'service_accounts/service_account_detail.html', context)


@login_required
def service_account_create(request):
    """Create a new service account"""
    if request.method == 'POST':
        form = ServiceAccountForm(request.POST)
        if form.is_valid():
            service_account = form.save(commit=False)
            service_account.created_by = request.user
            service_account.updated_by = request.user
            service_account.save()
            messages.success(request, f'Service account "{service_account.account_name}" created successfully.')
            return redirect('service_accounts:service_account_detail', pk=service_account.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceAccountForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    return render(request, 'service_accounts/service_account_form.html', context)


@login_required
def service_account_update(request, pk):
    """Update an existing service account"""
    service_account = get_object_or_404(ServiceAccount, pk=pk)
    
    if request.method == 'POST':
        form = ServiceAccountForm(request.POST, instance=service_account)
        if form.is_valid():
            service_account = form.save(commit=False)
            service_account.updated_by = request.user
            service_account.save()
            messages.success(request, f'Service account "{service_account.account_name}" updated successfully.')
            return redirect('service_accounts:service_account_detail', pk=service_account.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceAccountForm(instance=service_account)
    
    context = {
        'form': form,
        'service_account': service_account,
        'action': 'Update',
    }
    return render(request, 'service_accounts/service_account_form.html', context)


@login_required
def service_account_delete(request, pk):
    """Delete a service account"""
    service_account = get_object_or_404(ServiceAccount, pk=pk)
    
    if request.method == 'POST':
        account_name = service_account.account_name
        service_account.delete()
        messages.success(request, f'Service account "{account_name}" deleted successfully.')
        return redirect('service_accounts:service_account_list')
    
    context = {
        'service_account': service_account,
    }
    return render(request, 'service_accounts/service_account_confirm_delete.html', context)


@login_required
def service_account_password_history_add(request, pk):
    """Add a password change record to service account history"""
    service_account = get_object_or_404(ServiceAccount, pk=pk)
    
    if request.method == 'POST':
        form = ServiceAccountPasswordHistoryForm(request.POST)
        if form.is_valid():
            password_history = form.save(commit=False, changed_by=request.user)
            password_history.service_account = service_account
            
            # Update service account password fields
            service_account.password_last_changed = password_history.password_changed_date
            service_account.password_expires_on = password_history.expires_on
            service_account.password_complies_with_policy = password_history.complies_with_policy
            service_account.updated_by = request.user
            
            password_history.save()
            service_account.save()
            
            messages.success(request, 'Password change recorded successfully.')
            return redirect('service_accounts:service_account_detail', pk=service_account.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceAccountPasswordHistoryForm(initial={
            'service_account': service_account,
            'password_changed_date': timezone.now(),
        })
        form.fields['service_account'].widget = forms.HiddenInput()
    
    context = {
        'form': form,
        'service_account': service_account,
    }
    return render(request, 'service_accounts/service_account_password_history_form.html', context)


@login_required
def service_account_attest(request, pk):
    """Capture an attestation for a service/privileged account."""
    service_account = get_object_or_404(ServiceAccount, pk=pk)

    if request.method == 'POST':
        form = ServiceAccountAttestationForm(request.POST)
        if form.is_valid():
            attestation = form.save(commit=False)
            attestation.service_account = service_account
            attestation.attested_by = request.user
            attestation.save()

            service_account.last_attested_at = attestation.attested_at
            service_account.last_attested_by = request.user
            service_account.last_attestation_status = attestation.status
            service_account.last_attestation_notes = attestation.notes
            if attestation.storage_location:
                service_account.password_storage_location = attestation.storage_location
            service_account.updated_by = request.user
            service_account.save()

            messages.success(request, 'Attestation recorded successfully.')
            return redirect('service_accounts:service_account_detail', pk=pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = ServiceAccountAttestationForm(initial={
            'status': 'Confirmed',
            'storage_location': service_account.password_storage_location,
        })

    return render(request, 'service_accounts/service_account_attest.html', {
        'form': form,
        'service_account': service_account,
    })


@login_required
def service_account_compliance_report(request):
    """Generate compliance report for service accounts"""
    service_accounts = ServiceAccount.objects.select_related(
        'system',
        'owner',
        'password_policy_verified_by',
        'admin_user',
        'last_attested_by',
    ).all()
    
    # Statistics
    total = service_accounts.count()
    active = service_accounts.filter(is_active=True).count()
    compliant = service_accounts.filter(
        password_complies_with_policy=True,
        password_policy_verified_date__isnull=False
    ).count()
    non_compliant = total - compliant
    expired = service_accounts.filter(
        password_expires_on__lt=timezone.now()
    ).count()
    expiring_soon = service_accounts.filter(
        password_expires_on__lte=timezone.now() + timedelta(days=30),
        password_expires_on__gt=timezone.now()
    ).count()
    
    # Group by system
    by_system = service_accounts.values('system__name').annotate(
        count=Count('id'),
        compliant_count=Count('id', filter=Q(password_complies_with_policy=True, password_policy_verified_date__isnull=False))
    ).order_by('system__name')
    
    # Group by account type
    by_type = service_accounts.values('account_type').annotate(
        count=Count('id'),
        compliant_count=Count('id', filter=Q(password_complies_with_policy=True, password_policy_verified_date__isnull=False))
    ).order_by('account_type')
    
    context = {
        'service_accounts': service_accounts,
        'total': total,
        'active': active,
        'compliant': compliant,
        'non_compliant': non_compliant,
        'expired': expired,
        'expiring_soon': expiring_soon,
        'by_system': by_system,
        'by_type': by_type,
    }
    return render(request, 'service_accounts/service_account_compliance_report.html', context)


@login_required
def export_service_accounts_to_excel(request):
    """Export service accounts to Excel"""
    service_accounts = ServiceAccount.objects.select_related('system', 'owner', 'password_policy_verified_by').all()
    
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Service Accounts"
    
    headers = [
        "Account Name",
        "System",
        "Account Type",
        "Privileged",
        "Admin User",
        "Purpose",
        "Owner",
        "Password Last Changed",
        "Password Expires On",
        "Password Complies with Policy",
        "Policy Verified Date",
        "Policy Verified By",
        "Change Request ID",
        "SOP Reference",
        "Password Storage Location",
        "Last Attested",
        "Last Attestation Status",
        "Is Active",
        "Compliance Status",
        "Created At",
        "Updated At",
    ]
    worksheet.append(headers)
    
    for account in service_accounts:
        worksheet.append([
            account.account_name,
            account.system.name if account.system else '',
            account.get_account_type_display(),
            'Yes' if account.is_privileged else 'No',
            account.admin_user.full_name if account.admin_user else '',
            account.purpose,
            account.owner.full_name if account.owner else '',
            account.password_last_changed.strftime('%Y-%m-%d %H:%M') if account.password_last_changed else '',
            account.password_expires_on.strftime('%Y-%m-%d %H:%M') if account.password_expires_on else '',
            'Yes' if account.password_complies_with_policy else 'No',
            account.password_policy_verified_date.strftime('%Y-%m-%d %H:%M') if account.password_policy_verified_date else '',
            account.password_policy_verified_by.full_name if account.password_policy_verified_by else '',
            account.change_request_id,
            account.sop_reference,
            account.password_storage_location,
            account.last_attested_at.strftime('%Y-%m-%d %H:%M') if account.last_attested_at else '',
            account.last_attestation_status,
            'Yes' if account.is_active else 'No',
            account.compliance_status,
            account.created_at.strftime('%Y-%m-%d %H:%M'),
            account.updated_at.strftime('%Y-%m-%d %H:%M'),
        ])
    
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    
    response = HttpResponse(
        stream.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="service_accounts.xlsx"'
    return response

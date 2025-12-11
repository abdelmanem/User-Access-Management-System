from datetime import timedelta
from decimal import Decimal

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.http import HttpResponse
from datetime import date
import csv
from io import StringIO

from .models import System, SystemContract
from .forms import (
    SystemForm,
    SystemUserAssignForm,
    SystemHardwareAssignForm,
    SystemContractForm,
    SystemSubscriptionTierFormSet,
)
from access_management.models import UserSystemAccess
from accounts.models import CustomUser

@login_required
def system_list(request):
    systems = System.objects.all().annotate(user_count=Count('user_accesses', distinct=True))

    # Search and filters
    search_query = request.GET.get('q', '').strip()
    filter_system_type = request.GET.get('system_type', '').strip()
    filter_criticality = request.GET.get('criticality_level', '').strip()
    filter_status = request.GET.get('status', '').strip()

    if search_query:
        systems = systems.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(url__icontains=search_query) |
            Q(ip_address__icontains=search_query) |
            Q(server_name__icontains=search_query)
        )

    if filter_system_type:
        systems = systems.filter(system_type=filter_system_type)

    if filter_criticality:
        systems = systems.filter(criticality_level=filter_criticality)

    if filter_status:
        is_active_value = True if filter_status == 'active' else False
        systems = systems.filter(is_active=is_active_value)

    total_count = systems.count()
    active_count = systems.filter(is_active=True).count()
    inactive_count = total_count - active_count
    critical_count = systems.filter(criticality_level='Critical').count()
    context = {
        'systems': systems,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'critical_count': critical_count,
        'search_query': search_query,
        'filter_system_type': filter_system_type,
        'filter_criticality': filter_criticality,
        'filter_status': filter_status,
        'system_type_choices': System.SYSTEM_TYPE_CHOICES,
        'criticality_choices': System.CRITICALITY_LEVEL_CHOICES,
    }
    return render(request, 'systems/system_list.html', context)


@login_required
def system_type_management(request):
    """
    Simple management view for system types.
    Uses the static SYSTEM_TYPE_CHOICES defined on the System model and shows
    how many systems currently use each type, with quick links to filter.
    """
    type_stats = []
    for value, label in System.SYSTEM_TYPE_CHOICES:
        count = System.objects.filter(system_type=value).count()
        type_stats.append({
            "value": value,
            "label": label,
            "count": count,
        })

    context = {
        "type_stats": type_stats,
    }
    return render(request, "systems/system_type_management.html", context)

@login_required
def system_detail(request, pk):
    system = get_object_or_404(
        System.objects.prefetch_related('hardware_assets'),
        pk=pk
    )
    contract = getattr(system, 'contract', None)
    assignments = UserSystemAccess.objects.filter(system=system).select_related('user', 'approved_by').order_by(
        'user__first_name', 'user__last_name'
    )
    contract_form = SystemContractForm(instance=contract)

    if request.method == 'POST':
        # Check which form was submitted
        if 'manage_users' in request.POST:
            assign_form = SystemUserAssignForm(request.POST, system=system)
            hardware_form = SystemHardwareAssignForm(system=system)
            
            if assign_form.is_valid():
                selected_users = assign_form.cleaned_data['users']
                selected_ids = set(selected_users.values_list('id', flat=True))

                existing_assignments = UserSystemAccess.objects.filter(system=system)
                existing_ids = set(existing_assignments.values_list('user_id', flat=True))

                removed_queryset = existing_assignments.exclude(user_id__in=selected_ids)
                removed_count = removed_queryset.count()
                removed_queryset.delete()

                to_add_ids = selected_ids - existing_ids
                added_count = 0
                if to_add_ids:
                    bulk_users = CustomUser.objects.filter(id__in=to_add_ids)
                    now = timezone.now()
                    new_assignments = []
                    for user in bulk_users:
                        new_assignments.append(UserSystemAccess(
                            user=user,
                            system=system,
                            access_type='Read Only',
                            status='Approved',
                            request_type='New Access',
                            priority='Medium',
                            business_justification='Assigned via system management interface.',
                            requested_by=request.user if request.user.is_authenticated else None,
                            created_by=request.user if request.user.is_authenticated else None,
                            updated_by=request.user if request.user.is_authenticated else None,
                            approved_by=request.user if request.user.is_authenticated else None,
                            approval_date=now,
                            access_start_date=now,
                        ))
                    UserSystemAccess.objects.bulk_create(new_assignments)
                    added_count = len(new_assignments)

                messages.success(
                    request,
                    f"System user assignments updated. Added {added_count} user(s), removed {removed_count} user(s)."
                )
                return redirect('systems:system_detail', pk=system.pk)
            else:
                messages.error(request, 'Please correct the errors below.')
        
        elif 'manage_hardware' in request.POST:
            assign_form = SystemUserAssignForm(system=system)
            hardware_form = SystemHardwareAssignForm(request.POST, system=system)
            contract_form = SystemContractForm(instance=contract)
            
            if hardware_form.is_valid():
                selected_hardware = hardware_form.cleaned_data['hardware_assets']
                system.hardware_assets.set(selected_hardware)
                
                messages.success(
                    request,
                    f"Hardware assignments updated. {selected_hardware.count()} hardware asset(s) linked to this system."
                )
                return redirect('systems:system_detail', pk=system.pk)
            else:
                messages.error(request, 'Please correct the errors below.')
        elif 'manage_contract' in request.POST:
            assign_form = SystemUserAssignForm(system=system)
            hardware_form = SystemHardwareAssignForm(system=system)
            contract_form = SystemContractForm(request.POST, request.FILES, instance=contract)

            if contract_form.is_valid():
                contract_obj = contract_form.save(commit=False)
                contract_obj.system = system
                contract_obj.save()
                messages.success(request, 'Contract & renewal details saved.')
                return redirect('systems:system_detail', pk=system.pk)
            else:
                messages.error(request, 'Please correct the contract errors below.')
        else:
            assign_form = SystemUserAssignForm(system=system)
            hardware_form = SystemHardwareAssignForm(system=system)
            contract_form = SystemContractForm(instance=contract)
    else:
        assign_form = SystemUserAssignForm(system=system)
        hardware_form = SystemHardwareAssignForm(system=system)
        contract_form = SystemContractForm(instance=contract)

    context = {
        'system': system,
        'assign_form': assign_form,
        'hardware_form': hardware_form,
        'assignments': assignments,
        'contract': contract,
        'contract_form': contract_form,
    }
    return render(request, 'systems/system_detail.html', context)

@login_required
def system_create(request):
    if request.method == 'POST':
        form = SystemForm(request.POST)
        if form.is_valid():
            sys_obj = form.save(commit=False)
            sys_obj.created_by = request.user
            sys_obj.updated_by = request.user
            sys_obj.save()
            SystemContract.objects.get_or_create(system=sys_obj)
            messages.success(request, 'System created successfully.')
            return redirect('systems:system_detail', pk=sys_obj.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = SystemForm()
    return render(request, 'systems/system_form.html', {'form': form})

@login_required
def system_update(request, pk):
    system = get_object_or_404(System, pk=pk)
    if request.method == 'POST':
        form = SystemForm(request.POST, instance=system)
        if form.is_valid():
            sys_obj = form.save(commit=False)
            sys_obj.updated_by = request.user
            sys_obj.save()
            messages.success(request, 'System updated successfully.')
            return redirect('systems:system_detail', pk=system.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = SystemForm(instance=system)
    return render(request, 'systems/system_form.html', {'form': form, 'system': system})

@login_required
def system_delete(request, pk):
    system = get_object_or_404(System, pk=pk)
    if request.method == 'POST':
        system.delete()
        messages.success(request, 'System deleted successfully.')
        return redirect('systems:system_list')
    return render(request, 'systems/system_confirm_delete.html', {'system': system})


@login_required
def system_notifications(request):
    """
    In-app view for renewal reminders and contract visibility.
    """
    try:
        window_days = int(request.GET.get('window', 60))
        window_days = max(1, min(window_days, 365))
    except (TypeError, ValueError):
        window_days = 60

    today = timezone.now().date()
    cutoff = today + timedelta(days=window_days)

    contracts = SystemContract.objects.select_related('system')
    upcoming = contracts.filter(renewal_date__isnull=False, renewal_date__lte=cutoff).order_by('renewal_date')
    overdue = upcoming.filter(renewal_date__lt=today)
    due_soon = upcoming.filter(renewal_date__gte=today)
    missing = contracts.filter(renewal_date__isnull=True)
    missing_for_systems = System.objects.filter(contract__isnull=True)
    missing_total = missing.count() + missing_for_systems.count()

    total_annualized = Decimal('0')
    for contract in contracts:
        annual = contract.annualized_fee()
        if annual:
            total_annualized += annual

    context = {
        'window_days': window_days,
        'today': today,
        'upcoming': upcoming,
        'overdue': overdue,
        'due_soon': due_soon,
        'missing': missing,
        'missing_for_systems': missing_for_systems,
        'missing_total': missing_total,
        'total_annualized': total_annualized,
        'monthly_equivalent': (total_annualized / Decimal('12')) if total_annualized else None,
    }
    return render(request, 'systems/notification.html', context)


@login_required
def system_contract_edit(request, pk):
    """
    Dedicated page to manage contract & renewal data for a system.
    """
    system = get_object_or_404(System, pk=pk)
    contract, _ = SystemContract.objects.get_or_create(system=system)
    show_tiers = system.system_type == 'Email Subscription'

    if request.method == 'POST':
        form = SystemContractForm(request.POST, request.FILES, instance=contract)
        tier_formset = SystemSubscriptionTierFormSet(
            request.POST,
            instance=contract,
            prefix='tiers'
        ) if show_tiers else None
        if form.is_valid() and (not show_tiers or tier_formset.is_valid()):
            form.save()
            if show_tiers:
                tier_formset.save()
            messages.success(request, 'Contract & renewal details updated.')
            return redirect('systems:system_detail', pk=system.pk)
        # Surface detailed validation for debugging
        error_blobs = []
        if form.errors:
            error_blobs.append(f"Contract: {form.errors.as_text()}")
        if form.non_field_errors():
            error_blobs.append(f"Contract (non-field): {form.non_field_errors().as_text()}")
        if show_tiers and tier_formset:
            if tier_formset.non_form_errors():
                error_blobs.append(f"Tiers (non-form): {tier_formset.non_form_errors().as_text()}")
            for idx, tf in enumerate(tier_formset.forms):
                if tf.errors or tf.non_field_errors():
                    error_blobs.append(f"Tier {idx + 1}: {tf.errors.as_text()} {tf.non_field_errors().as_text()}")
        detail_msg = " | ".join(error_blobs) if error_blobs else ''
        messages.error(request, f'Please correct the errors below. {detail_msg}')
    else:
        form = SystemContractForm(instance=contract)
        tier_formset = SystemSubscriptionTierFormSet(
            instance=contract,
            prefix='tiers'
        ) if show_tiers else None

    context = {
        'system': system,
        'form': form,
        'tier_formset': tier_formset,
        'show_tiers': show_tiers,
    }
    return render(request, 'systems/contract_form.html', context)


@login_required
def system_dues_notifications(request):
    """
    P&L-style view of monthly and yearly dues for all systems.
    Shows billing currency amounts plus local equivalents (when exchange is provided).
    """
    contracts = SystemContract.objects.select_related('system')

    # Filters
    q = request.GET.get('q', '').strip()
    billing_currency_filter = request.GET.get('billing_currency', '').strip()
    local_currency_filter = request.GET.get('local_currency', '').strip()

    if q:
        contracts = contracts.filter(
            Q(system__name__icontains=q) |
            Q(system__code__icontains=q)
        )
    if billing_currency_filter:
        contracts = contracts.filter(contract_fee_currency__iexact=billing_currency_filter)
    if local_currency_filter:
        contracts = contracts.filter(local_currency__iexact=local_currency_filter)

    summary_rows = []
    total_monthly_local = Decimal('0')
    total_yearly_local = Decimal('0')

    today = date.today()
    current_month = today.strftime("%B %Y")
    next_month = (today.replace(day=1) + timedelta(days=32)).strftime("%B %Y")
    previous_month = (today.replace(day=1) - timedelta(days=1)).strftime("%B %Y")

    def derive_billing_amounts(contract: SystemContract):
        """
        Derive monthly/yearly billing amounts if not explicitly provided.
        Prefer subscription tiers when present; else use due_amount_*; else derive from contract_fee_amount/payment_frequency.
        Uses VAT-inclusive fee if available.
        """
        # 1) Sum tiers if available
        tiers = list(contract.subscription_tiers.all())
        if tiers:
            monthly = sum([t.monthly_billing_amount() for t in tiers], Decimal('0'))
            yearly = sum([t.yearly_billing_amount() for t in tiers], Decimal('0'))
            return monthly, yearly

        # 2) Use explicit dues
        monthly = contract.due_amount_monthly
        yearly = contract.due_amount_yearly

        base = contract.fee_amount_including_vat() or contract.contract_fee_amount or Decimal('0')
        freq = (contract.payment_frequency or '').lower()

        if monthly is None or yearly is None:
            if freq == 'monthly':
                monthly = monthly if monthly is not None else base
                yearly = yearly if yearly is not None else (base * Decimal('12'))
            elif freq == 'quarterly':
                monthly = monthly if monthly is not None else (base / Decimal('3'))
                yearly = yearly if yearly is not None else (base * Decimal('4'))
            elif freq == 'yearly':
                yearly = yearly if yearly is not None else base
                monthly = monthly if monthly is not None else (yearly / Decimal('12'))
            else:
                # one_time or hybrid or unspecified: treat as yearly, spread across 12 for monthly view
                yearly = yearly if yearly is not None else base
                monthly = monthly if monthly is not None else (yearly / Decimal('12'))

        return (
            monthly or Decimal('0'),
            yearly or Decimal('0'),
        )

    for contract in contracts:
        system = contract.system
        monthly_billing, yearly_billing = derive_billing_amounts(contract)

        monthly_local = None
        yearly_local = None
        if contract.exchange_rate_to_local:
            monthly_local = (monthly_billing * contract.exchange_rate_to_local).quantize(Decimal('0.01'))
            yearly_local = (yearly_billing * contract.exchange_rate_to_local).quantize(Decimal('0.01'))
            total_monthly_local += monthly_local
            total_yearly_local += yearly_local

        summary_rows.append({
            "system": system,
            "monthly_billing": monthly_billing.quantize(Decimal('0.01')),
            "yearly_billing": yearly_billing.quantize(Decimal('0.01')),
            "monthly_local": monthly_local,
            "yearly_local": yearly_local,
            "billing_currency": contract.contract_fee_currency,
            "local_currency": contract.local_currency,
        })

    context = {
        "rows": summary_rows,
        "current_month": current_month,
        "next_month": next_month,
        "previous_month": previous_month,
        "total_monthly_local": total_monthly_local if total_monthly_local else None,
        "total_yearly_local": total_yearly_local if total_yearly_local else None,
        "q": q,
        "billing_currency_filter": billing_currency_filter,
        "local_currency_filter": local_currency_filter,
    }
    export_fmt = request.GET.get('export', '').lower()
    if export_fmt == 'csv':
        return _export_dues_csv(summary_rows)
    if export_fmt == 'pdf':
        return _export_dues_pdf(context)

    return render(request, 'systems/dues_notification.html', context)


def _export_dues_csv(rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "System",
        "Monthly (billing)",
        "Yearly (billing)",
        "Billing Currency",
        "Monthly (local)",
        "Yearly (local)",
        "Local Currency",
    ])
    for row in rows:
        writer.writerow([
            row["system"].name,
            f"{row['monthly_billing']:.2f}",
            f"{row['yearly_billing']:.2f}",
            row["billing_currency"],
            f"{row['monthly_local']:.2f}" if row["monthly_local"] is not None else "",
            f"{row['yearly_local']:.2f}" if row["yearly_local"] is not None else "",
            row["local_currency"],
        ])
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="system_dues.csv"'
    return response


def _export_dues_pdf(context):
    """
    Best-effort PDF export. If WeasyPrint is unavailable, falls back to an HTML download.
    """
    html = render_to_string("systems/dues_notification_export.html", context)
    try:
        from weasyprint import HTML  # type: ignore
        pdf_file = HTML(string=html).write_pdf()
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="system_dues.pdf"'
        return response
    except Exception:
        # Fallback to HTML download
        response = HttpResponse(html, content_type='text/html')
        response['Content-Disposition'] = 'attachment; filename="system_dues.html"'
        return response

from datetime import timedelta, date, datetime
from decimal import Decimal
from calendar import monthrange

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from django.template.loader import render_to_string
from django.http import HttpResponse
import csv
from io import StringIO

from .models import System, SystemContract, SystemContractHistory
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
            
            # Handle hardware_assets M2M relationship
            if 'hardware_assets' in form.cleaned_data:
                selected_hardware = form.cleaned_data['hardware_assets']
                sys_obj.hardware_assets.set(selected_hardware)
            
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

    # Ensure dues are auto-derived for existing contracts so fields are not blank
    if contract.due_amount_monthly is None or contract.due_amount_yearly is None:
        contract._current_user = getattr(request, 'user', None)
        contract.save()

    # Manual history snapshot creation (for previous years/months)
    history_action = request.POST.get('history_action') if request.method == 'POST' else None

    # Delete history entry
    if request.method == 'POST' and history_action == 'delete_history':
        history_id = request.POST.get('history_id')
        if history_id:
            try:
                entry = contract.history.get(pk=history_id)
                entry.delete()
                messages.success(request, 'History entry deleted.')
            except Exception:
                messages.error(request, 'Could not delete history entry.')
        return redirect('systems:system_contract_edit', pk=system.pk)

    # Edit history entry
    if request.method == 'POST' and history_action == 'edit_history':
        def _to_decimal(val):
            try:
                return Decimal(str(val)) if val not in (None, '',) else None
            except (ArithmeticError, ValueError):
                return None
        history_id = request.POST.get('history_id')
        if history_id:
            try:
                entry = contract.history.get(pk=history_id)
                entry.contract_fee_amount = _to_decimal(request.POST.get('edit_contract_fee_amount'))
                entry.due_amount_monthly = _to_decimal(request.POST.get('edit_due_amount_monthly'))
                entry.due_amount_yearly = _to_decimal(request.POST.get('edit_due_amount_yearly'))
                entry.exchange_rate_to_local = _to_decimal(request.POST.get('edit_exchange_rate_to_local'))
                entry.contract_fee_currency = (request.POST.get('edit_contract_fee_currency') or '').strip() or entry.contract_fee_currency
                entry.local_currency = (request.POST.get('edit_local_currency') or '').strip() or entry.local_currency
                entry.payment_frequency = (request.POST.get('edit_payment_frequency') or '').strip() or entry.payment_frequency
                date_str = request.POST.get('edit_date') or ''
                try:
                    date_val = date.fromisoformat(date_str) if date_str else None
                except Exception:
                    date_val = None
                if date_val:
                    entry.created_at = datetime.combine(date_val, datetime.min.time(), tzinfo=timezone.get_current_timezone())
                entry.change_reason = request.POST.get('edit_change_reason') or entry.change_reason
                entry.created_by = request.user
                entry.save()
                messages.success(request, 'History entry updated.')
            except Exception:
                messages.error(request, 'Could not update history entry.')
        return redirect('systems:system_contract_edit', pk=system.pk)

    # Manual history snapshot creation (for previous years/months)
    if request.method == 'POST' and history_action == 'add_history':
        def _to_decimal(val):
            try:
                return Decimal(str(val)) if val not in (None, '',) else None
            except (ArithmeticError, ValueError):
                return None

        history_date_str = request.POST.get('history_date') or ''
        try:
            history_date = date.fromisoformat(history_date_str)
        except Exception:
            history_date = None

        contract_fee_amount = _to_decimal(request.POST.get('history_contract_fee_amount'))
        due_amount_monthly = _to_decimal(request.POST.get('history_due_amount_monthly'))
        due_amount_yearly = _to_decimal(request.POST.get('history_due_amount_yearly'))
        exchange_rate_to_local = _to_decimal(request.POST.get('history_exchange_rate_to_local'))
        contract_fee_currency = (request.POST.get('history_contract_fee_currency') or '').strip() or contract.contract_fee_currency
        local_currency = (request.POST.get('history_local_currency') or '').strip() or contract.local_currency
        payment_frequency = (request.POST.get('history_payment_frequency') or '').strip() or contract.payment_frequency

        SystemContractHistory.create_from_contract(
            contract,
            user=request.user,
            reason=f"Manual snapshot {history_date.strftime('%Y-%m-%d') if history_date else 'manual entry'}"
        )
        # Update the freshly created entry with provided overrides
        latest_entry = contract.history.order_by('-created_at').first()
        if latest_entry:
            latest_entry.contract_fee_amount = contract_fee_amount
            latest_entry.due_amount_monthly = due_amount_monthly
            latest_entry.due_amount_yearly = due_amount_yearly
            latest_entry.exchange_rate_to_local = exchange_rate_to_local
            latest_entry.contract_fee_currency = contract_fee_currency or latest_entry.contract_fee_currency
            latest_entry.local_currency = local_currency or latest_entry.local_currency
            latest_entry.payment_frequency = payment_frequency or latest_entry.payment_frequency
            if history_date:
                latest_entry.created_at = datetime.combine(history_date, datetime.min.time(), tzinfo=timezone.get_current_timezone())
            latest_entry.save()

        messages.success(request, 'Manual history snapshot added.')
        return redirect('systems:system_contract_edit', pk=system.pk)

    if request.method == 'POST':
        form = SystemContractForm(request.POST, request.FILES, instance=contract)
        tier_formset = SystemSubscriptionTierFormSet(
            request.POST,
            instance=contract,
            prefix='tiers'
        ) if show_tiers else None
        if form.is_valid() and (not show_tiers or tier_formset.is_valid()):
            # Set user on contract instance so save() can capture it for history
            contract._current_user = request.user
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

    # Get historical data for comparison
    from calendar import monthrange
    
    today = date.today()
    
    # Get previous month history
    if today.month == 1:
        prev_month_start = date(today.year - 1, 12, 1)
        prev_month_end = date(today.year - 1, 12, 31)
    else:
        prev_month_start = date(today.year, today.month - 1, 1)
        _, last_day = monthrange(today.year, today.month - 1)
        prev_month_end = date(today.year, today.month - 1, last_day)
    
    # Get previous year history
    prev_year_start = date(today.year - 1, 1, 1)
    prev_year_end = date(today.year - 1, 12, 31)
    
    # Get history entries for comparison
    # Handle case where history model might not exist yet (migrations not run)
    prev_month_history = None
    prev_year_history = None
    latest_history = None
    
    try:
        prev_month_history = contract.history.filter(
            created_at__date__gte=prev_month_start,
            created_at__date__lte=prev_month_end
        ).order_by('-created_at').first()
        
        prev_year_history = contract.history.filter(
            created_at__date__gte=prev_year_start,
            created_at__date__lte=prev_year_end
        ).order_by('-created_at').first()
        
        # Get most recent history entry (before current values)
        latest_history = contract.history.order_by('-created_at').first()
    except (AttributeError, Exception):
        # History model doesn't exist yet or other error
        pass
    
    # History log (latest first)
    history_entries = contract.history.order_by('-created_at')[:50] if hasattr(contract, 'history') else []

    context = {
        'system': system,
        'form': form,
        'tier_formset': tier_formset,
        'show_tiers': show_tiers,
        'contract': contract,
        'prev_month_history': prev_month_history,
        'prev_year_history': prev_year_history,
        'latest_history': latest_history,
        'previous_month_str': prev_month_start.strftime("%B %Y"),
        'previous_year_str': str(today.year - 1),
        'history_entries': history_entries,
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
    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()

    if q:
        contracts = contracts.filter(
            Q(system__name__icontains=q) |
            Q(system__code__icontains=q)
        )
    if billing_currency_filter:
        contracts = contracts.filter(contract_fee_currency__iexact=billing_currency_filter)
    if local_currency_filter:
        contracts = contracts.filter(local_currency__iexact=local_currency_filter)
    
    # Date range filter - filter by renewal_date, but include contracts without renewal_date
    if start_date_str or end_date_str:
        date_conditions = Q()
        
        if start_date_str and end_date_str:
            try:
                start_date = date.fromisoformat(start_date_str)
                end_date = date.fromisoformat(end_date_str)
                # Include contracts with renewal_date in range OR no renewal_date
                date_conditions = (Q(renewal_date__gte=start_date) & Q(renewal_date__lte=end_date)) | Q(renewal_date__isnull=True)
            except (ValueError, TypeError):
                start_date_str = ''
                end_date_str = ''
        elif start_date_str:
            try:
                start_date = date.fromisoformat(start_date_str)
                # Include contracts with renewal_date >= start_date OR no renewal_date
                date_conditions = Q(renewal_date__gte=start_date) | Q(renewal_date__isnull=True)
            except (ValueError, TypeError):
                start_date_str = ''
        elif end_date_str:
            try:
                end_date = date.fromisoformat(end_date_str)
                # Include contracts with renewal_date <= end_date OR no renewal_date
                date_conditions = Q(renewal_date__lte=end_date) | Q(renewal_date__isnull=True)
            except (ValueError, TypeError):
                end_date_str = ''
        
        if date_conditions:
            contracts = contracts.filter(date_conditions)

    summary_rows = []
    total_monthly_local = Decimal('0')
    total_yearly_local = Decimal('0')

    today = date.today()
    current_month = today.strftime("%B %Y")
    next_month = (today.replace(day=1) + timedelta(days=32)).strftime("%B %Y")
    previous_month = (today.replace(day=1) - timedelta(days=1)).strftime("%B %Y")
    
    # Calculate previous month and previous year dates
    if today.month == 1:
        prev_month_start = date(today.year - 1, 12, 1)
        prev_month_end = date(today.year - 1, 12, 31)
    else:
        prev_month_start = date(today.year, today.month - 1, 1)
        _, last_day = monthrange(today.year, today.month - 1)
        prev_month_end = date(today.year, today.month - 1, last_day)
    
    prev_year_start = date(today.year - 1, 1, 1)
    prev_year_end = date(today.year - 1, 12, 31)
    
    previous_month_str = prev_month_start.strftime("%B %Y")
    previous_year_str = f"{today.year - 1}"

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

    # Calculate previous month totals (contracts that existed in previous month)
    prev_month_contracts = SystemContract.objects.select_related('system')
    # Apply same filters but for previous month
    if q:
        prev_month_contracts = prev_month_contracts.filter(
            Q(system__name__icontains=q) |
            Q(system__code__icontains=q)
        )
    if billing_currency_filter:
        prev_month_contracts = prev_month_contracts.filter(contract_fee_currency__iexact=billing_currency_filter)
    if local_currency_filter:
        prev_month_contracts = prev_month_contracts.filter(local_currency__iexact=local_currency_filter)
    # Only include contracts created before or during previous month
    prev_month_end_datetime = timezone.make_aware(datetime.combine(prev_month_end, datetime.min.time()))
    prev_month_contracts = prev_month_contracts.filter(created_at__lte=prev_month_end_datetime)
    
    prev_month_total_monthly = Decimal('0')
    prev_month_total_yearly = Decimal('0')
    for contract in prev_month_contracts:
        monthly_billing, yearly_billing = derive_billing_amounts(contract)
        if contract.exchange_rate_to_local:
            prev_month_total_monthly += (monthly_billing * contract.exchange_rate_to_local).quantize(Decimal('0.01'))
            prev_month_total_yearly += (yearly_billing * contract.exchange_rate_to_local).quantize(Decimal('0.01'))
    
    # Calculate previous year totals
    prev_year_contracts = SystemContract.objects.select_related('system')
    if q:
        prev_year_contracts = prev_year_contracts.filter(
            Q(system__name__icontains=q) |
            Q(system__code__icontains=q)
        )
    if billing_currency_filter:
        prev_year_contracts = prev_year_contracts.filter(contract_fee_currency__iexact=billing_currency_filter)
    if local_currency_filter:
        prev_year_contracts = prev_year_contracts.filter(local_currency__iexact=local_currency_filter)
    # Only include contracts created before or during previous year
    prev_year_end_datetime = timezone.make_aware(datetime.combine(prev_year_end, datetime.max.time()))
    prev_year_contracts = prev_year_contracts.filter(created_at__lte=prev_year_end_datetime)
    
    prev_year_total_monthly = Decimal('0')
    prev_year_total_yearly = Decimal('0')
    for contract in prev_year_contracts:
        monthly_billing, yearly_billing = derive_billing_amounts(contract)
        if contract.exchange_rate_to_local:
            prev_year_total_monthly += (monthly_billing * contract.exchange_rate_to_local).quantize(Decimal('0.01'))
            prev_year_total_yearly += (yearly_billing * contract.exchange_rate_to_local).quantize(Decimal('0.01'))
    
    # Calculate differences and percentages
    monthly_diff = total_monthly_local - prev_month_total_monthly if total_monthly_local and prev_month_total_monthly else None
    monthly_diff_pct = (monthly_diff / prev_month_total_monthly * Decimal('100')).quantize(Decimal('0.01')) if monthly_diff and prev_month_total_monthly else None
    
    yearly_diff = total_yearly_local - prev_year_total_yearly if total_yearly_local and prev_year_total_yearly else None
    yearly_diff_pct = (yearly_diff / prev_year_total_yearly * Decimal('100')).quantize(Decimal('0.01')) if yearly_diff and prev_year_total_yearly else None

    context = {
        "rows": summary_rows,
        "current_month": current_month,
        "next_month": next_month,
        "previous_month": previous_month,
        "previous_month_str": previous_month_str,
        "previous_year_str": previous_year_str,
        "total_monthly_local": total_monthly_local if total_monthly_local else None,
        "total_yearly_local": total_yearly_local if total_yearly_local else None,
        "prev_month_total_monthly": prev_month_total_monthly if prev_month_total_monthly else None,
        "prev_month_total_yearly": prev_month_total_yearly if prev_month_total_yearly else None,
        "prev_year_total_monthly": prev_year_total_monthly if prev_year_total_monthly else None,
        "prev_year_total_yearly": prev_year_total_yearly if prev_year_total_yearly else None,
        "monthly_diff": monthly_diff,
        "monthly_diff_pct": monthly_diff_pct,
        "yearly_diff": yearly_diff,
        "yearly_diff_pct": yearly_diff_pct,
        "q": q,
        "billing_currency_filter": billing_currency_filter,
        "local_currency_filter": local_currency_filter,
        "start_date": start_date_str,
        "end_date": end_date_str,
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

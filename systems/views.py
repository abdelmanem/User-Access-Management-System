from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from .models import System
from .forms import SystemForm, SystemUserAssignForm, SystemHardwareAssignForm
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
    assignments = UserSystemAccess.objects.filter(system=system).select_related('user', 'approved_by').order_by(
        'user__first_name', 'user__last_name'
    )

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
        else:
            assign_form = SystemUserAssignForm(system=system)
            hardware_form = SystemHardwareAssignForm(system=system)
    else:
        assign_form = SystemUserAssignForm(system=system)
        hardware_form = SystemHardwareAssignForm(system=system)

    context = {
        'system': system,
        'assign_form': assign_form,
        'hardware_form': hardware_form,
        'assignments': assignments,
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

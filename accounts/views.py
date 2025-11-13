from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.contrib.auth.forms import SetPasswordForm
from django.db import transaction
from django.db.models import Q, F, Value
from django.db.models.functions import Concat
from django.utils import timezone
from .models import CustomUser
from .forms import UserCreateForm, UserUpdateForm, UserPermissionForm
from departments.models import Department
from hardware.models import HardwareAsset
from urllib.parse import urlencode
from django.http import HttpResponse
from django.urls import reverse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from access_management.models import UserSystemAccess

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_list(request):
    from django.core.paginator import Paginator

    users_qs = CustomUser.objects.select_related('department').all().annotate(
        sort_full_name=Concat(
            F('first_name'),
            Value(' '),
            F('last_name'),
        )
    )

    # Filters
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()  # 'active', 'inactive', or ''
    dept_id = request.GET.get('department', '').strip()
    page_size_param = request.GET.get('page_size', '').strip().lower()
    allowed_page_sizes = [25, 50, 100]
    paginate = True
    if page_size_param == 'all':
        paginate = False
        page_size = None
        page_size_display = 'all'
    else:
        try:
            page_size = int(page_size_param) if page_size_param else 25
        except ValueError:
            page_size = 25
        if page_size not in allowed_page_sizes:
            page_size = 25
        page_size_display = page_size

    if q:
        users_qs = users_qs.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(employee_id__icontains=q)
        )
    if status == 'active':
        users_qs = users_qs.filter(is_active=True)
    elif status == 'inactive':
        users_qs = users_qs.filter(is_active=False)
    if dept_id:
        users_qs = users_qs.filter(department_id=dept_id)

    sort_key = (request.GET.get('sort') or 'full_name').strip()
    sort_dir = (request.GET.get('dir') or 'asc').strip().lower()

    sort_map = {
        'id': 'id',
        'username': 'username',
        'full_name': 'sort_full_name',
        'name': 'sort_full_name',
        'email': 'email',
        'department': 'department__name',
        'position': 'position',
        'status': 'is_active',
    }

    order_field = sort_map.get(sort_key, 'full_name')
    if sort_dir == 'desc':
        order_field = f'-{order_field}'

    users_qs = users_qs.order_by(order_field, 'id')

    total_count = users_qs.count()
    active_count = users_qs.filter(is_active=True).count()
    inactive_count = total_count - active_count
    no_department_count = users_qs.filter(department__isnull=True).count()

    if paginate:
        paginator = Paginator(users_qs, page_size)  # type: ignore[arg-type]
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        users_page = page_obj.object_list
    else:
        page_obj = None
        users_page = list(users_qs)

    departments = Department.objects.all().order_by('name')

    query_params = request.GET.copy()
    for key in ['sort', 'dir', 'page']:
        if key in query_params:
            del query_params[key]
    base_query = query_params.urlencode()

    return render(request, 'accounts/user_list.html', {
        'page_obj': page_obj,
        'users': users_page,
        'q': q,
        'status': status,
        'department_selected': dept_id,
        'departments': departments,
        'page_size': page_size_display,
        'allowed_page_sizes': allowed_page_sizes,
        'total_count': total_count,
        'current_sort': sort_key,
        'current_dir': 'desc' if sort_dir == 'desc' else 'asc',
        'base_query': base_query,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'no_department_count': no_department_count,
    })


def _build_filtered_users_queryset(request):
    users_qs = CustomUser.objects.select_related('department').all().annotate(
        sort_full_name=Concat(
            F('first_name'),
            Value(' '),
            F('last_name'),
        )
    )
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()
    dept_id = request.GET.get('department', '').strip()
    if q:
        users_qs = users_qs.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(employee_id__icontains=q)
        )
    if status == 'active':
        users_qs = users_qs.filter(is_active=True)
    elif status == 'inactive':
        users_qs = users_qs.filter(is_active=False)
    if dept_id:
        users_qs = users_qs.filter(department_id=dept_id)

    sort_key = (request.GET.get('sort') or 'full_name').strip()
    sort_dir = (request.GET.get('dir') or 'asc').strip().lower()
    sort_map = {
        'id': 'id',
        'username': 'username',
        'full_name': 'sort_full_name',
        'name': 'sort_full_name',
        'email': 'email',
        'department': 'department__name',
        'position': 'position',
        'status': 'is_active',
    }
    order_field = sort_map.get(sort_key, 'sort_full_name')
    if sort_dir == 'desc':
        order_field = f'-{order_field}'
    return users_qs.order_by(order_field, 'id')


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_export_excel(request):
    qs = _build_filtered_users_queryset(request)
    headers = ['ID', 'Username', 'Full Name', 'Email', 'Department', 'Position', 'Status']
    wb = Workbook()
    ws = wb.active
    ws.title = 'Users'
    ws.append(headers)
    for u in qs:
        ws.append([
            u.id,
            u.username,
            f"{u.first_name} {u.last_name}".strip(),
            u.email,
            u.department.name if u.department else '',
            u.position or '',
            'Active' if u.is_active else 'Inactive',
        ])
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="users.xlsx"'
    wb.save(response)
    return response


@login_required
@user_passes_test(lambda u: u.is_staff)
def user_export_pdf(request):
    qs = _build_filtered_users_queryset(request)
    data = [['ID', 'Username', 'Full Name', 'Email', 'Department', 'Position', 'Status']]
    for u in qs:
        data.append([
            str(u.id),
            u.username,
            f"{u.first_name} {u.last_name}".strip(),
            u.email,
            u.department.name if u.department else '',
            u.position or '',
            'Active' if u.is_active else 'Inactive',
        ])
    buffer_response = HttpResponse(content_type='application/pdf')
    buffer_response['Content-Disposition'] = 'attachment; filename="users.pdf"'
    page_size = landscape(A4)
    c = canvas.Canvas(buffer_response, pagesize=page_size)
    width, height = page_size
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))
    # Calculate table size and paginate if needed
    available_width = width - 40
    available_height = height - 60
    table.wrapOn(c, available_width, available_height)
    # Simple pagination if table is long
    y = height - 30
    rows_per_page = 25
    header = data[0]
    chunk = []
    for i, row in enumerate(data[1:], start=1):
        chunk.append(row)
        if len(chunk) == rows_per_page or i == len(data) - 1:
            t = Table([header] + chunk, repeatRows=1)
            t.setStyle(table._argW[1]) if hasattr(table, '_argW') else None
            t.setStyle(table._cellStyles) if hasattr(table, '_cellStyles') else None
            t.setStyle(table._tblStyle)
            t.wrapOn(c, available_width, available_height)
            t.drawOn(c, 20, 20)
            c.showPage()
            chunk = []
    c.save()
    return buffer_response

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    accesses = UserSystemAccess.objects.filter(user=user).select_related('system').order_by('-created_at')
    return render(request, 'accounts/user_detail.html', {'user': user, 'accesses': accesses})

@login_required
@permission_required('accounts.add_customuser', raise_exception=True)
def user_create(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.created_by = request.user
            user.updated_by = request.user
            user.save()
            form.save_m2m()
            messages.success(request, 'User created successfully.')
            return redirect('accounts:user_detail', pk=user.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = UserCreateForm()
    return render(request, 'accounts/user_form.html', {'form': form})

@login_required
@permission_required('accounts.change_customuser', raise_exception=True)
def user_update(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            updated_user.updated_by = request.user
            updated_user.save()
            form.save_m2m()
            messages.success(request, 'User updated successfully.')
            return redirect('accounts:user_detail', pk=user.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'user': user})


@login_required
@permission_required('accounts.change_customuser', raise_exception=True)
def user_reset_password(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = SetPasswordForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password reset successfully.')
            return redirect('accounts:user_detail', pk=user.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = SetPasswordForm(user=user)
    return render(request, 'accounts/user_reset_password.html', {'form': form, 'user': user})

@login_required
@permission_required('accounts.delete_customuser', raise_exception=True)
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

@login_required
@permission_required('accounts.change_customuser', raise_exception=True)
def user_toggle_active(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('accounts:user_list')

    if request.method != 'POST':
        return redirect(next_url)

    target_status = not user.is_active

    if user.is_active and not target_status:
        active_assignments = list(UserSystemAccess.objects.filter(
            user=user,
            status__in=['Active', 'Approved', 'Pending']
        ).select_related('system'))

        hardware_primary = list(HardwareAsset.objects.filter(primary_user=user))
        hardware_shared = list(HardwareAsset.objects.filter(assigned_users=user).exclude(primary_user=user))

        hardware_assets_map = {}
        for asset in hardware_primary:
            hardware_assets_map.setdefault(asset.id, {'asset': asset, 'roles': set()})
            hardware_assets_map[asset.id]['roles'].add('Primary Owner')
        for asset in hardware_shared:
            hardware_assets_map.setdefault(asset.id, {'asset': asset, 'roles': set()})
            hardware_assets_map[asset.id]['roles'].add('Shared User')
        hardware_assets = []
        for entry in hardware_assets_map.values():
            entry['roles'] = sorted(entry['roles'])
            hardware_assets.append(entry)

        needs_confirmation = bool(active_assignments or hardware_assets)
        confirmed = request.POST.get('confirm_deactivate') == '1'

        if needs_confirmation and not confirmed:
            context = {
                'user': user,
                'next_url': next_url,
                'system_assignments': active_assignments,
                'hardware_assets': hardware_assets,
            }
            return render(request, 'accounts/user_deactivate_confirm.html', context)

        if needs_confirmation and confirmed:
            errors = []
            if active_assignments and request.POST.get('confirm_system', '') != '1':
                errors.append('Please confirm system assignments should be suspended.')
            if hardware_assets and request.POST.get('confirm_hardware', '') != '1':
                errors.append('Please confirm any assigned hardware has been collected.')

            if errors:
                for error in errors:
                    messages.error(request, error)
                context = {
                    'user': user,
                    'next_url': next_url,
                    'system_assignments': active_assignments,
                    'hardware_assets': hardware_assets,
                }
                return render(request, 'accounts/user_deactivate_confirm.html', context)

            with transaction.atomic():
                if active_assignments:
                    now = timezone.now()
                    UserSystemAccess.objects.filter(
                        user=user,
                        status__in=['Active', 'Approved']
                    ).update(status='Suspended', access_end_date=now)
                    UserSystemAccess.objects.filter(
                        user=user,
                        status='Pending'
                    ).update(status='Cancelled')

                if hardware_assets:
                    status_action = request.POST.get('hardware_status_action', 'no_change')
                    for entry in hardware_assets:
                        asset = entry['asset']
                        fields_to_update = set()

                        if asset.primary_user_id == user.id:
                            asset.primary_user = None
                            fields_to_update.add('primary_user')

                        if asset.assigned_users.filter(id=user.id).exists():
                            asset.assigned_users.remove(user)

                        if status_action == 'in_storage' and asset.status != 'In Storage':
                            asset.status = 'In Storage'
                            fields_to_update.add('status')
                        elif status_action == 'retired' and asset.status != 'Retired':
                            asset.status = 'Retired'
                            fields_to_update.add('status')

                        if fields_to_update:
                            if hasattr(asset, 'updated_by'):
                                asset.updated_by = request.user
                                fields_to_update.add('updated_by')
                            asset.save(update_fields=list(fields_to_update))

                user.is_active = False
                if hasattr(user, 'updated_by'):
                    user.updated_by = request.user
                    user.save(update_fields=['is_active', 'updated_by'])
                else:
                    user.save(update_fields=['is_active'])

                messages.success(request, 'User deactivated. Related assignments have been updated.')
                return redirect(next_url)

    user.is_active = target_status
    if hasattr(user, 'updated_by'):
        user.updated_by = request.user
        user.save(update_fields=['is_active', 'updated_by'])
    else:
        user.save(update_fields=['is_active'])

    messages.success(request, f"User {'activated' if user.is_active else 'deactivated'} successfully.")
    return redirect(next_url)

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_bulk_action(request):
    if request.method != 'POST':
        return redirect('accounts:user_list')

    action = request.POST.get('action', '').strip()
    selected_ids = request.POST.getlist('selected')

    # Preserve filters after redirect
    redirect_params = {
        'q': request.POST.get('q', ''),
        'status': request.POST.get('status', ''),
        'department': request.POST.get('department', ''),
        'page_size': request.POST.get('page_size', ''),
        'sort': request.POST.get('sort', ''),
        'dir': request.POST.get('dir', ''),
    }
    base_url = reverse('accounts:user_list')
    query_string = urlencode({k: v for k, v in redirect_params.items() if v})
    redirect_url = f"{base_url}?{query_string}" if query_string else base_url

    if not selected_ids:
        messages.warning(request, 'No users selected.')
        return redirect(redirect_url)

    queryset = CustomUser.objects.filter(id__in=selected_ids)

    if action == 'activate':
        if not request.user.has_perm('accounts.change_customuser'):
            messages.error(request, 'You do not have permission to activate users.')
            return redirect(redirect_url)
        updated = queryset.update(is_active=True)
        messages.success(request, f'Activated {updated} user(s).')
    elif action == 'deactivate':
        if not request.user.has_perm('accounts.change_customuser'):
            messages.error(request, 'You do not have permission to deactivate users.')
            return redirect(redirect_url)
        dependency_users = queryset.filter(
            Q(system_accesses__status__in=['Active', 'Approved', 'Pending']) |
            Q(primary_hardware_assets__isnull=False) |
            Q(hardware_assets__isnull=False)
        ).distinct()
        if dependency_users.exists():
            sample = ', '.join(dependency_users.values_list('username', flat=True)[:5])
            if dependency_users.count() > 5:
                sample += ', …'
            messages.error(
                request,
                f"Bulk deactivation halted. The following users still have system or hardware assignments: {sample}. "
                "Please review and deactivate these accounts individually so dependencies can be addressed."
            )
            return redirect(redirect_url)
        updated = queryset.update(is_active=False)
        messages.success(request, f'Deactivated {updated} user(s).')
    elif action == 'delete':
        if not request.user.has_perm('accounts.delete_customuser'):
            messages.error(request, 'You do not have permission to delete users.')
            return redirect(redirect_url)
        count = queryset.count()
        queryset.delete()
        messages.success(request, f'Deleted {count} user(s).')
    elif action == 'assign_department':
        if not request.user.has_perm('accounts.change_customuser'):
            messages.error(request, 'You do not have permission to assign departments.')
            return redirect(redirect_url)
        department_id = request.POST.get('bulk_department_id', '').strip()
        if department_id:
            department = Department.objects.filter(id=department_id).first()
            if department is None:
                messages.error(request, 'Selected department was not found.')
                return redirect(redirect_url)
            updated = queryset.update(department=department, updated_by=request.user)
            messages.success(request, f'Assigned {updated} user(s) to {department.name}.')
        else:
            # Clear department assignment
            updated = queryset.update(department=None, updated_by=request.user)
            messages.success(request, f'Removed department assignment for {updated} user(s).')
    elif action == 'clear_email':
        if not request.user.has_perm('accounts.change_customuser'):
            messages.error(request, 'You do not have permission to modify user emails.')
            return redirect(redirect_url)
        cleared = queryset.update(email='', updated_by=request.user)
        messages.success(request, f'Cleared email addresses for {cleared} user(s).')
    else:
        messages.warning(request, 'Please choose a valid bulk action.')

    return redirect(redirect_url)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_manage_permissions(request, pk):
    """Allow superusers to manage a user's group memberships and direct permissions."""
    target_user = get_object_or_404(CustomUser, pk=pk)

    if request.method == 'POST':
        form = UserPermissionForm(request.POST, user_instance=target_user)
        if form.is_valid():
            is_staff = form.cleaned_data['is_staff']
            is_superuser_flag = form.cleaned_data['is_superuser']
            groups = form.cleaned_data['groups']
            permissions = form.cleaned_data['permissions']

            if target_user.is_superuser and not is_superuser_flag:
                other_superusers = CustomUser.objects.filter(is_superuser=True).exclude(pk=target_user.pk).exists()
                if not other_superusers:
                    messages.error(request, 'At least one superuser account must remain. Promote another superuser before demoting this user.')
                    return redirect('accounts:user_manage_permissions', pk=target_user.pk)

            target_user.groups.set(groups)
            target_user.user_permissions.set(permissions)
            target_user.is_staff = is_staff
            target_user.is_superuser = is_superuser_flag
            target_user.updated_by = request.user
            target_user.save(update_fields=['is_staff', 'is_superuser', 'updated_by', 'updated_at'])

            messages.success(request, 'Permissions updated successfully.')
            return redirect('accounts:user_detail', pk=target_user.pk)

        messages.error(request, 'Please correct the errors below.')
    else:
        form = UserPermissionForm(user_instance=target_user)

    direct_permissions = target_user.user_permissions.select_related('content_type').order_by(
        'content_type__app_label', 'codename'
    )

    return render(
        request,
        'accounts/user_permissions.html',
        {
            'form': form,
            'user': target_user,
            'direct_permissions': direct_permissions,
        },
    )


@login_required
@permission_required('accounts.change_customuser', raise_exception=True)
def user_assign_department(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', reverse('accounts:user_list')))

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('accounts:user_list')
    department_id = (request.POST.get('department_id') or '').strip()

    if department_id:
        department = Department.objects.filter(id=department_id).first()
        if department is None:
            messages.error(request, 'Selected department was not found.')
            return redirect(next_url)
        user.department = department
        dept_label = department.name
    else:
        user.department = None
        dept_label = 'No department'

    if hasattr(user, 'updated_by'):
        user.updated_by = request.user
        user.save(update_fields=['department', 'updated_by'])
    else:
        user.save(update_fields=['department'])

    messages.success(request, f"Assigned {user.username} to {dept_label}.")
    return redirect(next_url)

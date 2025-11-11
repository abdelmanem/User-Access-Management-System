from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.db.models import Q
from .models import CustomUser
from .forms import UserCreateForm, UserUpdateForm
from departments.models import Department
from urllib.parse import urlencode

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_list(request):
    from django.core.paginator import Paginator

    users_qs = CustomUser.objects.select_related('department').all()

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

    users_qs = users_qs.order_by('first_name', 'last_name')

    total_count = users_qs.count()

    if paginate:
        paginator = Paginator(users_qs, page_size)  # type: ignore[arg-type]
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        users_page = page_obj.object_list
    else:
        page_obj = None
        users_page = list(users_qs)

    departments = Department.objects.all().order_by('name')

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
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    return render(request, 'accounts/user_detail.html', {'user': user})

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
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        messages.success(request, f"User {'activated' if user.is_active else 'deactivated'} successfully.")
    return redirect(request.META.get('HTTP_REFERER', 'accounts:user_list'))

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
    }
    redirect_url = f"{redirect('accounts:user_list').url}?{urlencode({k: v for k, v in redirect_params.items() if v})}"

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
        updated = queryset.update(is_active=False)
        messages.success(request, f'Deactivated {updated} user(s).')
    elif action == 'delete':
        if not request.user.has_perm('accounts.delete_customuser'):
            messages.error(request, 'You do not have permission to delete users.')
            return redirect(redirect_url)
        count = queryset.count()
        queryset.delete()
        messages.success(request, f'Deleted {count} user(s).')
    else:
        messages.warning(request, 'Please choose a valid bulk action.')

    return redirect(redirect_url)

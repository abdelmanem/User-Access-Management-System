from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, F, Value, Case, When, IntegerField
from django.db.models.functions import Concat, Cast
from .models import Department
from .forms import DepartmentForm, DepartmentMemberAssignForm
from accounts.models import CustomUser

@login_required
def department_list(request):
    # Handle bulk actions
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected')
        bulk_action = (request.POST.get('bulk_action') or '').strip()
        next_url = request.META.get('HTTP_REFERER') or ''

        if not selected_ids:
            messages.error(request, 'No departments selected for bulk action.')
            return redirect(request.path)

        queryset = Department.objects.filter(id__in=selected_ids)

        if bulk_action == 'activate':
            updated = queryset.update(is_active=True)
            messages.success(request, f'Activated {updated} department(s).')
        elif bulk_action == 'deactivate':
            updated = queryset.update(is_active=False)
            messages.success(request, f'Deactivated {updated} department(s).')
        elif bulk_action == 'set_parent':
            parent_id = request.POST.get('parent_department_id')
            parent = None
            if parent_id:
                parent = Department.objects.filter(id=parent_id).first()
                if parent is None:
                    messages.error(request, 'Selected parent department not found.')
                    return redirect(request.path)
            for dept in queryset:
                # Prevent setting a department as parent of itself or creating cycles
                if parent and (dept.id == parent.id or parent.full_path.startswith(dept.full_path)):
                    continue
                if dept.parent_department_id != (parent.id if parent else None):
                    dept.parent_department = parent
                    dept.save(update_fields=['parent_department'])
            messages.success(request, 'Updated parent department for selected items.')
        elif bulk_action == 'set_type':
            dept_type = (request.POST.get('department_type') or '').strip()
            valid_types = {k for k, _ in Department.DEPARTMENT_TYPE_CHOICES}
            if dept_type not in valid_types:
                messages.error(request, 'Invalid department type selected.')
                return redirect(request.path)
            updated = queryset.update(department_type=dept_type)
            messages.success(request, f'Updated type for {updated} department(s).')
        else:
            messages.error(request, 'Invalid bulk action.')

        return redirect(next_url or request.path)

    # Supported sort keys -> ORM fields
    sort_key = (request.GET.get('sort') or 'name').strip()
    sort_dir = (request.GET.get('dir') or 'asc').strip().lower()

    sortable_map = {
        'name': 'name',
        'code': 'code',
        'parent': 'parent_department__name',
        'head': 'head_of_department__first_name',
        'member_count': 'member_count',
    }

    # Base queryset with annotations for sorting
    queryset = Department.objects.all().annotate(
        member_count=Count('department_members', distinct=True),
        head_name=Concat(
            F('head_of_department__first_name'),
            Value(' '),
            F('head_of_department__last_name'),
        ),
    )

    # Special handling for code: natural numeric sort when codes are numeric
    if sort_key == 'code':
        queryset = queryset.annotate(
            code_numeric=Case(
                When(code__regex=r'^\d+$', then=Cast('code', IntegerField())),
                default=Value(None),
                output_field=IntegerField(),
            )
        )
        if sort_dir == 'desc':
            departments = queryset.order_by('-code_numeric', '-code', 'id')
        else:
            departments = queryset.order_by('code_numeric', 'code', 'id')
    else:
        order_field = sortable_map.get(sort_key, 'name')
        if sort_dir == 'desc':
            order_field = f'-{order_field}'
        departments = queryset.order_by(order_field, 'id')

    context = {
        'departments': departments,
        'current_sort': sort_key,
        'current_dir': 'desc' if sort_dir == 'desc' else 'asc',
        'all_departments': Department.objects.order_by('name'),
        'type_choices': Department.DEPARTMENT_TYPE_CHOICES,
    }
    return render(request, 'departments/department_list.html', context)

@login_required
def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        member_form = DepartmentMemberAssignForm(request.POST, department=department)
        if member_form.is_valid():
            selected_users = member_form.cleaned_data['users']
            selected_ids = list(selected_users.values_list('id', flat=True))

            removed_count = CustomUser.objects.filter(department=department).exclude(id__in=selected_ids).update(
                department=None,
                updated_by=request.user
            )

            added_queryset = CustomUser.objects.filter(id__in=selected_ids)
            added_count = added_queryset.exclude(department=department).update(
                department=department,
                updated_by=request.user
            )

            # Ensure all selected users are attached to this department (covers already members too)
            added_queryset.filter(department=department).update(updated_by=request.user)

            messages.success(
                request,
                f"Department membership updated. Assigned {added_count} user(s), removed {removed_count} user(s)."
            )
            return redirect('departments:department_detail', pk=department.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        member_form = DepartmentMemberAssignForm(department=department)

    context = {
        'department': department,
        'member_form': member_form,
    }
    return render(request, 'departments/department_detail.html', context)

@login_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            dept = form.save(commit=False)
            dept.created_by = request.user
            dept.updated_by = request.user
            dept.save()
            messages.success(request, 'Department created successfully.')
            return redirect('departments:department_detail', pk=dept.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = DepartmentForm()
    return render(request, 'departments/department_form.html', {'form': form})

@login_required
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            dept = form.save(commit=False)
            dept.updated_by = request.user
            dept.save()
            messages.success(request, 'Department updated successfully.')
            return redirect('departments:department_detail', pk=department.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'departments/department_form.html', {'form': form, 'department': department})

@login_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully.')
        return redirect('departments:department_list')
    return render(request, 'departments/department_confirm_delete.html', {'department': department})

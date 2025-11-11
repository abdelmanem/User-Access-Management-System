from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Department
from .forms import DepartmentForm

@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'departments/department_list.html', {'departments': departments})

@login_required
def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return render(request, 'departments/department_detail.html', {'department': department})

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

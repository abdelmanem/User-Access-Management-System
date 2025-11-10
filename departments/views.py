from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Department

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
    # Placeholder for department creation view
    return render(request, 'departments/department_form.html', {'form': None})

@login_required
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    # Placeholder for department update view
    return render(request, 'departments/department_form.html', {'form': None, 'department': department})

@login_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully.')
        return redirect('departments:department_list')
    return render(request, 'departments/department_confirm_delete.html', {'department': department})

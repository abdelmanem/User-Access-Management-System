from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Department

def department_list(request):
    departments = Department.objects.all()
    return render(request, 'departments/department_list.html', {'departments': departments})

def department_detail(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return render(request, 'departments/department_detail.html', {'department': department})

def department_create(request):
    # Placeholder for department creation view
    return render(request, 'departments/department_form.html', {'form': None})

def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    # Placeholder for department update view
    return render(request, 'departments/department_form.html', {'form': None, 'department': department})

def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully.')
        return redirect('departments:department_list')
    return render(request, 'departments/department_confirm_delete.html', {'department': department})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import System
from .forms import SystemForm

@login_required
def system_list(request):
    systems = System.objects.all()
    return render(request, 'systems/system_list.html', {'systems': systems})

@login_required
def system_detail(request, pk):
    system = get_object_or_404(System, pk=pk)
    return render(request, 'systems/system_detail.html', {'system': system})

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

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import System

def system_list(request):
    systems = System.objects.all()
    return render(request, 'systems/system_list.html', {'systems': systems})

def system_detail(request, pk):
    system = get_object_or_404(System, pk=pk)
    return render(request, 'systems/system_detail.html', {'system': system})

def system_create(request):
    # Placeholder for system creation view
    return render(request, 'systems/system_form.html', {'form': None})

def system_update(request, pk):
    system = get_object_or_404(System, pk=pk)
    # Placeholder for system update view
    return render(request, 'systems/system_form.html', {'form': None, 'system': system})

def system_delete(request, pk):
    system = get_object_or_404(System, pk=pk)
    if request.method == 'POST':
        system.delete()
        messages.success(request, 'System deleted successfully.')
        return redirect('systems:system_list')
    return render(request, 'systems/system_confirm_delete.html', {'system': system})

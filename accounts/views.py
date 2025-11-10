from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser

@login_required
def user_list(request):
    users = CustomUser.objects.all()
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
def user_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    return render(request, 'accounts/user_detail.html', {'user': user})

@login_required
def user_create(request):
    # Placeholder for user creation view
    return render(request, 'accounts/user_form.html', {'form': None})

@login_required
def user_update(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    # Placeholder for user update view
    return render(request, 'accounts/user_form.html', {'form': None, 'user': user})

@login_required
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

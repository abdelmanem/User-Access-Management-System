from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import CustomUser
from .forms import UserCreateForm, UserUpdateForm

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
def user_delete(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user': user})

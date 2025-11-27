"""
LDAP/AD Configuration and Management Views
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate
from .models import LDAPConfiguration
from .forms import (
    LDAPConfigurationForm,
    LDAPTestLoginForm,
)
from .ldap_backend import LDAPSync


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_configuration(request):
    """
    View for configuring LDAP/AD settings
    """
    # Get or create LDAP configuration
    ldap_config = LDAPConfiguration.objects.first()
    
    if request.method == 'POST':
        form = LDAPConfigurationForm(request.POST, instance=ldap_config)
        if form.is_valid():
            config = form.save(commit=False)
            config.updated_by = request.user
            config.save()
            messages.success(request, 'LDAP configuration saved successfully.')
            return redirect('accounts:ldap_configuration')
    else:
        form = LDAPConfigurationForm(instance=ldap_config)
    
    test_login_form = LDAPTestLoginForm()
    
    return render(request, 'accounts/ldap_configuration.html', {
        'form': form,
        'ldap_config': ldap_config,
        'test_login_form': test_login_form,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_test_connection(request):
    """
    Test LDAP connection
    """
    ldap_config = LDAPConfiguration.get_active_config()
    
    if not ldap_config:
        messages.error(request, 'LDAP is not configured. Please configure LDAP settings first.')
        return redirect('accounts:ldap_configuration')
    
    if request.method == 'POST':
        result = LDAPSync.test_connection(ldap_config)
        if result['success']:
            messages.success(request, f"✓ {result['message']}")
        else:
            messages.error(request, f"✗ {result['message']}")
        return redirect('accounts:ldap_configuration')
    
    return redirect('accounts:ldap_configuration')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_test_login(request):
    """
    Test LDAP login with credentials
    """
    ldap_config = LDAPConfiguration.get_active_config()
    
    if not ldap_config:
        messages.error(request, 'LDAP is not configured. Please configure LDAP settings first.')
        return redirect('accounts:ldap_configuration')
    
    if request.method == 'POST':
        form = LDAPTestLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Try to authenticate
            user = authenticate(request, username=username, password=password)
            
            if user:
                messages.success(
                    request,
                    f"✓ LDAP login successful for user: {username} ({user.first_name} {user.last_name})"
                )
            else:
                messages.error(
                    request,
                    f"✗ LDAP login failed for user: {username}. Check credentials and LDAP configuration."
                )
    
    return redirect('accounts:ldap_configuration')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_sync_users(request):
    """
    Sync users from LDAP/AD
    """
    ldap_config = LDAPConfiguration.get_active_config()
    
    if not ldap_config:
        messages.error(request, 'LDAP is not configured. Please configure LDAP settings first.')
        return redirect('accounts:ldap_configuration')
    
    if request.method == 'POST':
        messages.info(request, 'Starting LDAP user sync...')
        result = LDAPSync.sync_all_users(ldap_config)
        
        if result['success']:
            messages.success(request, f"✓ {result['message']}")
        else:
            messages.error(request, f"✗ Sync failed: {result['message']}")
    
    return redirect('accounts:ldap_configuration')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_configuration_list(request):
    """
    List all LDAP configurations
    """
    configs = LDAPConfiguration.objects.all().order_by('-created_at')
    
    return render(request, 'accounts/ldap_configuration_list.html', {
        'configs': configs,
    })


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
    LDAPBindPasswordForm,
)
from .ldap_backend import LDAPSync, LDAPComputerSync


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
    bind_password_form = LDAPBindPasswordForm()

    # Get user lookup query if provided
    lookup_username = request.GET.get('lookup_user', '').strip()
    lookup_user = None
    if lookup_username:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            # Try multiple lookup methods
            lookup_user = User.objects.get(username=lookup_username)
        except User.DoesNotExist:
            try:
                # Try by email
                lookup_user = User.objects.get(email=lookup_username)
            except User.DoesNotExist:
                try:
                    # Try by ad_username
                    lookup_user = User.objects.get(ad_username=lookup_username)
                except User.DoesNotExist:
                    # Try username without domain
                    if '@' in lookup_username:
                        base_username = lookup_username.split('@')[0]
                        try:
                            lookup_user = User.objects.get(username=base_username)
                        except User.DoesNotExist:
                            try:
                                lookup_user = User.objects.get(ad_username=base_username)
                            except User.DoesNotExist:
                                pass

    return render(request, 'accounts/ldap_configuration.html', {
        'form': form,
        'ldap_config': ldap_config,
        'test_login_form': test_login_form,
        'bind_password_form': bind_password_form,
        'lookup_user': lookup_user,
        'lookup_username': lookup_username,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_test_connection(request):
    """
    Test LDAP connection using a live bind password (not stored).
    """
    ldap_config = LDAPConfiguration.get_active_config()

    if not ldap_config:
        messages.error(request, 'LDAP is not configured. Please configure LDAP settings first.')
        return redirect('accounts:ldap_configuration')

    if request.method == 'POST':
        form = LDAPBindPasswordForm(request.POST)
        if form.is_valid():
            bind_password = form.cleaned_data['bind_password']
            result = LDAPSync.test_connection(ldap_config, bind_password=bind_password)
            if result['success']:
                messages.success(request, f"✓ {result['message']}")
            else:
                messages.error(request, f"✗ {result['message']}")
        else:
            messages.error(request, 'Please provide a valid LDAP bind password.')
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
    Sync users from LDAP/AD using a live bind password (not stored).
    """
    ldap_config = LDAPConfiguration.get_active_config()

    if not ldap_config:
        messages.error(request, 'LDAP is not configured. Please configure LDAP settings first.')
        return redirect('accounts:ldap_configuration')

    if request.method == 'POST':
        form = LDAPBindPasswordForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Please provide a valid LDAP bind password to start sync.')
            return redirect('accounts:ldap_configuration')

        bind_password = form.cleaned_data['bind_password']
        messages.info(request, 'Starting LDAP user sync...')
        result = LDAPSync.sync_all_users(ldap_config, bind_password=bind_password)

        if result['success']:
            messages.success(request, f"✓ {result['message']}")
        else:
            messages.error(request, f"✗ Sync failed: {result['message']}")

    return redirect('accounts:ldap_configuration')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_sync_computers(request):
    """
    Sync computer objects from LDAP/AD into the hardware inventory.
    """
    ldap_config = LDAPConfiguration.get_active_config()

    if not ldap_config:
        messages.error(request, 'LDAP is not configured. Please configure LDAP settings first.')
        return redirect('accounts:ldap_configuration')

    if request.method == 'POST':
        form = LDAPBindPasswordForm(request.POST)
        if not form.is_valid():
            messages.error(request, 'Please provide a valid LDAP bind password to start computer sync.')
            return redirect('accounts:ldap_configuration')

        bind_password = form.cleaned_data['bind_password']
        messages.info(request, 'Starting LDAP computer sync...')
        result = LDAPComputerSync.sync_all_computers(ldap_config, bind_password=bind_password)

        if result.get('success'):
            messages.success(request, f"✓ {result.get('message')}")
        else:
            messages.error(request, f"✗ Computer sync failed: {result.get('message')}")

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


@login_required
@user_passes_test(lambda u: u.is_superuser)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_sync_user_fields(request):
    """
    Custom LDAP sync page for selecting which user fields to sync
    """
    from .forms import LDAPBindPasswordForm, LDAPSyncFieldSelectionForm
    
    ldap_config = LDAPConfiguration.get_active_config()

    if not ldap_config:
        messages.error(request, 'LDAP is not configured. Please configure LDAP settings first.')
        return redirect('accounts:ldap_configuration')

    if request.method == 'POST':
        field_form = LDAPSyncFieldSelectionForm(request.POST, prefix='fields')
        password_form = LDAPBindPasswordForm(request.POST, prefix='password')
        
        if field_form.is_valid() and password_form.is_valid():
            bind_password = password_form.cleaned_data['bind_password']
            
            # Get selected fields
            selected_fields = {
                key: value for key, value in field_form.cleaned_data.items() 
                if value is True
            }
            
            messages.info(request, f'Starting user sync with {len(selected_fields)} fields...')
            result = LDAPSync.sync_all_users(ldap_config, bind_password=bind_password, selected_fields=selected_fields)
            
            if result['success']:
                messages.success(request, f"✓ {result['message']}")
            else:
                messages.error(request, f"✗ Sync failed: {result['message']}")
            
            return redirect('accounts:ldap_configuration')
    else:
        field_form = LDAPSyncFieldSelectionForm(prefix='fields')
        password_form = LDAPBindPasswordForm(prefix='password')
    
    return render(request, 'accounts/ldap_sync_user_fields.html', {
        'field_form': field_form,
        'password_form': password_form,
        'ldap_config': ldap_config,
    })


@login_required
@user_passes_test(lambda u: u.is_superuser)
@login_required
@user_passes_test(lambda u: u.is_superuser)
def ldap_sync_computer_fields(request):
    """
    Custom LDAP sync page for selecting which computer fields to sync
    """
    from .forms import LDAPBindPasswordForm, LDAPSyncComputerFieldSelectionForm
    
    ldap_config = LDAPConfiguration.get_active_config()

    if not ldap_config:
        messages.error(request, 'LDAP is not configured. Please configure LDAP settings first.')
        return redirect('accounts:ldap_configuration')

    if request.method == 'POST':
        field_form = LDAPSyncComputerFieldSelectionForm(request.POST, prefix='fields')
        password_form = LDAPBindPasswordForm(request.POST, prefix='password')
        
        if field_form.is_valid() and password_form.is_valid():
            bind_password = password_form.cleaned_data['bind_password']
            
            # Get selected fields
            selected_fields = {
                key: value for key, value in field_form.cleaned_data.items() 
                if value is True
            }
            
            messages.info(request, f'Starting computer sync with {len(selected_fields)} fields...')
            result = LDAPComputerSync.sync_all_computers(ldap_config, bind_password=bind_password, selected_fields=selected_fields)
            
            # Clear session (just in case)
            if 'ldap_sync_computer_fields' in request.session:
                del request.session['ldap_sync_computer_fields']
            
            if result.get('success'):
                messages.success(request, f"✓ {result.get('message')}")
            else:
                messages.error(request, f"✗ Computer sync failed: {result.get('message')}")
            
            return redirect('accounts:ldap_configuration')
    else:
        field_form = LDAPSyncComputerFieldSelectionForm(prefix='fields')
        password_form = LDAPBindPasswordForm(prefix='password')
    
    return render(request, 'accounts/ldap_sync_computer_fields.html', {
        'field_form': field_form,
        'password_form': password_form,
        'ldap_config': ldap_config,
    })

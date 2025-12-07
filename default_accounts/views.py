from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from openpyxl import Workbook

from systems.models import System

from .forms import (
    DefaultAccountActionForm,
    DefaultAccountForm,
    DefaultAccountTemplateForm,
)
from .models import (
    DefaultAccount,
    DefaultAccountAction,
    DefaultAccountTemplate,
)
from .services import create_default_accounts_for_system, ensure_default_account_templates_seeded


@login_required
def default_account_dashboard(request):
    """
    Dashboard + registry list for default accounts (PCI 4.7 evidence).
    """
    ensure_default_account_templates_seeded()
    accounts = DefaultAccount.objects.select_related(
        'system',
        'password_changed_by',
        'removal_confirmed_by',
        'installation_documented_by',
        'last_verified_by',
        'created_by',
        'updated_by',
    )

    search_query = request.GET.get('search', '').strip()
    if search_query:
        accounts = accounts.filter(
            Q(account_name__icontains=search_query)
            | Q(system__name__icontains=search_query)
            | Q(remediation_notes__icontains=search_query)
            | Q(password_change_reference__icontains=search_query)
            | Q(removal_reference__icontains=search_query)
        )

    system_filter = request.GET.get('system', '')
    if system_filter:
        accounts = accounts.filter(system_id=system_filter)

    status_filter = request.GET.get('status', '')
    if status_filter:
        accounts = accounts.filter(status=status_filter)

    account_type_filter = request.GET.get('account_type', '')
    if account_type_filter:
        accounts = accounts.filter(account_type=account_type_filter)

    attention_filter = request.GET.get('attention', '')
    if attention_filter == 'needs_action':
        accounts = accounts.requiring_attention()
    elif attention_filter == 'rhg_special':
        accounts = accounts.filter(is_rhg_special_account=True)
    elif attention_filter == 'hosted_na':
        accounts = accounts.filter(status='Not Applicable')

    ordering = request.GET.get('ordering', 'system__name')
    accounts = accounts.order_by(ordering, 'account_name')

    paginator = Paginator(accounts, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Stats for summary cards
    base_qs = DefaultAccount.objects.all()
    stats = {
        'total': base_qs.count(),
        'pending': base_qs.filter(status='Pending').count(),
        'removed': base_qs.filter(status='Removed').count(),
        'password_changed': base_qs.filter(status='Active - Password Changed').count(),
        'not_applicable': base_qs.filter(status='Not Applicable').count(),
        'needs_attention': base_qs.requiring_attention().count(),
        'rhg_special': base_qs.filter(is_rhg_special_account=True).count(),
    }

    systems = System.objects.filter(is_active=True).order_by('name')
    template_count = DefaultAccountTemplate.objects.count()

    query_params = request.GET.copy()
    query_params.pop('page', None)

    status_choices = DefaultAccount._meta.get_field('status').choices
    account_type_choices = DefaultAccount._meta.get_field('account_type').choices

    context = {
        'page_obj': page_obj,
        'accounts': page_obj,
        'stats': stats,
        'search_query': search_query,
        'system_filter': system_filter,
        'status_filter': status_filter,
        'account_type_filter': account_type_filter,
        'attention_filter': attention_filter,
        'ordering': ordering,
        'systems': systems,
        'template_count': template_count,
        'query_string': query_params.urlencode(),
        'status_choices': status_choices,
        'account_type_choices': account_type_choices,
    }
    return render(request, 'default_accounts/default_account_dashboard.html', context)


@login_required
def default_account_detail(request, pk):
    account = get_object_or_404(
        DefaultAccount.objects.select_related(
            'system',
            'password_changed_by',
            'removal_confirmed_by',
            'installation_documented_by',
            'last_verified_by',
            'created_by',
            'updated_by',
        ),
        pk=pk,
    )
    actions = account.actions.select_related('performed_by').order_by('-action_date')
    action_form = DefaultAccountActionForm()
    context = {
        'account': account,
        'actions': actions,
        'action_form': action_form,
    }
    return render(request, 'default_accounts/default_account_detail.html', context)


@login_required
def default_account_create(request):
    if request.method == 'POST':
        form = DefaultAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.created_by = request.user
            account.updated_by = request.user
            account.save()
            messages.success(request, 'Default account added to registry.')
            return redirect('default_accounts:default_account_detail', pk=account.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = DefaultAccountForm()
    return render(request, 'default_accounts/default_account_form.html', {'form': form, 'action': 'Create'})


@login_required
def default_account_update(request, pk):
    account = get_object_or_404(DefaultAccount, pk=pk)
    if request.method == 'POST':
        form = DefaultAccountForm(request.POST, instance=account)
        if form.is_valid():
            updated_account = form.save(commit=False)
            updated_account.updated_by = request.user
            updated_account.updated_at = timezone.now()
            updated_account.save()
            messages.success(request, 'Default account updated.')
            return redirect('default_accounts:default_account_detail', pk=account.pk)
        messages.error(request, 'Please correct the errors below.')
    else:
        form = DefaultAccountForm(instance=account)
    return render(
        request,
        'default_accounts/default_account_form.html',
        {'form': form, 'action': 'Update', 'account': account},
    )


@login_required
def default_account_delete(request, pk):
    account = get_object_or_404(DefaultAccount, pk=pk)
    if request.method == 'POST':
        account_name = account.account_name
        account.delete()
        messages.success(request, f'Default account "{account_name}" was deleted from registry.')
        return redirect('default_accounts:default_account_dashboard')
    return render(request, 'default_accounts/default_account_confirm_delete.html', {'account': account})


@login_required
def default_account_log_action(request, pk):
    account = get_object_or_404(DefaultAccount, pk=pk)
    if request.method == 'POST':
        form = DefaultAccountActionForm(request.POST)
        if form.is_valid():
            action: DefaultAccountAction = form.save(commit=False)
            action.default_account = account
            action.performed_by = request.user
            action.save()
            messages.success(request, 'Action logged and registry updated.')
        else:
            messages.error(request, 'Unable to log action. Please fix the highlighted fields.')
        return redirect('default_accounts:default_account_detail', pk=pk)
    else:
        form = DefaultAccountActionForm(initial={'action_date': timezone.now()})
    return render(
        request,
        'default_accounts/default_account_action_form.html',
        {'form': form, 'account': account},
    )


@login_required
def default_account_export(request):
    """Export current registry to Excel for auditors."""
    accounts = DefaultAccount.objects.select_related(
        'system',
        'password_changed_by',
        'removal_confirmed_by',
        'installation_documented_by',
        'last_verified_by',
    ).order_by('system__name', 'account_name')

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Default Accounts"
    headers = [
        "System",
        "Account Name",
        "Account Type",
        "Status",
        "Removal Required",
        "Password Changed",
        "Password Changed Date",
        "Password Changed By",
        "Password Evidence",
        "Removed",
        "Removal Date",
        "Removal Confirmed By",
        "Removal Evidence",
        "Installation Checklist",
        "Installation Date",
        "Installation Documented By",
        "Verification Date",
        "Verification By",
        "Verification Artifact",
        "Hosted N/A Reason",
        "RHG Special",
        "Last Updated",
    ]
    worksheet.append(headers)

    for account in accounts:
        worksheet.append([
            account.system.name,
            account.account_name,
            account.get_account_type_display(),
            account.status,
            "Yes" if account.removal_required else "No",
            "Yes" if account.password_changed_in_external_system else "No",
            account.password_changed_date.strftime('%Y-%m-%d %H:%M') if account.password_changed_date else '',
            account.password_changed_by.full_name if account.password_changed_by else '',
            account.password_change_reference,
            "Yes" if account.removed_from_external_system else "No",
            account.removal_date.strftime('%Y-%m-%d %H:%M') if account.removal_date else '',
            account.removal_confirmed_by.full_name if account.removal_confirmed_by else '',
            account.removal_reference,
            "Yes" if account.installation_checklist_completed else "No",
            account.installation_checklist_completed_date.strftime('%Y-%m-%d %H:%M') if account.installation_checklist_completed_date else '',
            account.installation_documented_by.full_name if account.installation_documented_by else '',
            account.last_verified_date.strftime('%Y-%m-%d %H:%M') if account.last_verified_date else '',
            account.last_verified_by.full_name if account.last_verified_by else '',
            account.verification_artifact,
            account.hosted_not_applicable_reason,
            "Yes" if account.is_rhg_special_account else "No",
            account.updated_at.strftime('%Y-%m-%d %H:%M'),
        ])

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)

    response = HttpResponse(
        stream.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = 'attachment; filename="default_accounts_registry.xlsx"'
    return response


@login_required
def seed_defaults_for_system(request, system_id):
    system = get_object_or_404(System, pk=system_id)
    result = create_default_accounts_for_system(system, created_by=request.user)
    if result.created_count:
        messages.success(
            request,
            f'{result.created_count} default account{"s" if result.created_count != 1 else ""} created for {system.name}.',
        )
    else:
        messages.info(request, f'No new default accounts were created for {system.name} (already tracked).')
    return redirect('default_accounts:default_account_dashboard')


@login_required
def default_account_template_list(request):
    ensure_default_account_templates_seeded()
    templates = DefaultAccountTemplate.objects.all().order_by('system_type', 'account_name')
    
    # Check if editing a specific template
    edit_id = request.GET.get('edit')
    editing_template = None
    if edit_id:
        try:
            editing_template = DefaultAccountTemplate.objects.get(pk=edit_id)
        except DefaultAccountTemplate.DoesNotExist:
            pass
    
    if request.method == 'POST':
        template_id = request.POST.get('template_id')
        if template_id:
            # Editing existing template
            template_instance = get_object_or_404(DefaultAccountTemplate, pk=template_id)
            form = DefaultAccountTemplateForm(request.POST, instance=template_instance)
        else:
            # Creating new template
            form = DefaultAccountTemplateForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Template saved. Future systems will inherit the updated registry.')
            return redirect('default_accounts:default_account_templates')
        messages.error(request, 'Please correct the errors below.')
    else:
        if editing_template:
            form = DefaultAccountTemplateForm(instance=editing_template)
        else:
            form = DefaultAccountTemplateForm()

    template_stats = templates.aggregate(
        total=Count('id'),
        rhg=Count('id', filter=Q(rhg_special_account=True)),
        global_templates=Count('id', filter=Q(applies_to_all=True)),
    )
    return render(
        request,
        'default_accounts/default_account_templates.html',
        {
            'templates': templates,
            'form': form,
            'template_stats': template_stats,
            'editing_template': editing_template,
        },
    )


@login_required
def default_account_template_update(request, pk):
    """Update an existing template."""
    template = get_object_or_404(DefaultAccountTemplate, pk=pk)
    if request.method == 'POST':
        form = DefaultAccountTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template updated. Future systems will inherit the updated registry.')
            return redirect('default_accounts:default_account_templates')
        messages.error(request, 'Please correct the errors below.')
    else:
        form = DefaultAccountTemplateForm(instance=template)
    
    return render(
        request,
        'default_accounts/default_account_templates.html',
        {
            'templates': DefaultAccountTemplate.objects.all().order_by('system_type', 'account_name'),
            'form': form,
            'editing_template': template,
            'template_stats': DefaultAccountTemplate.objects.aggregate(
                total=Count('id'),
                rhg=Count('id', filter=Q(rhg_special_account=True)),
                global_templates=Count('id', filter=Q(applies_to_all=True)),
            ),
        },
    )


@login_required
def default_account_template_delete(request, pk):
    """Delete a template."""
    template = get_object_or_404(DefaultAccountTemplate, pk=pk)
    if request.method == 'POST':
        template_name = template.account_name
        template.delete()
        messages.success(request, f'Template "{template_name}" was deleted.')
        return redirect('default_accounts:default_account_templates')
    return render(request, 'default_accounts/default_account_template_confirm_delete.html', {'template': template})

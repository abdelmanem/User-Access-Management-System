from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta

from .models import UserSystemAccess, AccessHistory
from accounts.models import CustomUser
from systems.models import System


@login_required
def access_assignment_list(request):
    """List all access assignments with filtering and search"""
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    access_type_filter = request.GET.get('access_type', '')
    system_filter = request.GET.get('system', '')
    user_filter = request.GET.get('user', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    queryset = UserSystemAccess.objects.select_related('user', 'system', 'approved_by').all()
    
    # Apply filters
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if priority_filter:
        queryset = queryset.filter(priority=priority_filter)
    if access_type_filter:
        queryset = queryset.filter(access_type=access_type_filter)
    if system_filter:
        queryset = queryset.filter(system_id=system_filter)
    if user_filter:
        queryset = queryset.filter(user_id=user_filter)
    if search_query:
        queryset = queryset.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(system__name__icontains=search_query) |
            Q(business_justification__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    access_assignments = paginator.get_page(page_number)
    
    # Get filter options
    systems = System.objects.all().order_by('name')
    users = CustomUser.objects.all().order_by('first_name', 'last_name')
    
    context = {
        'access_assignments': access_assignments,
        'status_choices': UserSystemAccess.STATUS_CHOICES,
        'priority_choices': UserSystemAccess.PRIORITY_CHOICES,
        'access_type_choices': UserSystemAccess.ACCESS_TYPE_CHOICES,
        'systems': systems,
        'users': users,
        'filters': {
            'status': status_filter,
            'priority': priority_filter,
            'access_type': access_type_filter,
            'system': system_filter,
            'user': user_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'access_management/access_assignment_list.html', context)


@login_required
def access_assignment_detail(request, pk):
    """Detail view of an access assignment"""
    access_assignment = get_object_or_404(
        UserSystemAccess.objects.select_related('user', 'system', 'approved_by', 'requested_by'),
        pk=pk
    )
    
    # Get recent access history
    access_history = AccessHistory.objects.filter(
        user_system_access=access_assignment
    ).select_related('user', 'system').order_by('-accessed_at')[:10]
    
    context = {
        'access_assignment': access_assignment,
        'access_history': access_history,
    }
    
    return render(request, 'access_management/access_assignment_detail.html', context)


@login_required
def access_assignment_create(request):
    """Create a new access assignment"""
    
    if request.method == 'POST':
        user_id = request.POST.get('user')
        system_id = request.POST.get('system')
        access_type = request.POST.get('access_type')
        request_type = request.POST.get('request_type')
        priority = request.POST.get('priority')
        business_justification = request.POST.get('business_justification')
        requested_access_duration = request.POST.get('requested_access_duration')
        technical_requirements = request.POST.get('technical_requirements')
        access_start_date = request.POST.get('access_start_date')
        access_end_date = request.POST.get('access_end_date')
        
        try:
            user = CustomUser.objects.get(id=user_id)
            system = System.objects.get(id=system_id)
            
            # Check if access already exists
            if UserSystemAccess.objects.filter(user=user, system=system).exists():
                messages.error(request, f'Access assignment for {user.full_name} to {system.name} already exists.')
                return redirect('access_management:access_assignment_create')
            
            # Create new access assignment
            access_assignment = UserSystemAccess.objects.create(
                user=user,
                system=system,
                access_type=access_type,
                request_type=request_type or 'New Access',
                priority=priority,
                business_justification=business_justification,
                requested_access_duration=int(requested_access_duration) if requested_access_duration else None,
                technical_requirements=technical_requirements,
                access_start_date=timezone.datetime.fromisoformat(access_start_date) if access_start_date else None,
                access_end_date=timezone.datetime.fromisoformat(access_end_date) if access_end_date else None,
                requested_by=request.user,
                created_by=request.user,
                updated_by=request.user
            )
            
            # Create access history entry
            AccessHistory.objects.create(
                user=user,
                system=system,
                user_system_access=access_assignment,
                action='Requested',
                action_description=f'Access requested by {request.user.full_name}',
                created_by=request.user
            )
            
            messages.success(request, f'Access assignment created successfully for {user.full_name} to {system.name}.')
            return redirect('access_management:access_assignment_detail', pk=access_assignment.pk)
            
        except (CustomUser.DoesNotExist, System.DoesNotExist):
            messages.error(request, 'Invalid user or system selected.')
        except Exception as e:
            messages.error(request, f'Error creating access assignment: {str(e)}')
    
    # Get data for form
    systems = System.objects.all().order_by('name')
    users = CustomUser.objects.all().order_by('first_name', 'last_name')
    selected_user_id = (request.POST.get('user') if request.method == 'POST' else None) or ''
    selected_system_id = (request.POST.get('system') if request.method == 'POST' else None) or (request.GET.get('system') or '')
    selected_access_type = (request.POST.get('access_type') if request.method == 'POST' else '') or ''
    selected_request_type = (request.POST.get('request_type') if request.method == 'POST' else '') or ''
    selected_priority = (request.POST.get('priority') if request.method == 'POST' else '') or ''
    
    context = {
        'systems': systems,
        'users': users,
        'access_type_choices': UserSystemAccess.ACCESS_TYPE_CHOICES,
        'request_type_choices': UserSystemAccess.REQUEST_TYPE_CHOICES,
        'priority_choices': UserSystemAccess.PRIORITY_CHOICES,
        'selected_user_id': str(selected_user_id),
        'selected_system_id': str(selected_system_id),
        'selected_access_type': selected_access_type,
        'selected_request_type': selected_request_type,
        'selected_priority': selected_priority,
        'business_justification_value': request.POST.get('business_justification', ''),
    }
    
    return render(request, 'access_management/access_assignment_form.html', context)


@login_required
def access_assignment_update(request, pk):
    """Update an existing access assignment"""
    access_assignment = get_object_or_404(UserSystemAccess, pk=pk)
    
    if request.method == 'POST':
        access_type = request.POST.get('access_type')
        request_type = request.POST.get('request_type')
        priority = request.POST.get('priority')
        business_justification = request.POST.get('business_justification')
        technical_requirements = request.POST.get('technical_requirements')
        requested_access_duration = request.POST.get('requested_access_duration')
        access_start_date = request.POST.get('access_start_date')
        access_end_date = request.POST.get('access_end_date')
        status = request.POST.get('status') or access_assignment.status
        
        try:
            # Update fields
            access_assignment.access_type = access_type
            access_assignment.request_type = request_type or access_assignment.request_type
            access_assignment.priority = priority
            access_assignment.business_justification = business_justification
            access_assignment.technical_requirements = technical_requirements
            access_assignment.requested_access_duration = int(requested_access_duration) if requested_access_duration else None
            access_assignment.access_start_date = timezone.datetime.fromisoformat(access_start_date) if access_start_date else None
            access_assignment.access_end_date = timezone.datetime.fromisoformat(access_end_date) if access_end_date else None
            access_assignment.status = status
            access_assignment.updated_by = request.user
            
            access_assignment.save()
            
            # Create access history entry
            AccessHistory.objects.create(
                user=access_assignment.user,
                system=access_assignment.system,
                user_system_access=access_assignment,
                action='Modified',
                action_description=f'Access modified by {request.user.full_name}',
                created_by=request.user
            )
            
            messages.success(request, 'Access assignment updated successfully.')
            return redirect('access_management:access_assignment_detail', pk=access_assignment.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating access assignment: {str(e)}')
    
    context = {
        'access_assignment': access_assignment,
        # dropdown choices
        'access_type_choices': UserSystemAccess.ACCESS_TYPE_CHOICES,
        'request_type_choices': UserSystemAccess.REQUEST_TYPE_CHOICES,
        'priority_choices': UserSystemAccess.PRIORITY_CHOICES,
        'status_choices': UserSystemAccess.STATUS_CHOICES,
        # pre-selected values for template
        'selected_user_id': str(access_assignment.user_id),
        'selected_system_id': str(access_assignment.system_id),
        'selected_access_type': access_assignment.access_type,
        'selected_request_type': access_assignment.request_type,
        'selected_priority': access_assignment.priority,
        # lists
        'users': CustomUser.objects.all().order_by('first_name', 'last_name'),
        'systems': System.objects.all().order_by('name'),
        'business_justification_value': request.POST.get('business_justification', access_assignment.business_justification or ''),
    }
    
    return render(request, 'access_management/access_assignment_form.html', context)


@login_required
def access_assignment_delete(request, pk):
    """Delete an access assignment"""
    access_assignment = get_object_or_404(UserSystemAccess, pk=pk)
    
    if request.method == 'POST':
        try:
            # Create access history entry before deletion
            AccessHistory.objects.create(
                user=access_assignment.user,
                system=access_assignment.system,
                action='Revoked',
                action_description=f'Access revoked by {request.user.full_name}',
                created_by=request.user
            )
            
            access_assignment.delete()
            messages.success(request, 'Access assignment deleted successfully.')
            return redirect('access_management:access_assignment_list')
            
        except Exception as e:
            messages.error(request, f'Error deleting access assignment: {str(e)}')
    
    context = {
        'access_assignment': access_assignment,
    }
    
    return render(request, 'access_management/access_assignment_confirm_delete.html', context)


@login_required
def user_access_assignments(request, user_id):
    """View and manage access assignments for a specific user"""
    user = get_object_or_404(CustomUser, pk=user_id)
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    system_filter = request.GET.get('system', '')
    
    # Base queryset
    queryset = UserSystemAccess.objects.select_related('system').filter(user=user)
    
    # Apply filters
    if status_filter and status_filter.lower() != 'all':
        queryset = queryset.filter(status__iexact=status_filter)
    if system_filter:
        queryset = queryset.filter(system_id=system_filter)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_assignments')
        action = request.POST.get('bulk_action')

        if not selected_ids:
            messages.error(request, 'Select at least one assignment to perform bulk actions.')
            return redirect(request.get_full_path())

        assignments = UserSystemAccess.objects.filter(pk__in=selected_ids, user=user)

        if action == 'bulk_delete':
            deleted = 0
            for assignment in assignments:
                AccessHistory.objects.create(
                    user=assignment.user,
                    system=assignment.system,
                    action='Revoked',
                    action_description=f'Access revoked in bulk by {request.user.full_name}',
                    created_by=request.user
                )
                assignment.delete()
                deleted += 1

            messages.success(request, f'Successfully deleted {deleted} access assignment{"s" if deleted != 1 else ""}.')
            return redirect(request.path_info)

        if action == 'bulk_update':
            new_status = request.POST.get('bulk_status', '')
            new_priority = request.POST.get('bulk_priority', '')
            new_access_type = request.POST.get('bulk_access_type', '')

            if not any([new_status, new_priority, new_access_type]):
                messages.error(request, 'Choose at least one field to update when performing a bulk edit.')
                return redirect(request.get_full_path())

            updated = 0
            for assignment in assignments:
                changes = []
                if new_status:
                    assignment.status = new_status
                    changes.append(f"status → {new_status}")
                if new_priority:
                    assignment.priority = new_priority
                    changes.append(f"priority → {new_priority}")
                if new_access_type:
                    assignment.access_type = new_access_type
                    changes.append(f"access type → {new_access_type}")

                if changes:
                    assignment.updated_by = request.user
                    assignment.save()
                    AccessHistory.objects.create(
                        user=assignment.user,
                        system=assignment.system,
                        user_system_access=assignment,
                        action='Modified',
                        action_description=f"Bulk update by {request.user.full_name}: {', '.join(changes)}",
                        created_by=request.user
                    )
                    updated += 1

            messages.success(request, f'Successfully updated {updated} access assignment{"s" if updated != 1 else ""}.')
            return redirect(request.get_full_path())

        messages.error(request, 'Unsupported bulk action.')
        return redirect(request.get_full_path())
    
    # Pagination
    paginator = Paginator(queryset.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    access_assignments = paginator.get_page(page_number)
    
    # Summary metrics
    total_assignments = queryset.count()
    active_assignments = queryset.filter(status='Active').count()
    pending_assignments = queryset.filter(status='Pending').count()
    unique_systems = queryset.values('system_id').distinct().count()
    
    # Get user's systems for filter
    user_systems = System.objects.filter(
        user_accesses__user=user
    ).distinct().order_by('name')
    
    context = {
        'user': user,
        'access_assignments': access_assignments,
        'status_choices': UserSystemAccess.STATUS_CHOICES,
        'priority_choices': UserSystemAccess.PRIORITY_CHOICES,
        'access_type_choices': UserSystemAccess.ACCESS_TYPE_CHOICES,
        'systems': user_systems,
        'filters': {
            'status': status_filter,
            'system': system_filter,
        },
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'pending_assignments': pending_assignments,
        'unique_systems': unique_systems,
        'is_paginated': access_assignments.has_other_pages(),
        'page_obj': access_assignments,
    }
    
    return render(request, 'access_management/user_access_assignments.html', context)


@login_required
def system_access_assignments(request, system_id):
    """View and manage access assignments for a specific system"""
    system = get_object_or_404(System, pk=system_id)
    
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    access_type_filter = request.GET.get('access_type', '')
    
    # Base queryset
    queryset = UserSystemAccess.objects.select_related('user').filter(system=system)
    
    # Apply filters
    if status_filter and status_filter.lower() != 'all':
        queryset = queryset.filter(status__iexact=status_filter)
    if access_type_filter:
        queryset = queryset.filter(access_type=access_type_filter)

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_assignments')
        action = request.POST.get('bulk_action')

        if not selected_ids:
            messages.error(request, 'Select at least one assignment to perform bulk actions.')
            return redirect(request.get_full_path())

        assignments = UserSystemAccess.objects.filter(pk__in=selected_ids, system=system)

        if action == 'bulk_delete':
            deleted = 0
            for assignment in assignments:
                AccessHistory.objects.create(
                    user=assignment.user,
                    system=assignment.system,
                    action='Revoked',
                    action_description=f'Access revoked in bulk by {request.user.full_name}',
                    created_by=request.user
                )
                assignment.delete()
                deleted += 1

            messages.success(request, f'Successfully deleted {deleted} access assignment{"s" if deleted != 1 else ""}.')
            return redirect(request.path_info)

        if action == 'bulk_update':
            new_status = request.POST.get('bulk_status', '')
            new_priority = request.POST.get('bulk_priority', '')
            new_access_type = request.POST.get('bulk_access_type', '')

            if not any([new_status, new_priority, new_access_type]):
                messages.error(request, 'Choose at least one field to update when performing a bulk edit.')
                return redirect(request.get_full_path())

            updated = 0
            for assignment in assignments:
                changes = []
                if new_status:
                    assignment.status = new_status
                    changes.append(f"status → {new_status}")
                if new_priority:
                    assignment.priority = new_priority
                    changes.append(f"priority → {new_priority}")
                if new_access_type:
                    assignment.access_type = new_access_type
                    changes.append(f"access type → {new_access_type}")

                if changes:
                    assignment.updated_by = request.user
                    assignment.save()
                    AccessHistory.objects.create(
                        user=assignment.user,
                        system=assignment.system,
                        user_system_access=assignment,
                        action='Modified',
                        action_description=f"Bulk update by {request.user.full_name}: {', '.join(changes)}",
                        created_by=request.user
                    )
                    updated += 1

            messages.success(request, f'Successfully updated {updated} access assignment{"s" if updated != 1 else ""}.')
            return redirect(request.get_full_path())

        messages.error(request, 'Unsupported bulk action.')
        return redirect(request.get_full_path())
    
    # Pagination
    paginator = Paginator(queryset.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    access_assignments = paginator.get_page(page_number)
    
    # Summary metrics
    total_assignments = queryset.count()
    active_assignments = queryset.filter(status='Active').count()
    pending_assignments = queryset.filter(status='Pending').count()
    unique_users = queryset.values('user_id').distinct().count()
    
    context = {
        'system': system,
        'access_assignments': access_assignments,
        'status_choices': UserSystemAccess.STATUS_CHOICES,
        'priority_choices': UserSystemAccess.PRIORITY_CHOICES,
        'access_type_choices': UserSystemAccess.ACCESS_TYPE_CHOICES,
        'filters': {
            'status': status_filter,
            'access_type': access_type_filter,
        },
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'pending_assignments': pending_assignments,
        'unique_users': unique_users,
        'access_levels': {
            (item['granted_access_level'] or 'Unspecified'): item['count']
            for item in queryset.values('granted_access_level').annotate(count=Count('id')).order_by('granted_access_level')
        },
        'is_paginated': access_assignments.has_other_pages(),
        'page_obj': access_assignments,
    }
    
    return render(request, 'access_management/system_access_assignments.html', context)


@login_required
def approve_access_assignment(request, pk):
    """Approve an access assignment"""
    access_assignment = get_object_or_404(UserSystemAccess, pk=pk)
    
    if request.method == 'POST':
        comments = request.POST.get('approval_comments', '')
        
        try:
            access_assignment.approve_access(request.user, comments)
            
            # Create access history entry
            AccessHistory.objects.create(
                user=access_assignment.user,
                system=access_assignment.system,
                user_system_access=access_assignment,
                action='Approved',
                action_description=f'Access approved by {request.user.full_name}',
                created_by=request.user
            )
            
            messages.success(request, f'Access assignment approved for {access_assignment.user.full_name}.')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error approving access assignment: {str(e)}')
    
    return redirect('access_management:access_assignment_detail', pk=pk)


@login_required
def reject_access_assignment(request, pk):
    """Reject an access assignment"""
    access_assignment = get_object_or_404(UserSystemAccess, pk=pk)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        
        if not rejection_reason:
            messages.error(request, 'Rejection reason is required.')
            return redirect('access_management:access_assignment_detail', pk=pk)
        
        try:
            access_assignment.reject_access(request.user, rejection_reason)
            
            # Create access history entry
            AccessHistory.objects.create(
                user=access_assignment.user,
                system=access_assignment.system,
                user_system_access=access_assignment,
                action='Rejected',
                action_description=f'Access rejected by {request.user.full_name}',
                created_by=request.user
            )
            
            messages.success(request, f'Access assignment rejected for {access_assignment.user.full_name}.')
            
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Error rejecting access assignment: {str(e)}')
    
    return redirect('access_management:access_assignment_detail', pk=pk)


@login_required
def access_history_list(request):
    """List all access history events"""
    
    # Get filter parameters
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    system_filter = request.GET.get('system', '')
    success_filter = request.GET.get('success', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    queryset = AccessHistory.objects.select_related('user', 'system', 'user_system_access').all()
    
    # Apply filters
    if action_filter:
        queryset = queryset.filter(action=action_filter)
    if user_filter:
        queryset = queryset.filter(user_id=user_filter)
    if system_filter:
        queryset = queryset.filter(system_id=system_filter)
    if success_filter:
        queryset = queryset.filter(success=success_filter.lower() == 'true')
    if search_query:
        queryset = queryset.filter(
            Q(user__username__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(system__name__icontains=search_query) |
            Q(action_description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    access_history = paginator.get_page(page_number)
    
    # Get filter options
    systems = System.objects.all().order_by('name')
    users = CustomUser.objects.all().order_by('first_name', 'last_name')
    
    context = {
        'access_history': access_history,
        'action_choices': AccessHistory.ACTION_CHOICES,
        'systems': systems,
        'users': users,
        'filters': {
            'action': action_filter,
            'user': user_filter,
            'system': system_filter,
            'success': success_filter,
            'search': search_query,
        }
    }
    
    return render(request, 'access_management/access_history_list.html', context)


@login_required
def user_access_history(request, user_id):
    """Display access history for a specific user."""
    user = get_object_or_404(CustomUser, pk=user_id)
    queryset = AccessHistory.objects.filter(user=user).select_related('system').order_by('-timestamp')
    
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    access_history = paginator.get_page(page_number)
    
    context = {
        'access_history': access_history,
        'user': user,
        'title': f'Access History for {user.get_full_name()}',
    }
    
    return render(request, 'access_management/access_history_list.html', context)


@login_required
def system_access_history(request, system_id):
    """Display access history for a specific system."""
    system = get_object_or_404(System, pk=system_id)
    queryset = AccessHistory.objects.filter(system=system).select_related('user').order_by('-timestamp')
    
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    access_history = paginator.get_page(page_number)
    
    context = {
        'access_history': access_history,
        'system': system,
        'title': f'Access History for {system.name}',
    }
    
    return render(request, 'access_management/access_history_list.html', context)


@login_required
def assignment_access_history(request, assignment_id):
    """Display access history for a specific assignment."""
    assignment = get_object_or_404(UserSystemAccess, pk=assignment_id)
    queryset = AccessHistory.objects.filter(user_system_access=assignment).select_related('user', 'system').order_by('-timestamp')
    
    paginator = Paginator(queryset, 50)
    page_number = request.GET.get('page')
    access_history = paginator.get_page(page_number)
    
    context = {
        'access_history': access_history,
        'assignment': assignment,
        'title': f'Access History for Assignment {assignment.id}',
    }
    
    return render(request, 'access_management/access_history_list.html', context)

"""
Global search views for the User Access Management System.
Provides unified search functionality across all models.
"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse

from django.contrib.auth import get_user_model

User = get_user_model()
from departments.models import Department
from systems.models import System
from access_management.models import UserSystemAccess, AccessHistory


@login_required
def global_search(request):
    """
    Global search across all models in the system.
    
    Returns search results from users, departments, systems, and access records.
    """
    query = request.GET.get('q', '').strip()
    result_type = request.GET.get('type', 'all')
    
    if not query or len(query) < 2:
        return render(request, 'admin/search/global_search.html', {
            'query': query,
            'results': {},
            'result_type': result_type,
            'show_results': False
        })
    
    results = {}
    
    # Search Users
    if result_type in ['all', 'users']:
        user_results = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(department__name__icontains=query)
        ).select_related('department')[:10]
        
        results['users'] = {
            'items': user_results,
            'count': user_results.count(),
            'total': User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(department__name__icontains=query)
            ).count()
        }
    
    # Search Departments
    if result_type in ['all', 'departments']:
        dept_results = Department.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(code__icontains=query)
        )[:10]
        
        results['departments'] = {
            'items': dept_results,
            'count': dept_results.count(),
            'total': Department.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(code__icontains=query)
            ).count()
        }
    
    # Search Systems
    if result_type in ['all', 'systems']:
        system_results = System.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(system_type__icontains=query) |
            Q(department__name__icontains=query)
        ).select_related('department')[:10]
        
        results['systems'] = {
            'items': system_results,
            'count': system_results.count(),
            'total': System.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(system_type__icontains=query) |
                Q(department__name__icontains=query)
            ).count()
        }
    
    # Search Access Assignments
    if result_type in ['all', 'access']:
        access_results = UserSystemAccess.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(system__name__icontains=query) |
            Q(business_justification__icontains=query)
        ).select_related('user', 'system')[:10]
        
        results['access'] = {
            'items': access_results,
            'count': access_results.count(),
            'total': UserSystemAccess.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(system__name__icontains=query) |
                Q(business_justification__icontains=query)
            ).count()
        }
    
    # Search Access History
    if result_type in ['all', 'history']:
        history_results = AccessHistory.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(system__name__icontains=query) |
            Q(action__icontains=query) |
            Q(action_description__icontains=query) |
            Q(ip_address__icontains=query)
        ).select_related('user', 'system')[:10]
        
        results['history'] = {
            'items': history_results,
            'count': history_results.count(),
            'total': AccessHistory.objects.filter(
                Q(user__username__icontains=query) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(system__name__icontains=query) |
                Q(action__icontains=query) |
                Q(action_description__icontains=query) |
                Q(ip_address__icontains=query)
            ).count()
        }
    
    return render(request, 'admin/search/global_search.html', {
        'query': query,
        'results': results,
        'result_type': result_type,
        'show_results': True
    })


@login_required
def search_suggestions(request):
    """
    AJAX endpoint for search suggestions/autocomplete.
    
    Returns JSON response with search suggestions based on query.
    """
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    
    # User suggestions
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    )[:5]
    
    for user in users:
        suggestions.append({
            'type': 'user',
            'value': f"{user.username} - {user.get_full_name()}",
            'url': f"/admin/accounts/user/{user.id}/change/",
            'icon': 'fas fa-user'
        })
    
    # System suggestions
    systems = System.objects.filter(
        Q(name__icontains=query) |
        Q(description__icontains=query)
    )[:5]
    
    for system in systems:
        suggestions.append({
            'type': 'system',
            'value': system.name,
            'url': f"/admin/systems/system/{system.id}/change/",
            'icon': 'fas fa-server'
        })
    
    # Department suggestions
    departments = Department.objects.filter(
        Q(name__icontains=query) |
        Q(code__icontains=query)
    )[:5]
    
    for dept in departments:
        suggestions.append({
            'type': 'department',
            'value': dept.name,
            'url': f"/admin/departments/department/{dept.id}/change/",
            'icon': 'fas fa-building'
        })
    
    return JsonResponse({'suggestions': suggestions})


@login_required
def advanced_search(request):
    """
    Advanced search interface with detailed filtering options.
    """
    return render(request, 'admin/search/advanced_search.html', {
        'search_types': [
            {'value': 'users', 'label': 'Users', 'icon': 'fas fa-users'},
            {'value': 'systems', 'label': 'Systems', 'icon': 'fas fa-server'},
            {'value': 'departments', 'label': 'Departments', 'icon': 'fas fa-building'},
            {'value': 'access', 'label': 'Access Assignments', 'icon': 'fas fa-key'},
            {'value': 'history', 'label': 'Access History', 'icon': 'fas fa-history'},
            {'value': 'all', 'label': 'All Types', 'icon': 'fas fa-search'}
        ]
    })
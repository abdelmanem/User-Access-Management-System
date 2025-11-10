"""
Search and filtering utilities for the User Access Management System.
Provides common search, filter, and pagination functionality.
"""

from django.db.models import Q
from django.core.paginator import Paginator
from django.http import QueryDict


class SearchFilter:
    """Generic search and filter utility for Django models."""
    
    def __init__(self, queryset, search_fields=None, filter_fields=None, date_fields=None):
        """
        Initialize the search filter.
        
        Args:
            queryset: Django QuerySet to filter
            search_fields: List of field names to search in
            filter_fields: Dict of field names and their filter types
            date_fields: List of date field names for date range filtering
        """
        self.queryset = queryset
        self.search_fields = search_fields or []
        self.filter_fields = filter_fields or {}
        self.date_fields = date_fields or []
    
    def apply_search(self, search_query):
        """Apply text search to the queryset."""
        if not search_query:
            return self.queryset
        
        q_objects = Q()
        for field in self.search_fields:
            if '__' in field:
                # Handle related field lookups
                q_objects |= Q(**{f"{field}__icontains": search_query})
            else:
                q_objects |= Q(**{f"{field}__icontains": search_query})
        
        return self.queryset.filter(q_objects)
    
    def apply_filters(self, filter_params):
        """Apply filters to the queryset."""
        queryset = self.queryset
        
        for field_name, filter_type in self.filter_fields.items():
            filter_value = filter_params.get(field_name)
            if filter_value:
                if filter_type == 'exact':
                    queryset = queryset.filter(**{field_name: filter_value})
                elif filter_type == 'icontains':
                    queryset = queryset.filter(**{f"{field_name}__icontains": filter_value})
                elif filter_type == 'gte':
                    queryset = queryset.filter(**{f"{field_name}__gte": filter_value})
                elif filter_type == 'lte':
                    queryset = queryset.filter(**{f"{field_name}__lte": filter_value})
                elif filter_type == 'in':
                    values = filter_value.split(',')
                    queryset = queryset.filter(**{f"{field_name}__in": values})
        
        return queryset
    
    def apply_date_range_filters(self, date_params):
        """Apply date range filters to the queryset."""
        queryset = self.queryset
        
        for field_name in self.date_fields:
            start_date = date_params.get(f"{field_name}_start")
            end_date = date_params.get(f"{field_name}_end")
            
            if start_date:
                queryset = queryset.filter(**{f"{field_name}__gte": start_date})
            
            if end_date:
                queryset = queryset.filter(**{f"{field_name}__lte": end_date})
        
        return queryset
    
    def apply_all(self, request_params):
        """Apply all search and filter operations."""
        queryset = self.queryset
        
        # Apply text search
        search_query = request_params.get('search', '')
        if search_query:
            queryset = self.apply_search(search_query)
        
        # Apply regular filters
        queryset = self.apply_filters(request_params)
        
        # Apply date range filters
        queryset = self.apply_date_range_filters(request_params)
        
        return queryset


def get_paginated_queryset(queryset, request, per_page=25):
    """
    Get paginated queryset with page number from request.
    
    Args:
        queryset: Django QuerySet to paginate
        request: Django request object
        per_page: Number of items per page
    
    Returns:
        Paginated queryset
    """
    page_number = request.GET.get('page', 1)
    paginator = Paginator(queryset, per_page)
    
    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1
    
    return paginator.get_page(page_number)


def get_filter_context(request, available_filters):
    """
    Get filter context for template rendering.
    
    Args:
        request: Django request object
        available_filters: Dict of available filter options
    
    Returns:
        Dict with current filters and available options
    """
    context = {
        'filters': {},
        'available_filters': available_filters
    }
    
    for key in request.GET.keys():
        if key != 'page':  # Skip pagination parameter
            context['filters'][key] = request.GET.get(key)
    
    return context


def build_filter_querystring(request, exclude_params=None):
    """
    Build querystring for pagination links while preserving filters.
    
    Args:
        request: Django request object
        exclude_params: List of parameter names to exclude
    
    Returns:
        Querystring for use in pagination links
    """
    exclude_params = exclude_params or []
    query_dict = QueryDict(mutable=True)
    
    for key, value in request.GET.items():
        if key not in exclude_params and key != 'page':
            query_dict[key] = value
    
    return query_dict.urlencode()


# Model-specific search configurations
ACCESS_ASSIGNMENT_SEARCH_FIELDS = [
    'user__username',
    'user__first_name',
    'user__last_name',
    'system__name',
    'system__description',
    'business_justification',
    'technical_requirements',
    'special_instructions'
]

ACCESS_ASSIGNMENT_FILTER_FIELDS = {
    'status': 'exact',
    'priority': 'exact',
    'access_type': 'exact',
    'system': 'exact',
    'user': 'exact',
    'request_type': 'exact'
}

ACCESS_ASSIGNMENT_DATE_FIELDS = [
    'request_date',
    'start_date',
    'end_date',
    'approval_date'
]

ACCESS_HISTORY_SEARCH_FIELDS = [
    'user__username',
    'user__first_name',
    'user__last_name',
    'system__name',
    'action',
    'action_description',
    'ip_address'
]

ACCESS_HISTORY_FILTER_FIELDS = {
    'action': 'exact',
    'user': 'exact',
    'system': 'exact',
    'success': 'exact'
}

ACCESS_HISTORY_DATE_FIELDS = [
    'timestamp'
]

USER_SEARCH_FIELDS = [
    'username',
    'first_name',
    'last_name',
    'email',
    'department__name',
    'role'
]

USER_FILTER_FIELDS = {
    'department': 'exact',
    'is_active': 'exact',
    'role': 'exact'
}

SYSTEM_SEARCH_FIELDS = [
    'name',
    'description',
    'system_type',
    'department__name'
]

SYSTEM_FILTER_FIELDS = {
    'system_type': 'exact',
    'department': 'exact',
    'is_active': 'exact',
    'security_level': 'exact'
}

DEPARTMENT_SEARCH_FIELDS = [
    'name',
    'description',
    'code'
]

DEPARTMENT_FILTER_FIELDS = {
    'is_active': 'exact',
    'parent_department': 'exact'
}
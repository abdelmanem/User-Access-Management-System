from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import CustomUser
from systems.models import System
from .models import AccountChangeRequest
from .serializers import (
    AccountChangeRequestListSerializer,
    AccountChangeRequestDetailSerializer,
    ChangeApprovalSerializer,
    ChangeWorkflowStatusSerializer,
    ChangeRequestStatisticsSerializer,
    BulkChangeRequestSerializer,
)

import logging

logger = logging.getLogger(__name__)


@login_required
def change_request_list(request):
    """
    List all account change requests with basic filtering and search.
    """
    status_filter = request.GET.get("status", "").strip()
    change_type_filter = request.GET.get("change_type", "").strip()
    system_filter = request.GET.get("system", "").strip()
    user_filter = request.GET.get("user", "").strip()
    search_query = request.GET.get("search", "").strip()

    queryset = AccountChangeRequest.objects.select_related(
        "user", "system", "requested_by", "system_owner", "it_approval"
    )

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if change_type_filter:
        queryset = queryset.filter(change_type=change_type_filter)
    if system_filter:
        queryset = queryset.filter(system_id=system_filter)
    if user_filter:
        queryset = queryset.filter(user_id=user_filter)
    if search_query:
        queryset = queryset.filter(
            Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(system__name__icontains=search_query)
            | Q(system__code__icontains=search_query)
            | Q(business_justification__icontains=search_query)
        )

    queryset = queryset.order_by("-created_at")

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    systems = System.objects.all().order_by("name")
    users = CustomUser.objects.all().order_by("first_name", "last_name")

    context = {
        "page_obj": page_obj,
        "change_requests": page_obj,
        "status_choices": AccountChangeRequest.STATUS_CHOICES,
        "change_type_choices": AccountChangeRequest.CHANGE_TYPE_CHOICES,
        "systems": systems,
        "users": users,
        "filters": {
            "status": status_filter,
            "change_type": change_type_filter,
            "system": system_filter,
            "user": user_filter,
            "search": search_query,
        },
    }
    return render(request, "change_management/change_request_list.html", context)


@login_required
def change_request_detail(request, pk):
    """
    Show details of a single account change request.
    """
    change_request = get_object_or_404(
        AccountChangeRequest.objects.select_related(
            "user", "system", "requested_by", "system_owner", "it_approval"
        ),
        pk=pk,
    )

    context = {
        "change_request": change_request,
    }
    return render(request, "change_management/change_request_detail.html", context)


@login_required
def change_request_create(request):
    """
    Create a new account change request.
    """
    if request.method == "POST":
        change_type = request.POST.get("change_type")
        user_id = request.POST.get("user") or None
        system_id = request.POST.get("system")
        business_justification = request.POST.get("business_justification", "").strip()
        system_owner_id = request.POST.get("system_owner") or None
        system_owner_approved = request.POST.get("system_owner_approved") == "on"
        system_owner_approval_date_raw = request.POST.get("system_owner_approval_date")
        system_owner_approval_notes = request.POST.get(
            "system_owner_approval_notes", ""
        ).strip()
        it_approval_id = request.POST.get("it_approval") or None
        status = request.POST.get("status") or AccountChangeRequest.STATUS_PENDING

        try:
            system = System.objects.get(id=system_id)
        except System.DoesNotExist:
            messages.error(request, "Please select a valid system.")
            return redirect("change_management:change_request_create")

        user = None
        if user_id:
            user = CustomUser.objects.filter(id=user_id).first()

        system_owner = None
        if system_owner_id:
            system_owner = CustomUser.objects.filter(id=system_owner_id).first()

        it_approval = None
        if it_approval_id:
            it_approval = CustomUser.objects.filter(id=it_approval_id).first()

        approval_date = None
        if system_owner_approval_date_raw:
            try:
                approval_date = timezone.datetime.fromisoformat(
                    system_owner_approval_date_raw
                )
            except (ValueError, TypeError):
                approval_date = None

        change_request = AccountChangeRequest.objects.create(
            change_type=change_type,
            user=user,
            system=system,
            requested_by=request.user,
            business_justification=business_justification,
            system_owner=system_owner,
            system_owner_approved=system_owner_approved,
            system_owner_approval_date=approval_date,
            system_owner_approval_notes=system_owner_approval_notes or None,
            it_approval=it_approval,
            status=status,
        )

        messages.success(
            request,
            f"Change request #{change_request.pk} created for {system.name}.",
        )
        return redirect("change_management:change_request_detail", pk=change_request.pk)

    systems = System.objects.all().order_by("name")
    users = CustomUser.objects.all().order_by("first_name", "last_name")

    context = {
        "systems": systems,
        "users": users,
        "change_type_choices": AccountChangeRequest.CHANGE_TYPE_CHOICES,
        "status_choices": AccountChangeRequest.STATUS_CHOICES,
        "selected_change_type": "",
        "selected_status": AccountChangeRequest.STATUS_PENDING,
        "selected_user_id": "",
        "selected_system_id": request.GET.get("system", "") or "",
        "selected_system_owner_id": "",
        "selected_it_approval_id": "",
        "business_justification_value": "",
        "system_owner_approval_notes_value": "",
        "system_owner_approval_date_value": "",
        "system_owner_approved_value": "",
    }
    return render(request, "change_management/change_request_form.html", context)


@login_required
def change_request_update(request, pk):
    """
    Update an existing account change request.
    """
    change_request = get_object_or_404(AccountChangeRequest, pk=pk)

    if request.method == "POST":
        change_type = request.POST.get("change_type")
        user_id = request.POST.get("user") or None
        system_id = request.POST.get("system")
        business_justification = request.POST.get("business_justification", "").strip()
        system_owner_id = request.POST.get("system_owner") or None
        system_owner_approved = request.POST.get("system_owner_approved") == "on"
        system_owner_approval_date_raw = request.POST.get("system_owner_approval_date")
        system_owner_approval_notes = request.POST.get(
            "system_owner_approval_notes", ""
        ).strip()
        it_approval_id = request.POST.get("it_approval") or None
        status = request.POST.get("status") or change_request.status
        completed_in_external_system = (
            request.POST.get("completed_in_external_system") == "on"
        )
        completed_date_raw = request.POST.get("completed_date")

        try:
            system = System.objects.get(id=system_id)
        except System.DoesNotExist:
            messages.error(request, "Please select a valid system.")
            return redirect("change_management:change_request_update", pk=pk)

        user = None
        if user_id:
            user = CustomUser.objects.filter(id=user_id).first()

        system_owner = None
        if system_owner_id:
            system_owner = CustomUser.objects.filter(id=system_owner_id).first()

        it_approval = None
        if it_approval_id:
            it_approval = CustomUser.objects.filter(id=it_approval_id).first()

        approval_date = None
        if system_owner_approval_date_raw:
            try:
                approval_date = timezone.datetime.fromisoformat(
                    system_owner_approval_date_raw
                )
            except (ValueError, TypeError):
                approval_date = None

        completed_date = None
        if completed_in_external_system:
            if completed_date_raw:
                try:
                    completed_date = timezone.datetime.fromisoformat(completed_date_raw)
                except (ValueError, TypeError):
                    # If date is invalid, use today
                    completed_date = timezone.now()
            else:
                # If checkbox is checked but no date provided, use today
                completed_date = timezone.now()

        change_request.change_type = change_type
        change_request.user = user
        change_request.system = system
        change_request.business_justification = business_justification
        change_request.system_owner = system_owner
        change_request.system_owner_approved = system_owner_approved
        change_request.system_owner_approval_date = approval_date
        change_request.system_owner_approval_notes = (
            system_owner_approval_notes or None
        )
        change_request.it_approval = it_approval
        change_request.status = status
        change_request.completed_in_external_system = completed_in_external_system
        change_request.completed_date = completed_date
        change_request.save()

        messages.success(request, "Change request updated successfully.")
        return redirect("change_management:change_request_detail", pk=change_request.pk)

    systems = System.objects.all().order_by("name")
    users = CustomUser.objects.all().order_by("first_name", "last_name")

    def _format_dt(dt):
        if not dt:
            return ""
        try:
            return timezone.localtime(dt).strftime("%Y-%m-%dT%H:%M")
        except (ValueError, TypeError):
            return dt.strftime("%Y-%m-%dT%H:%M")

    context = {
        "change_request": change_request,
        "systems": systems,
        "users": users,
        "change_type_choices": AccountChangeRequest.CHANGE_TYPE_CHOICES,
        "status_choices": AccountChangeRequest.STATUS_CHOICES,
        "selected_change_type": change_request.change_type,
        "selected_status": change_request.status,
        "selected_user_id": str(change_request.user_id) if change_request.user_id else "",
        "selected_system_id": str(change_request.system_id),
        "selected_system_owner_id": (
            str(change_request.system_owner_id) if change_request.system_owner_id else ""
        ),
        "selected_it_approval_id": (
            str(change_request.it_approval_id) if change_request.it_approval_id else ""
        ),
        "business_justification_value": change_request.business_justification or "",
        "system_owner_approval_notes_value": (
            change_request.system_owner_approval_notes or ""
        ),
        "system_owner_approval_date_value": _format_dt(
            change_request.system_owner_approval_date
        ),
        "system_owner_approved_value": (
            "on" if change_request.system_owner_approved else ""
        ),
        "completed_in_external_system_value": (
            "on" if change_request.completed_in_external_system else ""
        ),
        "completed_date_value": _format_dt(change_request.completed_date),
    }
    return render(request, "change_management/change_request_form.html", context)


# =============================================================================
# REST API VIEWSET
# =============================================================================

class AccountChangeRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing account change requests via REST API.
    
    Endpoints:
    - GET /api/change-requests/ - List all change requests
    - GET /api/change-requests/{id}/ - Get change request details
    - POST /api/change-requests/ - Create new change request
    - PATCH /api/change-requests/{id}/ - Update change request
    - DELETE /api/change-requests/{id}/ - Delete change request
    - POST /api/change-requests/{id}/approve/ - Approve a change
    - POST /api/change-requests/{id}/reject/ - Reject a change
    - POST /api/change-requests/{id}/mark-completed/ - Mark as completed
    - GET /api/change-requests/statistics/summary/ - Get statistics
    - POST /api/change-requests/bulk-action/ - Perform bulk action
    """
    
    queryset = AccountChangeRequest.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'change_type', 'system', 'user']
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name',
        'system__name', 'business_justification'
    ]
    ordering_fields = ['created_at', 'status', 'change_type']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return AccountChangeRequestDetailSerializer
        elif self.action in ['approve', 'reject', 'mark_completed']:
            return ChangeApprovalSerializer
        elif self.action == 'set_status':
            return ChangeWorkflowStatusSerializer
        elif self.action == 'statistics':
            return ChangeRequestStatisticsSerializer
        elif self.action == 'bulk_action':
            return BulkChangeRequestSerializer
        return AccountChangeRequestListSerializer
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a change request.
        
        Body:
        {
            "approval_notes": "Approved - all requirements met"
        }
        """
        change_request = self.get_object()
        serializer = ChangeApprovalSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # Update change request
                change_request.status = AccountChangeRequest.STATUS_APPROVED
                change_request.system_owner = request.user
                change_request.system_owner_approved = True
                change_request.system_owner_approval_date = timezone.now()
                change_request.system_owner_approval_notes = serializer.validated_data.get('approval_notes', '')
                change_request.save()
                
                logger.info(
                    f"Change request {change_request.id} approved by {request.user.username}"
                )
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'Change request approved',
                        'data': AccountChangeRequestDetailSerializer(change_request).data
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(f"Error approving change request: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a change request.
        
        Body:
        {
            "approval_notes": "Rejected - security concerns"
        }
        """
        change_request = self.get_object()
        serializer = ChangeApprovalSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                change_request.status = AccountChangeRequest.STATUS_REJECTED
                change_request.system_owner = request.user
                change_request.system_owner_approval_notes = serializer.validated_data.get('approval_notes', '')
                change_request.save()
                
                logger.info(
                    f"Change request {change_request.id} rejected by {request.user.username}"
                )
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'Change request rejected',
                        'data': AccountChangeRequestDetailSerializer(change_request).data
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(f"Error rejecting change request: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """
        Mark change request as completed in external system.
        
        Body:
        {
            "approval_notes": "Change implemented in AD"
        }
        """
        change_request = self.get_object()
        serializer = ChangeApprovalSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                change_request.status = AccountChangeRequest.STATUS_COMPLETED
                change_request.completed_in_external_system = True
                change_request.completed_date = timezone.now()
                if serializer.validated_data.get('approval_notes'):
                    change_request.system_owner_approval_notes = serializer.validated_data.get('approval_notes')
                change_request.save()
                
                logger.info(
                    f"Change request {change_request.id} marked completed"
                )
                
                return Response(
                    {
                        'status': 'success',
                        'message': 'Change marked as completed',
                        'data': AccountChangeRequestDetailSerializer(change_request).data
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                logger.error(f"Error marking change as completed: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get change request statistics and metrics."""
        try:
            queryset = self.get_queryset()
            
            # Calculate basic statistics
            total = queryset.count()
            pending = queryset.filter(status=AccountChangeRequest.STATUS_PENDING).count()
            approved = queryset.filter(status=AccountChangeRequest.STATUS_APPROVED).count()
            completed = queryset.filter(status=AccountChangeRequest.STATUS_COMPLETED).count()
            rejected = queryset.filter(status=AccountChangeRequest.STATUS_REJECTED).count()
            
            # Calculate average approval time
            approved_requests = queryset.filter(
                status=AccountChangeRequest.STATUS_APPROVED,
                system_owner_approval_date__isnull=False
            )
            
            avg_approval_hours = 0
            if approved_requests.exists():
                total_hours = 0
                for req in approved_requests:
                    if req.system_owner_approval_date and req.created_at:
                        diff = req.system_owner_approval_date - req.created_at
                        total_hours += diff.total_seconds() / 3600
                avg_approval_hours = total_hours / approved_requests.count()
            
            # Group by system
            by_system = dict(
                queryset.values('system__name').annotate(count=Count('id')).values_list('system__name', 'count')
            )
            
            # Group by change type
            by_change_type = dict(
                queryset.values('change_type').annotate(count=Count('id')).values_list('change_type', 'count')
            )
            
            # Group by status
            by_status = dict(
                queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
            )
            
            statistics = {
                'total_requests': total,
                'pending_requests': pending,
                'approved_requests': approved,
                'completed_requests': completed,
                'rejected_requests': rejected,
                'average_approval_time_hours': round(avg_approval_hours, 2),
                'by_system': by_system,
                'by_change_type': by_change_type,
                'by_status': by_status,
            }
            
            serializer = ChangeRequestStatisticsSerializer(statistics)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error generating statistics: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """
        Perform bulk action on multiple change requests.
        
        Body:
        {
            "ids": [1, 2, 3],
            "action": "approve",
            "notes": "Approved in batch"
        }
        """
        serializer = BulkChangeRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                ids = serializer.validated_data['ids']
                action_type = serializer.validated_data['action']
                notes = serializer.validated_data.get('notes', '')
                
                changes = AccountChangeRequest.objects.filter(id__in=ids)
                updated_count = 0
                
                for change in changes:
                    if action_type == 'approve':
                        change.status = AccountChangeRequest.STATUS_APPROVED
                        change.system_owner = request.user
                        change.system_owner_approved = True
                        change.system_owner_approval_date = timezone.now()
                        if notes:
                            change.system_owner_approval_notes = notes
                    
                    elif action_type == 'reject':
                        change.status = AccountChangeRequest.STATUS_REJECTED
                        if notes:
                            change.system_owner_approval_notes = notes
                    
                    elif action_type == 'complete':
                        change.status = AccountChangeRequest.STATUS_COMPLETED
                        change.completed_in_external_system = True
                        change.completed_date = timezone.now()
                    
                    elif action_type == 'cancel':
                        change.status = AccountChangeRequest.STATUS_REJECTED
                    
                    change.save()
                    updated_count += 1
                
                logger.info(
                    f"Bulk action '{action_type}' performed on {updated_count} change requests"
                )
                
                return Response(
                    {
                        'status': 'success',
                        'message': f'Bulk action completed',
                        'updated_count': updated_count
                    },
                    status=status.HTTP_200_OK
                )
            
            except Exception as e:
                logger.error(f"Error performing bulk action: {str(e)}")
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get pending change requests requiring approval."""
        try:
            # Get pending changes that need system owner approval
            pending_changes = AccountChangeRequest.objects.filter(
                status=AccountChangeRequest.STATUS_PENDING,
                system_owner_approved=False
            ).select_related('user', 'system', 'requested_by')
            
            page = self.paginate_queryset(pending_changes)
            if page is not None:
                serializer = AccountChangeRequestListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = AccountChangeRequestListSerializer(pending_changes, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error retrieving pending approvals: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )



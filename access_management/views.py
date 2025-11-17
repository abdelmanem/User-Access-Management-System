import csv
from io import BytesIO, StringIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer

from .models import UserSystemAccess, AccessHistory
from .reporting import build_policy_drift_snapshot, generate_policy_drift_rows
from .utils import (
    is_generic_username,
    detect_generic_accounts,
    get_generic_accounts_by_system,
    get_unremediated_generic_accounts
)
from accounts.models import CustomUser
from systems.models import System
from departments.models import Department


def _format_datetime(value):
    if not value:
        return ''
    try:
        return timezone.localtime(value).strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return value.strftime('%Y-%m-%d %H:%M') if hasattr(value, 'strftime') else ''


def export_access_assignments_to_excel(queryset):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Access Assignments"

    headers = [
        "User",
        "Username",
        "Department",
        "System",
        "System Code",
        "Access Username",
        "Access Type",
        "Access Level",
        "Status",
        "Priority",
        "Request Date",
        "Access Start",
        "Access End",
        "Approved By",
        "Approval Date",
    ]
    worksheet.append(headers)

    for assignment in queryset:
        user = assignment.user
        system = assignment.system
        approved_by = assignment.approved_by

        worksheet.append([
            user.get_full_name() if user else '',
            user.username if user else '',
            user.department.name if user and user.department else '',
            system.name if system else '',
            system.code if system else '',
            assignment.access_username or '',
            assignment.access_type or '',
            assignment.granted_access_level or '',
            assignment.status or '',
            assignment.priority or '',
            _format_datetime(assignment.request_date),
            _format_datetime(assignment.access_start_date),
            _format_datetime(assignment.access_end_date),
            approved_by.get_full_name() if approved_by else '',
            _format_datetime(assignment.approval_date),
        ])

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)

    response = HttpResponse(
        stream.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="access_assignments.xlsx"'
    return response


def export_access_assignments_to_pdf(queryset):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )

    headers = [
        "User",
        "System",
        "Access Type",
        "Access Level",
        "Status",
        "Priority",
        "Request Date",
        "Access Period",
        "Approved By",
    ]

    data = [headers]

    for assignment in queryset:
        user = assignment.user
        system = assignment.system
        approved_by = assignment.approved_by

        access_period = _format_datetime(assignment.access_start_date)
        if assignment.access_end_date:
            access_period = f"{access_period} → {_format_datetime(assignment.access_end_date)}" if access_period else _format_datetime(assignment.access_end_date)

        data.append([
            f"{user.get_full_name()} ({user.username})" if user else '',
            f"{system.name} ({system.code})" if system else '',
            assignment.access_type or '',
            assignment.granted_access_level or '',
            assignment.status or '',
            assignment.priority or '',
            _format_datetime(assignment.request_date),
            access_period or '',
            approved_by.get_full_name() if approved_by else '',
        ])

    table = Table(data, repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LINEBEFORE', (0, 0), (0, -1), 0.25, colors.grey),
        ('LINEAFTER', (-1, 0), (-1, -1), 0.25, colors.grey),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))

    doc.build([table])
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="access_assignments.pdf"'
    return response


def export_policy_drift_rows_to_csv(rows):
    headers = [
        "Issue Type",
        "User",
        "User Login",
        "Department",
        "System",
        "System Code",
        "External Username",
        "Status",
        "Last Review",
        "Next Review",
        "Detail",
        "Assignment ID",
    ]
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    for row in rows:
        writer.writerow([
            row["issue_type"],
            row["user_name"],
            row["user_username"],
            row["department"],
            row["system_name"],
            row["system_code"],
            row["external_username"],
            row["status"],
            row["last_review"],
            row["next_review"],
            row["detail"],
            row["assignment_id"],
        ])

    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="policy_drift_snapshot.csv"'
    return response


def export_policy_drift_rows_to_pdf(rows, summary, stale_threshold_days):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=24,
        rightMargin=24,
        topMargin=24,
        bottomMargin=24,
    )

    summary_data = [
        ["Metric", "Count"],
        ["Missing Usernames", summary["missing_usernames"]],
        ["Stale Reviews", summary["stale_reviews"]],
        ["Overlapping Usernames", summary["overlapping_usernames"]],
        ["Assignments Scanned", summary["total_assignments"]],
        ["Threshold (days)", stale_threshold_days],
    ]
    summary_table = Table(summary_data, hAlign='LEFT')
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
    ]))

    details_headers = [
        "Issue",
        "User",
        "System",
        "External Username",
        "Status",
        "Last Review",
        "Next Review",
        "Detail",
    ]
    data = [details_headers]
    for row in rows[:200]:
        system_label = f"{row['system_name']} ({row['system_code']})" if row['system_code'] else row['system_name']
        user_label = f"{row['user_name']} ({row['user_username']})" if row['user_username'] else row['user_name']
        data.append([
            row['issue_type'],
            user_label,
            system_label,
            row['external_username'],
            row['status'],
            row['last_review'],
            row['next_review'],
            row['detail'],
        ])

    details_table = Table(data, repeatRows=1, hAlign='LEFT')
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.grey),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))

    doc.build([summary_table, Spacer(1, 12), details_table])
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="policy_drift_snapshot.pdf"'
    return response


def export_policy_drift_rows_to_excel(rows):
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Policy Drift Snapshot"

    headers = [
        "Issue Type",
        "User",
        "User Login",
        "Department",
        "System",
        "System Code",
        "External Username",
        "Status",
        "Last Review",
        "Next Review",
        "Detail",
        "Assignment ID",
    ]
    worksheet.append(headers)

    for row in rows:
        worksheet.append([
            row["issue_type"],
            row["user_name"],
            row["user_username"],
            row["department"],
            row["system_name"],
            row["system_code"],
            row["external_username"],
            row["status"],
            row["last_review"],
            row["next_review"],
            row["detail"],
            row["assignment_id"],
        ])

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)

    response = HttpResponse(
        stream.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="policy_drift_snapshot.xlsx"'
    return response


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
    
    metrics_queryset = queryset

    summary_metrics = {
        'total': metrics_queryset.count(),
        'active': metrics_queryset.filter(status='Active').count(),
        'pending': metrics_queryset.filter(status='Pending').count(),
        'expired': metrics_queryset.filter(status='Expired').count(),
        'unique_users': metrics_queryset.values('user_id').distinct().count(),
        'unique_systems': metrics_queryset.values('system_id').distinct().count(),
    }

    export_format = request.GET.get('export')
    if export_format in {'xlsx', 'pdf'}:
        export_queryset = queryset.order_by('user__first_name', 'user__last_name', '-request_date', 'system__name')
        if export_format == 'xlsx':
            return export_access_assignments_to_excel(export_queryset)
        return export_access_assignments_to_pdf(export_queryset)
    
    # Pagination
    queryset = queryset.order_by('user__first_name', 'user__last_name', '-request_date', 'system__name')

    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    access_assignments = paginator.get_page(page_number)
    
    # Get filter options
    systems = System.objects.all().order_by('name')
    users = CustomUser.objects.all().order_by('first_name', 'last_name')

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_params.pop('export', None)
    current_query = query_params.urlencode()

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
        },
        'current_query': current_query,
        'summary_metrics': summary_metrics,
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
            
            # Get new fields
            system_username = request.POST.get('system_username', '').strip()
            access_username_raw = request.POST.get('access_username')
            if access_username_raw is not None:
                access_username = access_username_raw.strip()
            else:
                access_username = None
            is_generic = request.POST.get('is_generic_account') == 'on'
            
            # If system_username is empty but access_username exists, use access_username
            # This helps migrate legacy data
            if not system_username and access_username:
                system_username = access_username
            
            # Convert empty string to None for database consistency
            system_username = system_username if system_username else None
            access_username = access_username if access_username else None
            
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
                system_username=system_username,
                access_username=access_username,
                is_generic_account=is_generic,
                requested_by=request.user,
                created_by=request.user,
                updated_by=request.user
            )
            
            # Auto-detect generic accounts
            if system_username:
                access_assignment.mark_as_generic_if_needed()
                access_assignment.save()
                
                # Show warning if generic account detected
                if access_assignment.is_generic_account:
                    messages.warning(
                        request,
                        f'Warning: Username "{system_username}" appears to be a generic account. '
                        f'Please ensure this is remediated per RHG Access Control Policy.'
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
        'requested_access_duration_value': request.POST.get('requested_access_duration', ''),
        'access_start_date_value': request.POST.get('access_start_date', ''),
        'access_end_date_value': request.POST.get('access_end_date', ''),
        'access_url_value': request.POST.get('access_url', ''),
        'granted_access_level_value': request.POST.get('granted_access_level', ''),
        'technical_requirements_value': request.POST.get('technical_requirements', ''),
        'security_clearance_required_value': request.POST.get('security_clearance_required', ''),
        'data_access_level_value': request.POST.get('data_access_level', ''),
        'risk_assessment_score_value': request.POST.get('risk_assessment_score', ''),
        'review_frequency_days_value': request.POST.get('review_frequency_days', ''),
        'special_instructions_value': request.POST.get('special_instructions', ''),
        'compliance_requirements_value': request.POST.get('compliance_requirements', ''),
        'system_username_value': request.POST.get('system_username', ''),
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
        access_username_raw = request.POST.get('access_username')
        system_username = request.POST.get('system_username', '').strip()
        access_url = request.POST.get('access_url')
        granted_access_level = request.POST.get('granted_access_level')
        security_clearance_required = request.POST.get('security_clearance_required')
        data_access_level = request.POST.get('data_access_level')
        risk_assessment_score = request.POST.get('risk_assessment_score')
        review_frequency_days = request.POST.get('review_frequency_days')
        special_instructions = request.POST.get('special_instructions')
        compliance_requirements = request.POST.get('compliance_requirements')
        
        # Generic account fields
        is_generic = request.POST.get('is_generic_account') == 'on'
        generic_remediated = request.POST.get('generic_account_remediated') == 'on'
        remediation_date = request.POST.get('remediation_date')
        remediation_notes = request.POST.get('remediation_notes', '')
        
        # If system_username is empty but access_username exists, use access_username
        # This helps migrate legacy data
        if not system_username and access_username_raw:
            system_username = access_username_raw.strip()
        
        # Convert empty string to None for database consistency
        system_username = system_username if system_username else None
        if access_username_raw is None:
            access_username = access_assignment.access_username
        else:
            access_username = access_username_raw.strip() or None
        
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
            access_assignment.access_username = access_username
            access_assignment.system_username = system_username
            access_assignment.access_url = access_url
            access_assignment.granted_access_level = granted_access_level
            access_assignment.security_clearance_required = security_clearance_required
            access_assignment.data_access_level = data_access_level
            access_assignment.risk_assessment_score = int(risk_assessment_score) if risk_assessment_score else None
            access_assignment.review_frequency_days = int(review_frequency_days) if review_frequency_days else None
            access_assignment.special_instructions = special_instructions
            access_assignment.compliance_requirements = compliance_requirements
            
            # Update generic account fields
            access_assignment.is_generic_account = is_generic
            access_assignment.generic_account_remediated = generic_remediated
            if remediation_date:
                access_assignment.remediation_date = timezone.datetime.fromisoformat(remediation_date)
            access_assignment.remediation_notes = remediation_notes
            if generic_remediated and not access_assignment.remediated_by:
                access_assignment.remediated_by = request.user
            
            # Auto-detect generic accounts
            if system_username:
                access_assignment.mark_as_generic_if_needed()
                if access_assignment.is_generic_account and not is_generic:
                    messages.warning(
                        request,
                        f'Warning: Username "{system_username}" appears to be a generic account. '
                        f'It has been automatically flagged.'
                    )
            
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
        'requested_access_duration_value': request.POST.get('requested_access_duration', access_assignment.requested_access_duration or ''),
        'access_start_date_value': request.POST.get(
            'access_start_date',
            timezone.localtime(access_assignment.access_start_date).strftime('%Y-%m-%dT%H:%M') if access_assignment.access_start_date else ''
        ),
        'access_end_date_value': request.POST.get(
            'access_end_date',
            timezone.localtime(access_assignment.access_end_date).strftime('%Y-%m-%dT%H:%M') if access_assignment.access_end_date else ''
        ),
        # Pre-populate system_username from effective_username if system_username is empty (for legacy data migration)
        'system_username_value': request.POST.get('system_username', access_assignment.effective_username or ''),
        'access_url_value': request.POST.get('access_url', access_assignment.access_url or ''),
        'granted_access_level_value': request.POST.get('granted_access_level', access_assignment.granted_access_level or ''),
        'technical_requirements_value': request.POST.get('technical_requirements', access_assignment.technical_requirements or ''),
        'security_clearance_required_value': request.POST.get('security_clearance_required', access_assignment.security_clearance_required or ''),
        'data_access_level_value': request.POST.get('data_access_level', access_assignment.data_access_level or ''),
        'risk_assessment_score_value': request.POST.get('risk_assessment_score', access_assignment.risk_assessment_score or ''),
        'review_frequency_days_value': request.POST.get('review_frequency_days', access_assignment.review_frequency_days or ''),
        'special_instructions_value': request.POST.get('special_instructions', access_assignment.special_instructions or ''),
        'compliance_requirements_value': request.POST.get('compliance_requirements', access_assignment.compliance_requirements or ''),
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


@login_required
def generic_accounts_report(request):
    """Report of all generic accounts across external systems"""
    # Get filter parameters
    system_id = request.GET.get('system')
    show_remediated = request.GET.get('show_remediated', 'false') == 'true'
    search = request.GET.get('search', '').strip()
    
    # Start with all generic accounts
    queryset = UserSystemAccess.objects.filter(is_generic_account=True).select_related('user', 'system')
    
    # Filter by system
    if system_id:
        queryset = queryset.filter(system_id=system_id)
    
    # Filter by remediation status
    if not show_remediated:
        queryset = queryset.filter(generic_account_remediated=False)
    
    # Search filter - search in both system_username and access_username (for legacy data)
    if search:
        queryset = queryset.filter(
            Q(system_username__icontains=search) |
            Q(access_username__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__username__icontains=search) |
            Q(system__name__icontains=search)
        )
    
    # Order by system, then username (use system_username first, fallback to access_username)
    # Note: We can't order by effective_username directly, so we order by system_username
    # Records with only access_username will appear after those with system_username
    queryset = queryset.order_by('system__name', 'system_username', 'access_username')
    
    # Pagination
    paginator = Paginator(queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_generic = UserSystemAccess.objects.filter(is_generic_account=True).count()
    unremediated = UserSystemAccess.objects.filter(
        is_generic_account=True,
        generic_account_remediated=False
    ).count()
    remediated = total_generic - unremediated
    
    # Group by system
    by_system = queryset.values('system__name', 'system__code').annotate(
        count=Count('id')
    ).order_by('system__name')
    
    context = {
        'page_obj': page_obj,
        'generic_accounts': page_obj,
        'systems': System.objects.all().order_by('name'),
        'selected_system_id': system_id,
        'show_remediated': show_remediated,
        'search': search,
        'total_generic': total_generic,
        'unremediated': unremediated,
        'remediated': remediated,
        'by_system': by_system,
    }
    
    return render(request, 'access_management/generic_accounts_report.html', context)


@login_required
def policy_drift_monitoring(request):
    """
    Highlight access records that indicate potential policy drift:
    - Accounts missing external usernames
    - Accounts with stale or overdue reviews
    - Usernames reused by multiple employees in the same system
    """
    default_threshold_days = 90

    system_id_param = request.GET.get('system')
    department_id_param = request.GET.get('department')
    status_scope = request.GET.get('status_scope', 'active')
    threshold_param = request.GET.get('stale_threshold')

    def _coerce_int(value):
        if not value:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    system_id = _coerce_int(system_id_param)
    department_id = _coerce_int(department_id_param)

    try:
        stale_threshold_days = int(threshold_param) if threshold_param else default_threshold_days
        if stale_threshold_days <= 0:
            raise ValueError
    except (TypeError, ValueError):
        stale_threshold_days = default_threshold_days

    snapshot = build_policy_drift_snapshot(
        system_id=system_id,
        department_id=department_id,
        status_scope=status_scope,
        stale_threshold_days=stale_threshold_days,
    )

    def _get_bool(name, default=True):
        values = request.GET.getlist(name)
        if not values:
            return default
        return any(value.lower() == 'true' for value in values)

    show_missing = _get_bool('show_missing', True)
    show_stale = _get_bool('show_stale', True)
    show_overlapping = _get_bool('show_overlapping', True)

    export_format = request.GET.get('export')
    rows = list(generate_policy_drift_rows(snapshot))

    def filter_rows(row_list):
        issue_type = row_list.get('issue_type') if isinstance(row_list, dict) else None
        if issue_type == 'Missing Username' and not show_missing:
            return False
        if issue_type == 'Stale Review' and not show_stale:
            return False
        if issue_type == 'Overlapping Username' and not show_overlapping:
            return False
        return True

    filtered_rows = [row for row in rows if filter_rows(row)]

    if export_format in {'csv', 'pdf'}:
        if export_format == 'csv':
            return export_policy_drift_rows_to_csv(filtered_rows)
        return export_policy_drift_rows_to_pdf(filtered_rows, snapshot['issue_summary'], stale_threshold_days)
    if export_format == 'xlsx':
        return export_policy_drift_rows_to_excel(filtered_rows)

    query_params = request.GET.copy()
    query_params.pop('page', None)
    query_params.pop('export', None)
    base_query = query_params.urlencode()
    def _build_export_link(fmt):
        return f"?{base_query}&export={fmt}" if base_query else f"?export={fmt}"

    csv_link = _build_export_link('csv')
    pdf_link = _build_export_link('pdf')
    xlsx_link = _build_export_link('xlsx')

    context = {
        'issue_summary': snapshot['issue_summary'],
        'missing_usernames': snapshot['missing_usernames_qs'].select_related('user', 'system')[:50] if show_missing else [],
        'stale_reviews': snapshot['stale_reviews_qs'].select_related('user', 'system')[:50] if show_stale else [],
        'overlapping_groups': snapshot['overlapping_groups'].values() if show_overlapping else [],
        'system_issue_counts': snapshot['system_issue_counts'],
        'systems': System.objects.filter(is_active=True).order_by('name'),
        'departments': Department.objects.filter(is_active=True).order_by('name'),
        'filters': {
            'system': system_id_param or '',
            'department': department_id_param or '',
            'status_scope': status_scope,
            'stale_threshold': stale_threshold_days,
            'show_missing': show_missing,
            'show_stale': show_stale,
            'show_overlapping': show_overlapping,
        },
        'threshold_options': [30, 60, 90, 120, 180],
        'now': snapshot['now'],
        'stale_reference': snapshot['stale_reference'],
        'export_links': {
            'csv': csv_link,
            'pdf': pdf_link,
            'xlsx': xlsx_link,
        },
    }

    return render(request, 'access_management/policy_drift_monitoring.html', context)


@login_required
def mark_generic_account_remediated(request, pk):
    """Mark a generic account as remediated"""
    access_assignment = get_object_or_404(UserSystemAccess, pk=pk)
    
    if not access_assignment.is_generic_account:
        messages.error(request, 'This account is not marked as generic.')
        return redirect('access_management:generic_accounts_report')
    
    if request.method == 'POST':
        remediation_notes = request.POST.get('remediation_notes', '')
        remediation_date = request.POST.get('remediation_date')
        
        access_assignment.generic_account_remediated = True
        access_assignment.remediated_by = request.user
        access_assignment.remediation_notes = remediation_notes
        if remediation_date:
            try:
                access_assignment.remediation_date = timezone.datetime.fromisoformat(remediation_date.replace('Z', '+00:00'))
            except:
                access_assignment.remediation_date = timezone.now()
        else:
            access_assignment.remediation_date = timezone.now()
        access_assignment.save()
        
        # Create access history entry
        AccessHistory.objects.create(
            user=access_assignment.user,
            system=access_assignment.system,
            user_system_access=access_assignment,
            action='Modified',
            action_description=f'Generic account "{access_assignment.system_username}" marked as remediated by {request.user.full_name}',
            created_by=request.user
        )
        
        messages.success(
            request,
            f'Generic account "{access_assignment.system_username}" has been marked as remediated.'
        )
        return redirect('access_management:generic_accounts_report')
    
    context = {
        'access_assignment': access_assignment,
    }
    
    return render(request, 'access_management/mark_remediated.html', context)


@login_required
def cross_system_account_mapping(request):
    """Cross-system account mapping showing all employees and their usernames across all systems"""
    # Get filter parameters
    user_id = request.GET.get('user')
    system_id = request.GET.get('system')
    department_id = request.GET.get('department')
    search = request.GET.get('search', '').strip()
    show_only_with_access = request.GET.get('show_only_with_access', 'false') == 'true'
    
    # Get all users
    users = CustomUser.objects.all().select_related('department')
    
    # Get all systems
    systems = System.objects.filter(is_active=True).order_by('name')
    
    # Apply filters
    if user_id:
        users = users.filter(id=user_id)
    if department_id:
        users = users.filter(department_id=department_id)
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(username__icontains=search) |
            Q(employee_id__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Get all access assignments with system usernames
    access_assignments = UserSystemAccess.objects.filter(
        status__in=['Active', 'Approved']
    ).select_related('user', 'system')
    
    if system_id:
        access_assignments = access_assignments.filter(system_id=system_id)
    
    # Build mapping: user_id -> {system_id: system_username}
    user_system_mapping = {}
    for access in access_assignments:
        user_id = access.user_id
        system_id = access.system_id
        # Use effective_username property which handles system_username and access_username fallback
        username = access.effective_username
        
        if user_id not in user_system_mapping:
            user_system_mapping[user_id] = {}
        user_system_mapping[user_id][system_id] = {
            'username': username,
            'access_type': access.access_type,
            'status': access.status,
            'is_generic': access.is_generic_account,
            'access_id': access.id,
        }
    
    # Filter users if show_only_with_access
    if show_only_with_access:
        users = users.filter(id__in=user_system_mapping.keys())
    
    # Order users
    users = users.order_by('first_name', 'last_name')
    
    # Pagination
    paginator = Paginator(users, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_users = users.count()
    users_with_access = len(user_system_mapping)
    total_systems = systems.count()
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'systems': systems,
        'user_system_mapping': user_system_mapping,
        'selected_user_id': user_id,
        'selected_system_id': system_id,
        'selected_department_id': department_id,
        'search': search,
        'show_only_with_access': show_only_with_access,
        'total_users': total_users,
        'users_with_access': users_with_access,
        'total_systems': total_systems,
        'departments': Department.objects.filter(is_active=True).order_by('name'),
    }
    
    return render(request, 'access_management/cross_system_account_mapping.html', context)


@login_required
def user_cross_system_accounts(request, user_id):
    """Show all usernames for a single employee across all systems"""
    user = get_object_or_404(CustomUser, pk=user_id)
    
    # Get all access assignments for this user
    access_assignments = UserSystemAccess.objects.filter(
        user=user
    ).select_related('system').order_by('system__name')
    
    # Build mapping: system -> access details
    system_accounts = []
    for access in access_assignments:
        system_accounts.append({
            'system': access.system,
            'system_username': access.effective_username or 'N/A',
            'access_type': access.access_type,
            'status': access.status,
            'is_generic': access.is_generic_account,
            'generic_remediated': access.generic_account_remediated,
            'access_start_date': access.access_start_date,
            'access_end_date': access.access_end_date,
            'access_id': access.id,
        })
    
    # Get all systems to show which ones user doesn't have access to
    all_systems = System.objects.filter(is_active=True).order_by('name')
    systems_with_access = {acc['system'].id for acc in system_accounts}
    systems_without_access = [sys for sys in all_systems if sys.id not in systems_with_access]
    
    context = {
        'user': user,
        'system_accounts': system_accounts,
        'systems_without_access': systems_without_access,
        'total_systems': all_systems.count(),
        'systems_with_access_count': len(system_accounts),
    }
    
    return render(request, 'access_management/user_cross_system_accounts.html', context)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import CustomUser
from systems.models import System
from .models import AccountChangeRequest


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
        if completed_in_external_system and completed_date_raw:
            try:
                completed_date = timezone.datetime.fromisoformat(completed_date_raw)
            except (ValueError, TypeError):
                completed_date = None

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



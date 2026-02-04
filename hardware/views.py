from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import HardwareAssetForm
from .models import HardwareAsset


@login_required
def hardware_list(request):
    assets = (
        HardwareAsset.objects.all()
        .select_related("department", "primary_user")
        .prefetch_related("assigned_users", "related_systems")
        .annotate(user_count=Count("assigned_users", distinct=True))
    )

    # Filters
    search_query = request.GET.get("q", "").strip()
    filter_hardware_type = request.GET.get("hardware_type", "").strip()
    filter_status = request.GET.get("status", "").strip()
    filter_operating_system = request.GET.get("operating_system", "").strip()
    filter_os_version = request.GET.get("os_version", "").strip()

    if search_query:
        assets = assets.filter(
            Q(name__icontains=search_query)
            | Q(asset_tag__icontains=search_query)
            | Q(serial_number__icontains=search_query)
            | Q(location__icontains=search_query)
            | Q(ip_address__icontains=search_query)
            | Q(ipv4_address__icontains=search_query)
            | Q(operating_system__icontains=search_query)
            | Q(operating_system_version__icontains=search_query)
        )

    if filter_hardware_type:
        assets = assets.filter(hardware_type=filter_hardware_type)

    if filter_status:
        assets = assets.filter(status=filter_status)

    if filter_operating_system:
        assets = assets.filter(operating_system=filter_operating_system)

    if filter_os_version:
        assets = assets.filter(operating_system_version=filter_os_version)

    # Sorting
    sort = request.GET.get("sort", "")
    order = request.GET.get("order", "asc")
    valid_sort_fields = [
        "name", "serial_number", "operating_system", "operating_system_version", "ipv4_address",
        "hardware_type", "status", "department__name", "primary_user__full_name", "user_count"
    ]
    if sort in valid_sort_fields:
        if order == "desc":
            assets = assets.order_by(f"-{sort}")
        else:
            assets = assets.order_by(sort)

    # Choices for dropdowns
    operating_system_choices = (
        HardwareAsset.objects.values_list("operating_system", flat=True)
        .distinct()
        .order_by("operating_system")
    )
    operating_system_choices = [os for os in operating_system_choices if os]

    os_version_choices = (
        HardwareAsset.objects.values_list("operating_system_version", flat=True)
        .distinct()
        .order_by("operating_system_version")
    )
    os_version_choices = [ver for ver in os_version_choices if ver]

    context = {
        "assets": assets,
        "total_assets": assets.count(),
        "active_assets": assets.filter(status="In Service").count(),
        "in_storage_assets": assets.filter(status="In Storage").count(),
        "retired_assets": assets.filter(status__in=["Retired", "Disposed"]).count(),
        "search_query": search_query,
        "filter_hardware_type": filter_hardware_type,
        "filter_status": filter_status,
        "hardware_type_choices": HardwareAsset.HARDWARE_TYPE_CHOICES,
        "status_choices": HardwareAsset.STATUS_CHOICES,
        "operating_system_choices": operating_system_choices,
        "filter_operating_system": filter_operating_system,
        "os_version_choices": os_version_choices,
        "filter_os_version": filter_os_version,
    }
    return render(request, "hardware/hardware_list.html", context)


@login_required
def hardware_detail(request, pk):
    asset = get_object_or_404(
        HardwareAsset.objects.select_related(
            "department", "primary_user", "created_by", "updated_by"
        ).prefetch_related("assigned_users", "related_systems"),
        pk=pk,
    )
    context = {
        "asset": asset,
    }
    return render(request, "hardware/hardware_detail.html", context)


@login_required
def hardware_create(request):
    if request.method == "POST":
        form = HardwareAssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.created_by = request.user
            asset.updated_by = request.user
            asset.save()
            form.save_m2m()
            messages.success(request, "Hardware asset created successfully.")
            return redirect("hardware:hardware_detail", pk=asset.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = HardwareAssetForm()
    return render(request, "hardware/hardware_form.html", {"form": form})


@login_required
def hardware_update(request, pk):
    asset = get_object_or_404(HardwareAsset, pk=pk)
    if request.method == "POST":
        form = HardwareAssetForm(request.POST, instance=asset)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.updated_by = request.user
            asset.save()
            form.save_m2m()
            messages.success(request, "Hardware asset updated successfully.")
            return redirect("hardware:hardware_detail", pk=asset.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = HardwareAssetForm(instance=asset)
    return render(
        request, "hardware/hardware_form.html", {"form": form, "asset": asset}
    )


@login_required
def hardware_delete(request, pk):
    asset = get_object_or_404(HardwareAsset, pk=pk)
    if request.method == "POST":
        asset.delete()
        messages.success(request, "Hardware asset deleted successfully.")
        return redirect("hardware:hardware_list")
    return render(request, "hardware/hardware_confirm_delete.html", {"asset": asset})

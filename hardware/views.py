from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import HardwareAssetForm, AccessoryForm, RelatedAssetForm, BulkAccessoryForm
from .models import HardwareAsset, Accessory, RelatedAsset


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


# ============================
# ACCESSORY VIEWS
# ============================


@login_required
def accessory_list(request):
    """List all accessories with filtering, search, and bulk actions."""
    
    # Handle bulk actions
    if request.method == "POST":
        action = request.POST.get("action", "").strip()
        selected_ids = request.POST.getlist("selected_ids")
        
        if action == "delete" and selected_ids:
            count = Accessory.objects.filter(pk__in=selected_ids).delete()[0]
            messages.success(request, f"✅ Successfully deleted {count} accessory/accessories!")
            return redirect("hardware:accessory_list")
        elif action == "change_status" and selected_ids:
            new_status = request.POST.get("status", "").strip()
            if new_status:
                count = Accessory.objects.filter(pk__in=selected_ids).update(status=new_status)
                messages.success(request, f"✅ Updated status for {count} accessory/accessories!")
                return redirect("hardware:accessory_list")
    
    accessories = (
        Accessory.objects.all()
        .select_related("department", "primary_user")
        .prefetch_related("hardware_assignments")
    )

    # Filters
    search_query = request.GET.get("q", "").strip()
    filter_accessory_type = request.GET.get("accessory_type", "").strip()
    filter_status = request.GET.get("status", "").strip()

    if search_query:
        accessories = accessories.filter(
            Q(name__icontains=search_query)
            | Q(asset_tag__icontains=search_query)
            | Q(serial_number__icontains=search_query)
            | Q(manufacturer__icontains=search_query)
            | Q(model_number__icontains=search_query)
        )

    if filter_accessory_type:
        accessories = accessories.filter(accessory_type=filter_accessory_type)

    if filter_status:
        accessories = accessories.filter(status=filter_status)

    # Default ordering
    accessories = accessories.order_by("name", "asset_tag")

    context = {
        "accessories": accessories,
        "total_accessories": accessories.count(),
        "active_accessories": accessories.filter(status="In Service").count(),
        "in_storage_accessories": accessories.filter(status="In Storage").count(),
        "retired_accessories": accessories.filter(status__in=["Retired", "Disposed"]).count(),
        "search_query": search_query,
        "filter_accessory_type": filter_accessory_type,
        "filter_status": filter_status,
        "accessory_type_choices": Accessory.ACCESSORY_TYPE_CHOICES,
        "status_choices": Accessory.STATUS_CHOICES,
    }
    return render(request, "hardware/accessory_list.html", context)


@login_required
def accessory_detail(request, pk):
    """View a single accessory's details and assignments."""
    accessory = get_object_or_404(
        Accessory.objects.select_related("department", "primary_user", "created_by", "updated_by")
        .prefetch_related("hardware_assignments"),
        pk=pk,
    )
    context = {
        "accessory": accessory,
    }
    return render(request, "hardware/accessory_detail.html", context)


@login_required
def accessory_create(request):
    """Create a new accessory."""
    if request.method == "POST":
        form = AccessoryForm(request.POST)
        if form.is_valid():
            accessory = form.save(commit=False)
            accessory.created_by = request.user
            accessory.updated_by = request.user
            accessory.save()
            messages.success(request, "Accessory created successfully.")
            return redirect("hardware:accessory_detail", pk=accessory.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = AccessoryForm()
    return render(request, "hardware/accessory_form.html", {"form": form})


@login_required
def accessory_update(request, pk):
    """Edit an existing accessory."""
    accessory = get_object_or_404(Accessory, pk=pk)
    if request.method == "POST":
        form = AccessoryForm(request.POST, instance=accessory)
        if form.is_valid():
            accessory = form.save(commit=False)
            accessory.updated_by = request.user
            accessory.save()
            messages.success(request, "Accessory updated successfully.")
            return redirect("hardware:accessory_detail", pk=accessory.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = AccessoryForm(instance=accessory)
    return render(request, "hardware/accessory_form.html", {"form": form, "accessory": accessory})


@login_required
def accessory_delete(request, pk):
    """Delete an accessory."""
    accessory = get_object_or_404(Accessory, pk=pk)
    if request.method == "POST":
        accessory.delete()
        messages.success(request, "Accessory deleted successfully.")
        return redirect("hardware:accessory_list")
    return render(request, "hardware/accessory_confirm_delete.html", {"accessory": accessory})


# ============================
# RELATED ASSET (ASSIGNMENT) VIEWS
# ============================


@login_required
def related_asset_detail(request, pk):
    """View details of a hardware-to-accessory assignment."""
    related_asset = get_object_or_404(
        RelatedAsset.objects.select_related(
            "hardware_asset", "hardware_asset__department", "hardware_asset__primary_user",
            "accessory", "accessory__department", "accessory__primary_user",
            "created_by"
        ),
        pk=pk,
    )
    context = {
        "related_asset": related_asset,
    }
    return render(request, "hardware/related_asset_detail.html", context)


@login_required
def related_asset_create(request):
    """Create a new accessory assignment to hardware."""
    # Check if there's a pre-selected hardware or accessory from query parameters
    hardware_id = request.GET.get("hardware")
    accessory_id = request.GET.get("accessory")

    if request.method == "POST":
        form = RelatedAssetForm(request.POST)
        if form.is_valid():
            related_asset = form.save(commit=False)
            related_asset.created_by = request.user
            related_asset.save()
            messages.success(request, "Accessory assigned successfully.")
            return redirect("hardware:related_asset_detail", pk=related_asset.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        initial_data = {}
        if hardware_id:
            try:
                initial_data["hardware_asset"] = int(hardware_id)
            except (ValueError, TypeError):
                pass
        if accessory_id:
            try:
                initial_data["accessory"] = int(accessory_id)
            except (ValueError, TypeError):
                pass
        form = RelatedAssetForm(initial=initial_data)

    return render(request, "hardware/related_asset_form.html", {"form": form})


@login_required
def related_asset_update(request, pk):
    """Edit an existing accessory assignment."""
    related_asset = get_object_or_404(RelatedAsset, pk=pk)
    if request.method == "POST":
        form = RelatedAssetForm(request.POST, instance=related_asset)
        if form.is_valid():
            related_asset = form.save()
            messages.success(request, "Assignment updated successfully.")
            return redirect("hardware:related_asset_detail", pk=related_asset.pk)
        messages.error(request, "Please correct the errors below.")
    else:
        form = RelatedAssetForm(instance=related_asset)
    return render(request, "hardware/related_asset_form.html", {"form": form, "related_asset": related_asset})


@login_required
def related_asset_delete(request, pk):
    """Delete an accessory assignment."""
    related_asset = get_object_or_404(RelatedAsset, pk=pk)
    if request.method == "POST":
        related_asset.delete()
        messages.success(request, "Assignment deleted successfully.")
        return redirect("hardware:hardware_list")
    return render(request, "hardware/related_asset_confirm_delete.html", {"related_asset": related_asset})

@login_required
def bulk_accessory_create(request):
    """Bulk create accessories with individual form fields."""
    if request.method == "POST":
        form = BulkAccessoryForm(request.POST)
        if form.is_valid():
            try:
                accessories_data = form.generate_accessories()
                created_accessories = []
                
                for acc_data in accessories_data:
                    accessory = Accessory.objects.create(
                        name=acc_data['name'],
                        asset_tag=acc_data['asset_tag'],
                        accessory_type=acc_data['accessory_type'],
                        manufacturer=acc_data['manufacturer'],
                        model_number=acc_data['model_number'],
                        serial_number=acc_data['serial_number'],
                        status=acc_data['status'],
                        location=acc_data['location'],
                        department=acc_data['department'],
                        created_by=request.user,
                    )
                    created_accessories.append(accessory)
                
                count = len(created_accessories)
                messages.success(
                    request,
                    f"✅ Successfully created {count} accessory/accessories!"
                )
                return redirect("hardware:accessory_list")
                
            except Exception as e:
                messages.error(request, f"Error creating accessories: {str(e)}")
    else:
        form = BulkAccessoryForm()
    
    return render(request, "hardware/bulk_accessory_create.html", {"form": form})
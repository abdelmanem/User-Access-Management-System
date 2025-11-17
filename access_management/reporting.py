from collections import OrderedDict
from datetime import timedelta
from typing import Dict, Iterable, Optional

from django.db.models import Q, Count
from django.utils import timezone

from .models import UserSystemAccess


def build_policy_drift_snapshot(
    *,
    system_id: Optional[int] = None,
    department_id: Optional[int] = None,
    status_scope: str = "active",
    stale_threshold_days: int = 90,
) -> Dict:
    """
    Construct the data needed for the policy drift dashboard/reports.
    """
    now = timezone.now()
    stale_reference = now - timedelta(days=stale_threshold_days)

    base_queryset = UserSystemAccess.objects.select_related(
        "user",
        "user__department",
        "system",
    )

    if status_scope == "active":
        base_queryset = base_queryset.filter(status__in=["Active", "Approved", "Suspended"])

    if system_id:
        base_queryset = base_queryset.filter(system_id=system_id)

    if department_id:
        base_queryset = base_queryset.filter(user__department_id=department_id)

    missing_username_filter = Q(system_username__isnull=True) | Q(system_username__exact="")
    missing_username_qs = base_queryset.filter(missing_username_filter).order_by(
        "system__name", "user__first_name", "user__last_name"
    )

    stale_review_filter = (
        Q(last_review_date__lt=stale_reference)
        | Q(last_review_date__isnull=True, created_at__lt=stale_reference)
        | Q(next_review_date__lt=now)
    )
    stale_reviews_qs = base_queryset.filter(stale_review_filter).order_by(
        "next_review_date", "last_review_date"
    )

    duplicate_username_groups = (
        base_queryset.exclude(Q(system_username__isnull=True) | Q(system_username__exact=""))
        .values("system_id", "system__name", "system__code", "system_username")
        .annotate(user_count=Count("user_id", distinct=True), assignment_count=Count("id"))
        .filter(user_count__gt=1)
        .order_by("system__name", "system_username")
    )

    overlapping_groups = OrderedDict()
    duplicate_conditions = []
    for group in duplicate_username_groups:
        key = (group["system_id"], group["system_username"])
        overlapping_groups[key] = {
            "system_id": group["system_id"],
            "system_name": group["system__name"],
            "system_code": group["system__code"],
            "username": group["system_username"],
            "user_count": group["user_count"],
            "assignment_count": group["assignment_count"],
            "assignments": [],
        }
        duplicate_conditions.append(Q(system_id=group["system_id"], system_username=group["system_username"]))

    if duplicate_conditions:
        combined_condition = duplicate_conditions[0]
        for condition in duplicate_conditions[1:]:
            combined_condition |= condition

        overlapping_assignments = (
            base_queryset.filter(combined_condition)
            .select_related("user", "system", "user__department")
            .order_by("system__name", "system_username", "user__first_name", "user__last_name")
        )

        for assignment in overlapping_assignments:
            key = (assignment.system_id, assignment.system_username)
            if key in overlapping_groups:
                overlapping_groups[key]["assignments"].append(assignment)

    issue_summary = {
        "missing_usernames": missing_username_qs.count(),
        "stale_reviews": stale_reviews_qs.count(),
        "overlapping_usernames": len(overlapping_groups),
        "total_assignments": base_queryset.count(),
    }

    system_issue_counts = (
        base_queryset.values("system_id", "system__name", "system__code")
        .annotate(
            missing_count=Count("id", filter=missing_username_filter),
            stale_count=Count("id", filter=stale_review_filter),
        )
        .filter(Q(missing_count__gt=0) | Q(stale_count__gt=0))
        .order_by("-missing_count", "-stale_count", "system__name")
    )

    return {
        "now": now,
        "stale_reference": stale_reference,
        "stale_threshold_days": stale_threshold_days,
        "issue_summary": issue_summary,
        "missing_usernames_qs": missing_username_qs,
        "stale_reviews_qs": stale_reviews_qs,
        "overlapping_groups": overlapping_groups,
        "system_issue_counts": system_issue_counts,
        "base_queryset": base_queryset,
    }


def generate_policy_drift_rows(snapshot: Dict) -> Iterable[Dict]:
    """
    Flatten the snapshot into row dictionaries for exports/notifications.
    """

    def _field(value):
        if value is None:
            return ""
        if hasattr(value, "strftime"):
            try:
                return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                return value.strftime("%Y-%m-%d %H:%M")
        return value

    rows = []

    for assignment in snapshot["missing_usernames_qs"]:
        rows.append(
            {
                "issue_type": "Missing Username",
                "user_name": getattr(assignment.user, "full_name", "") if assignment.user else "",
                "user_username": getattr(assignment.user, "username", "") if assignment.user else "",
                "department": getattr(assignment.user.department, "name", "")
                if assignment.user and assignment.user.department
                else "",
                "system_name": getattr(assignment.system, "name", "") if assignment.system else "",
                "system_code": getattr(assignment.system, "code", "") if assignment.system else "",
                "external_username": assignment.system_username or assignment.access_username or "",
                "status": assignment.status,
                "last_review": _field(assignment.last_review_date),
                "next_review": _field(assignment.next_review_date),
                "detail": "External username not captured",
                "assignment_id": assignment.pk,
            }
        )

    for assignment in snapshot["stale_reviews_qs"]:
        detail = []
        if assignment.last_review_date and assignment.last_review_date < snapshot["stale_reference"]:
            detail.append("Last review stale")
        if not assignment.last_review_date:
            detail.append("No review on record")
        if assignment.next_review_date and assignment.next_review_date < snapshot["now"]:
            detail.append("Next review overdue")
        if not detail:
            detail.append("Review cadence exceeded")

        rows.append(
            {
                "issue_type": "Stale Review",
                "user_name": getattr(assignment.user, "full_name", "") if assignment.user else "",
                "user_username": getattr(assignment.user, "username", "") if assignment.user else "",
                "department": getattr(assignment.user.department, "name", "")
                if assignment.user and assignment.user.department
                else "",
                "system_name": getattr(assignment.system, "name", "") if assignment.system else "",
                "system_code": getattr(assignment.system, "code", "") if assignment.system else "",
                "external_username": assignment.system_username or assignment.access_username or "",
                "status": assignment.status,
                "last_review": _field(assignment.last_review_date),
                "next_review": _field(assignment.next_review_date),
                "detail": "; ".join(detail),
                "assignment_id": assignment.pk,
            }
        )

    for group in snapshot["overlapping_groups"].values():
        for assignment in group["assignments"]:
            rows.append(
                {
                    "issue_type": "Overlapping Username",
                    "user_name": getattr(assignment.user, "full_name", "") if assignment.user else "",
                    "user_username": getattr(assignment.user, "username", "") if assignment.user else "",
                    "department": getattr(assignment.user.department, "name", "")
                    if assignment.user and assignment.user.department
                    else "",
                    "system_name": group["system_name"],
                    "system_code": group["system_code"],
                    "external_username": group["username"],
                    "status": assignment.status,
                    "last_review": _field(assignment.last_review_date),
                    "next_review": _field(assignment.next_review_date),
                    "detail": f"Shared username across {group['user_count']} users",
                    "assignment_id": assignment.pk,
                }
            )

    return rows


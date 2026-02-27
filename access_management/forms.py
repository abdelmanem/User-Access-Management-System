from django import forms
from django.utils import timezone

from accounts.models import CustomUser
from systems.models import System

from .models import (
    QuarterlyAccessReview,
    PermissionChangeDocumentation,
    QuarterlyActiveUserReview,
    MonthlyObsoleteAccountReview,
    AccessRemovalDocumentation,
)


def get_current_quarter_label(reference=None):
    """Return a string like '2025-Q1' for the provided date (default: now)."""
    reference = reference or timezone.now().date()
    quarter = ((reference.month - 1) // 3) + 1
    return f"{reference.year}-Q{quarter}"


class QuarterlyAccessReviewForm(forms.ModelForm):
    review_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
        help_text="When the review occurred",
    )

    system_owner_confirmed_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = QuarterlyAccessReview
        fields = [
            "review_quarter",
            "reviewed_user",
            "system",
            "user_system_access",
            "reviewed_by",
            "review_date",
            "approved_permissions",
            "actual_permissions_in_external_system",
            "matches_approved",
            "discrepancies",
            "system_owner",
            "system_owner_confirmed",
            "system_owner_confirmed_date",
            "system_owner_notes",
            "review_completed",
        ]
        widgets = {
            "review_quarter": forms.TextInput(attrs={"placeholder": "YYYY-Q#"}),
            "approved_permissions": forms.Textarea(attrs={"rows": 3}),
            "actual_permissions_in_external_system": forms.Textarea(attrs={"rows": 3}),
            "discrepancies": forms.Textarea(attrs={"rows": 2}),
            "system_owner_notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get("review_quarter"):
            self.initial["review_quarter"] = get_current_quarter_label()
        if not self.initial.get("review_date"):
            self.initial["review_date"] = timezone.now().strftime("%Y-%m-%dT%H:%M")
        self._apply_bootstrap_classes()

    def _apply_bootstrap_classes(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()


class PermissionChangeDocumentationForm(forms.ModelForm):
    changed_in_external_system_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = PermissionChangeDocumentation
        fields = [
            "user_system_access",
            "old_permissions",
            "new_permissions",
            "changed_in_external_system_date",
            "has_approval",
            "approval_reference",
            "documented_by",
            "notes",
        ]
        widgets = {
            "old_permissions": forms.Textarea(attrs={"rows": 2}),
            "new_permissions": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get("changed_in_external_system_date"):
            self.initial["changed_in_external_system_date"] = timezone.now().strftime(
                "%Y-%m-%dT%H:%M"
            )
        self._apply_bootstrap_classes()

    def _apply_bootstrap_classes(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = (existing + " form-control").strip()


class BulkQuarterlyReviewForm(forms.Form):
    review_quarter = forms.CharField(
        label="Quarter",
        max_length=10,
        help_text="Format: YYYY-Q# (e.g., 2025-Q1)",
    )
    system = forms.ModelChoiceField(
        label="System",
        queryset=System.objects.none(),
    )
    users_qty = forms.IntegerField(
        label="Number of Users",
        min_value=1,
        max_value=500,
        initial=5,
        help_text="How many users to auto-generate quarterly reviews for this system.",
    )
    review_date = forms.DateTimeField(
        label="Review Date",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    reviewed_by = forms.ModelChoiceField(
        label="Reviewed By",
        queryset=CustomUser.objects.none(),
    )
    matches_approved = forms.BooleanField(
        label="Mark as matching approved permissions",
        required=False,
        initial=True,
    )
    review_completed = forms.BooleanField(
        label="Mark generated reviews as completed",
        required=False,
        initial=False,
    )
    discrepancies = forms.CharField(
        label="Default Discrepancy Notes",
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        help_text="Optional text applied to all generated reviews if mismatches exist.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get("review_quarter"):
            self.initial["review_quarter"] = get_current_quarter_label()
        if not self.initial.get("review_date"):
            self.initial["review_date"] = timezone.now().strftime("%Y-%m-%dT%H:%M")
        self.fields["system"].queryset = System.objects.filter(is_active=True).order_by("name")
        self.fields["reviewed_by"].queryset = CustomUser.objects.filter(is_active=True).order_by("first_name", "last_name")
        self._apply_bootstrap_classes()

    def _apply_bootstrap_classes(self):
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                classes = widget.attrs.get("class", "")
                widget.attrs["class"] = (classes + " form-control").strip()


class QuarterlyActiveUserReviewForm(forms.ModelForm):
    review_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    review_quarter = forms.ChoiceField(
        choices=[],  # Will be populated in __init__
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Quarter"
    )

    class Meta:
        model = QuarterlyActiveUserReview
        fields = [
            "review_quarter",
            "system",
            "reviewed_by",
            "review_date",
            "total_active_users_in_external_system",
            "approved_users_count",
            "unapproved_users_count",
            "unapproved_users_list",
            "discrepancies",
            "review_completed",
        ]
        widgets = {
            "unapproved_users_list": forms.Textarea(attrs={"rows": 3}),
            "discrepancies": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate quarter choices for current and previous years
        current_year = timezone.now().year
        quarters = []
        for year in [current_year, current_year - 1]:
            for q in range(1, 5):
                quarters.append((f"{year}-Q{q}", f"Q{q} {year}"))
        self.fields["review_quarter"].choices = sorted(quarters, reverse=True)
        
        if not self.initial.get("review_quarter"):
            self.initial["review_quarter"] = get_current_quarter_label()
        if not self.initial.get("review_date"):
            self.initial["review_date"] = timezone.now().strftime("%Y-%m-%dT%H:%M")
        self._apply_bootstrap()

    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                classes = widget.attrs.get("class", "")
                widget.attrs["class"] = (classes + " form-control").strip()


class MonthlyObsoleteAccountReviewForm(forms.ModelForm):
    review_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    review_month = forms.DateField(
        widget=forms.DateInput(attrs={"type": "month"}),
        label="Review Month"
    )
    obsolete_accounts_identified = forms.JSONField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
        help_text="Provide JSON (list or object) describing obsolete accounts located.",
    )

    class Meta:
        model = MonthlyObsoleteAccountReview
        fields = [
            "review_month",
            "reviewed_by",
            "review_date",
            "obsolete_accounts_identified",
            "accounts_deactivated_in_external_systems",
            "accounts_pending_deactivation",
            "review_completed",
            "notes",
        ]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        now = timezone.now()
        default_month = now.strftime("%Y-%m")
        if not self.initial.get("review_month"):
            self.initial["review_month"] = default_month
        if not self.initial.get("review_date"):
            self.initial["review_date"] = now.strftime("%Y-%m-%dT%H:%M")
        self._apply_bootstrap()

    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                classes = widget.attrs.get("class", "")
                widget.attrs["class"] = (classes + " form-control").strip()


class AccessRemovalDocumentationForm(forms.ModelForm):
    removed_from_external_system_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )
    verified_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}),
    )

    class Meta:
        model = AccessRemovalDocumentation
        fields = [
            "user_system_access",
            "removed_from_external_system_date",
            "removed_by",
            "removal_reason",
            "verified_removal",
            "verified_by",
            "verified_date",
            "notes",
        ]
        widgets = {
            "removal_reason": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get("removed_from_external_system_date"):
            self.initial["removed_from_external_system_date"] = timezone.now().strftime("%Y-%m-%dT%H:%M")
        self._apply_bootstrap()

    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            else:
                classes = widget.attrs.get("class", "")
                widget.attrs["class"] = (classes + " form-control").strip()


from django import forms
from django.utils import timezone

from accounts.models import CustomUser
from systems.models import System

from .models import QuarterlyAccessReview, PermissionChangeDocumentation


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


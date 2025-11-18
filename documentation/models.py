from django.db import models


class StandardOperatingProcedure(models.Model):
    """
    Stores Standard Operating Procedures (SOPs) for access/change processes (RHG 4.4+).

    This provides in-application documentation and versioning for written procedures
    that can be presented as audit evidence.
    """

    title = models.CharField(
        max_length=255,
        help_text="SOP title, e.g. 'User Account Creation Process'",
    )
    version = models.CharField(
        max_length=50,
        help_text="Document version identifier, e.g. 'v1.0', '2025-Q4'",
    )
    content = models.TextField(
        help_text="Full SOP content in markdown or rich text form",
    )
    approved_by = models.ForeignKey(
        "accounts.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_sops",
        help_text="Person who approved this SOP version",
    )
    approved_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this SOP version was approved",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Mark as active to show this SOP in current procedures",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title", "-created_at"]
        verbose_name = "Standard Operating Procedure"
        verbose_name_plural = "Standard Operating Procedures"

    def __str__(self) -> str:
        return f"{self.title} ({self.version})"



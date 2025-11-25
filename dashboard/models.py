from django.conf import settings
from django.db import models


class ApplicationSetting(models.Model):
    """
    Lightweight key/value storage for privileged configuration toggles.
    Values are stored as JSON blobs to keep the model flexible so future
    settings can be added without additional migrations.
    """

    key = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='general')
    value = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='modified_application_settings',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['key']

    def __str__(self) -> str:
        return f"{self.label} ({self.key})"

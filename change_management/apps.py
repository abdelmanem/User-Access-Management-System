from django.apps import AppConfig


class ChangeManagementConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "change_management"
    verbose_name = "Change Management"
    
    def ready(self):
        """Register change management signals on app startup."""
        from . import signals
        signals.register_change_management_signals()



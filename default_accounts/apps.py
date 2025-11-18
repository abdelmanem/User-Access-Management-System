from django.apps import AppConfig


class DefaultAccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'default_accounts'
    verbose_name = "Default Account Governance"

    def ready(self):
        # Import signals for auto-seeding behavior
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid crashing on migrations if dependencies are not ready yet.
            pass

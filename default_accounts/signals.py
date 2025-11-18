from django.db.models.signals import post_save
from django.dispatch import receiver

from systems.models import System

from .services import create_default_accounts_for_system


@receiver(post_save, sender=System)
def seed_default_accounts_when_system_created(sender, instance: System, created: bool, **kwargs):
    """
    Automatically seed default account tracking rows whenever a new System is added.
    """
    if not created:
        return

    try:
        create_default_accounts_for_system(instance, created_by=getattr(instance, 'created_by', None))
    except Exception:
        # Fail-safe: don't block system creation if seeding fails.
        # Errors will be visible in logs for administrators to address.
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Failed to seed default accounts for system %s", instance)


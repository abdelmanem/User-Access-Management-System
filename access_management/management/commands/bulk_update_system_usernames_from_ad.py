from contextlib import nullcontext

from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.utils import timezone

from access_management.models import UserSystemAccess
from systems.models import System


class Command(BaseCommand):
    """
    Bulk-populate or update `UserSystemAccess.system_username` from the
    related `accounts.CustomUser` record (typically the AD username).

    Examples:
      - Dry-run for all LDAP / AD systems, only where system_username is empty:
            python manage.py bulk_update_system_usernames_from_ad --dry-run

      - Actually update for a specific system code (e.g. 'WIN_AD'):
            python manage.py bulk_update_system_usernames_from_ad --system-code WIN_AD

      - Force overwrite existing values:
            python manage.py bulk_update_system_usernames_from_ad --system-code WIN_AD --overwrite
    """

    help = (
        "Bulk fill the 'System Username' field on UserSystemAccess records "
        "from the related CustomUser's AD username / login."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--system-code",
            dest="system_code",
            help=(
                "Limit updates to a single system by its code (e.g. 'WIN_AD'). "
                "If omitted, all systems are considered."
            ),
        )
        parser.add_argument(
            "--only-empty",
            action="store_true",
            dest="only_empty",
            default=False,
            help="Only update records where system_username is currently blank/NULL.",
        )
        parser.add_argument(
            "--overwrite",
            action="store_true",
            dest="overwrite",
            default=False,
            help="Overwrite existing system_username values as well.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Show what would be changed, but do not write anything to the database.",
        )

    def handle(self, *args, **options):
        system_code = options.get("system_code")
        only_empty = options.get("only_empty")
        overwrite = options.get("overwrite")
        dry_run = options.get("dry_run")

        if only_empty and overwrite:
            self.stderr.write(
                self.style.ERROR(
                    "You cannot pass both --only-empty and --overwrite. "
                    "Use one or neither (default is to update only empty values)."
                )
            )
            return

        # Default behaviour: only touch empty values unless --overwrite is passed.
        if not overwrite:
            only_empty = True

        qs = UserSystemAccess.objects.select_related("user", "system")

        # Optionally limit by specific system code
        if system_code:
            try:
                system = System.objects.get(code=system_code)
            except System.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f"System with code '{system_code}' does not exist.")
                )
                return
            qs = qs.filter(system=system)
            self.stdout.write(
                self.style.WARNING(
                    f"Limiting updates to system: {system.name} ({system.code})"
                )
            )

        # Heuristic: if no system_code given, prefer systems that use LDAP/AD auth
        else:
            qs = qs.filter(system__authentication_type__in=["LDAP", "SSO"])

        if only_empty:
            qs = qs.filter(
                models.Q(system_username__isnull=True) | models.Q(system_username__exact="")
            )

        # We will copy from user.ad_username if set, otherwise fall back to user.username
        total_candidates = qs.count()
        if total_candidates == 0:
            self.stdout.write(self.style.WARNING("No UserSystemAccess records matched the filters."))
            return

        self.stdout.write(
            self.style.NOTICE(
                f"Found {total_candidates} UserSystemAccess records to evaluate "
                f"({'dry-run' if dry_run else 'live-update'} mode)."
            )
        )

        updated = 0
        skipped = 0
        now = timezone.now()

        # Wrap in a single transaction for safety (no effect in dry-run)
        ctx = transaction.atomic() if not dry_run else nullcontext()
        with ctx:
            for access in qs.iterator():
                user = access.user
                if not user:
                    skipped += 1
                    continue

                ad_username = getattr(user, "ad_username", None)
                source_username = (ad_username or user.username or "").strip()

                if not source_username:
                    skipped += 1
                    continue

                if not overwrite and access.system_username:
                    # Should not occur when only_empty is True, but keep for clarity.
                    skipped += 1
                    continue

                old_value = access.system_username
                access.system_username = source_username

                if dry_run:
                    self.stdout.write(
                        f"[DRY-RUN] Would set system_username for access #{access.id} "
                        f"user={user.username} system={access.system.code} "
                        f"from='{old_value or ''}' to='{source_username}'"
                    )
                else:
                    access.updated_at = now  # keep audit fields reasonably fresh if present
                    access.save(update_fields=["system_username", "updated_at"])

                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would update' if dry_run else 'Updated'} {updated} records. Skipped {skipped}."
            )
        )



from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand

from systems.models import SystemContract
from access_management.models import UserSystemAccess


class Command(BaseCommand):
    help = (
        "Recalculate email subscription contract dues from subscription tiers, "
        "and surface duplicated tier amounts."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Persist recalculated monthly/yearly dues onto the contract.",
        )
        parser.add_argument(
            "--apply-dates",
            action="store_true",
            help=(
                "For Email Subscription systems, sync contract renewal_date to the latest assignment end date. "
                "If any assignment is open-ended, renewal_date is left unchanged (still billable)."
            ),
        )
        parser.add_argument(
            "--system",
            dest="system_filter",
            help="Filter by system code or name (case-insensitive substring).",
        )

    def handle(self, *args, **options):
        system_filter = (options.get("system_filter") or "").strip()
        apply_changes = options.get("apply", False)
        apply_dates = options.get("apply_dates", False)

        contracts = (
            SystemContract.objects.select_related("system")
            .prefetch_related("subscription_tiers")
            .filter(system__system_type="Email Subscription")
        )
        if system_filter:
            contracts = contracts.filter(
                system__code__icontains=system_filter
            ) | contracts.filter(system__name__icontains=system_filter)

        updated = 0
        for contract in contracts:
            tiers = list(contract.subscription_tiers.all())
            active_assignments = self._get_active_assignments(contract.system_id)
            derived_start, derived_end = self._assignment_window(active_assignments)

            monthly = sum(
                (tier.monthly_billing_amount() or Decimal("0")) for tier in tiers
            )
            yearly = sum(
                (tier.yearly_billing_amount() or Decimal("0")) for tier in tiers
            )

            monthly = monthly.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            yearly = yearly.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            duplicate_groups = self._find_duplicate_tiers(tiers)
            dup_label = " (DUPLICATES!)" if duplicate_groups else ""

            self.stdout.write(
                f"[{contract.system.code}] {contract.system.name}: "
                f"monthly={monthly} {contract.contract_fee_currency or ''}, "
                f"yearly={yearly} {contract.contract_fee_currency or ''}{dup_label}"
            )
            if derived_start or derived_end:
                self.stdout.write(
                    f"  Assignment-driven window: start={derived_start or 'open'}, end={derived_end or 'open'}"
                )
            if apply_dates and derived_end:
                contract.renewal_date = derived_end
                self.stdout.write(f"  -> renewal_date synced to {derived_end}")
            elif apply_dates and derived_end is None:
                self.stdout.write("  -> open-ended assignments: renewal_date left unchanged")

            if duplicate_groups:
                for key, group in duplicate_groups:
                    name, price, freq = key
                    ids = ", ".join(str(t.id) for t in group)
                    self.stdout.write(
                        f"  - duplicate tier group: name/license={name}, "
                        f"price={price}, freq={freq}, tier_ids=[{ids}]"
                    )

            if apply_changes:
                contract.due_amount_monthly = monthly
                contract.due_amount_yearly = yearly
                update_fields = ["due_amount_monthly", "due_amount_yearly", "updated_at"]
                if apply_dates and derived_end:
                    update_fields.append("renewal_date")
                contract.save(update_fields=update_fields)
                updated += 1

        if apply_changes or apply_dates:
            self.stdout.write(self.style.SUCCESS(f"Updated {updated} contracts."))
        else:
            self.stdout.write(self.style.WARNING("Dry-run complete (no data changed). Use --apply to persist."))

    @staticmethod
    def _find_duplicate_tiers(tiers):
        """
        Flag potential duplicate tiers: same license/name, price, and billing frequency.
        Returns list of tuples[(key, tiers_in_group)].
        """
        groups = {}
        for tier in tiers:
            key = (
                (tier.license_category or tier.name or "").strip().lower(),
                tier.unit_price,
                tier.billing_frequency,
            )
            groups.setdefault(key, []).append(tier)

        return [(key, group) for key, group in groups.items() if len(group) > 1]

    @staticmethod
    def _get_active_assignments(system_id):
        """
        Fetch assignments that are Active or Approved for the system.
        """
        return UserSystemAccess.objects.filter(
            system_id=system_id,
            status__in=["Active", "Approved"],
        ).only("access_start_date", "access_end_date", "request_date")

    @staticmethod
    def _assignment_window(assignments):
        """
        Derive start/end window from assignments:
        - start: earliest access_start_date (fallback to request_date if no start)
        - end: latest access_end_date among those that have one; open-ended if any are None.
        """
        starts = []
        ends = []
        for a in assignments:
            if a.access_start_date:
                starts.append(a.access_start_date.date())
            elif a.request_date:
                starts.append(a.request_date.date())
            if a.access_end_date:
                ends.append(a.access_end_date.date())
            else:
                # Open-ended; force end to None
                return (min(starts) if starts else None, None)
        return (min(starts) if starts else None, max(ends) if ends else None)


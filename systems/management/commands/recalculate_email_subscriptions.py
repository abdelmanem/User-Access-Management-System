from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand

from systems.models import SystemContract


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
            "--system",
            dest="system_filter",
            help="Filter by system code or name (case-insensitive substring).",
        )

    def handle(self, *args, **options):
        system_filter = (options.get("system_filter") or "").strip()
        apply_changes = options.get("apply", False)

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
                contract.save(update_fields=["due_amount_monthly", "due_amount_yearly", "updated_at"])
                updated += 1

        if apply_changes:
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


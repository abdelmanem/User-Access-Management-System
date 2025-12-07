from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

from django.db import transaction
from django.db.models import Q

from .models import (
    DefaultAccount,
    DefaultAccountTemplate,
)


FALLBACK_TEMPLATE_DATA: Sequence[dict] = [
    # Database defaults
    {
        "system_type": "Database",
        "account_name": "Opera",
        "account_type": "Database",
        "removal_required": True,
        "notes": "Opera PMS database master account. Must be removed or rotated.",
    },
    {
        "system_type": "Database",
        "account_name": "SYS",
        "account_type": "Database",
        "removal_required": True,
        "notes": "Oracle SYS account. Track password rotation and lockdown.",
    },
    {
        "system_type": "Database",
        "account_name": "VISION",
        "account_type": "Database",
        "removal_required": True,
        "notes": "Vision/accounting platform default account.",
    },
    # PMS / Application defaults
    {
        "system_type": "Desktop Application",
        "account_name": "supervisor",
        "account_type": "Application",
        "removal_required": True,
        "notes": "PMS supervisor ID included in hotel images.",
    },
    {
        "system_type": "Desktop Application",
        "account_name": "Interface",
        "account_type": "Application",
        "removal_required": True,
        "notes": "PMS interface connector account.",
    },
    # Workstation Images
    {
        "system_type": "Operating System",
        "account_name": "LocalAdmin",
        "account_type": "Workstation",
        "removal_required": True,
        "notes": "Local administrator password must be rotated from imaging defaults.",
    },
    {
        "system_type": "Operating System",
        "account_name": "Technician",
        "account_type": "Workstation",
        "removal_required": True,
        "notes": "Pre-build tech account found on workstation images.",
    },
    # Server/ILO
    {
        "system_type": "Operating System",
        "account_name": "Administrator",
        "account_type": "Server",
        "removal_required": True,
        "notes": "Windows Server default Administrator credential.",
    },
    {
        "system_type": "Other",
        "account_name": "ILO",
        "account_type": "Server",
        "removal_required": True,
        "notes": "ILO / out-of-band interface default login.",
    },
    # Network & printers
    {
        "system_type": "Network Device",
        "account_name": "admin",
        "account_type": "Network Device",
        "removal_required": True,
        "notes": "Generic admin account present on switches/routers.",
    },
    {
        "system_type": "Network Device",
        "account_name": "cisco",
        "account_type": "Network Device",
        "removal_required": True,
        "notes": "Cisco factory default credential.",
    },
    {
        "system_type": "Other",
        "account_name": "printer_admin",
        "account_type": "Printer",
        "removal_required": True,
        "notes": "Common printer admin password (7777) must be rotated.",
    },
    # RHG-specific accounts
    {
        "system_type": "Any",
        "account_name": "michael.brandt",
        "account_type": "Application",
        "removal_required": True,
        "applies_to_all": True,
        "rhg_special_account": True,
        "notes": "Legacy RHG corporate account flagged for removal everywhere.",
    },
    {
        "system_type": "Any",
        "account_name": "roger.bergh",
        "account_type": "Application",
        "removal_required": True,
        "applies_to_all": True,
        "rhg_special_account": True,
        "notes": "Legacy RHG corporate account flagged for removal everywhere.",
    },
    # Hosted exceptions
    {
        "system_type": "Cloud Service",
        "account_name": "EMMA Database Root",
        "account_type": "Database",
        "removal_required": False,
        "default_status": "Not Applicable",
        "notes": "EMMA is hosted; hotels have no database access. Document as N/A.",
    },
]


def ensure_default_account_templates_seeded() -> None:
    """
    Ensures that baseline template entries exist so new systems get seeded defaults.
    Note: With the new System-based structure, templates should be created manually
    or through the admin interface. This function now just ensures the model is accessible.
    """
    # Templates are now created manually via the Template Registry interface
    # or can be seeded programmatically when systems are available
    pass


@dataclass
class DefaultAccountSeedResult:
    created: List[DefaultAccount]
    skipped: int = 0

    @property
    def created_count(self) -> int:
        return len(self.created)


def get_templates_for_system(system) -> Iterable[DefaultAccountTemplate]:
    """
    Returns template queryset for the given system (matches specific system or global templates).
    """
    ensure_default_account_templates_seeded()
    qs = DefaultAccountTemplate.objects.filter(
        Q(system=system) | Q(system__isnull=True, applies_to_all=True)
    )
    return qs.order_by('account_name')


@transaction.atomic
def create_default_accounts_for_system(system, created_by=None) -> DefaultAccountSeedResult:
    """
    Creates DefaultAccount rows for the provided system leveraging templates.
    """
    created_records: List[DefaultAccount] = []
    skipped = 0
    templates = list(get_templates_for_system(system))

    for template in templates:
        existing = DefaultAccount.objects.filter(
            system=system,
            account_name__iexact=template.account_name,
        ).exists()
        if existing:
            skipped += 1
            continue

        account = DefaultAccount.objects.create(
            template=template,
            system=system,
            account_name=template.account_name,
            account_type=template.account_type,
            status=template.default_status,
            removal_required=template.removal_required,
            is_rhg_special_account=template.rhg_special_account,
            remediation_notes=template.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        created_records.append(account)

    return DefaultAccountSeedResult(created=created_records, skipped=skipped)


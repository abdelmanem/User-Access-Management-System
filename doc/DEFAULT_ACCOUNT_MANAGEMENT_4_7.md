# Default Account Management (Audit 4.7)

**Last Updated:** 2025-11-18  
**Applies To:** User Access Management System v2.1+

> Tracks and documents the reset/removal of factory default accounts in external systems to satisfy RHG Access Control Policy (section 4.7) and PCI DSS audit evidence expectations.

## Objectives

1. **Document** every known default account (database, PMS, workstation images, network devices, printers, RHG legacy IDs).
2. **Track remediation** status (password reset, removal, N/A) with timestamped evidence and verifier identity.
3. **Integrate with system onboarding** so new systems inherit a checklist of default accounts that must be remediated immediately after installation.
4. **Provide dashboards/exports** proving compliance status to auditors.

## Data Model

| Model | Purpose |
|-------|---------|
| `DefaultAccount` | Primary registry entry per system + account (status, evidence, installation checklist, verifier metadata). |
| `DefaultAccountAction` | Append-only log of remediation actions (password reset, removal, verification, checklists). Updates parent status automatically. |
| `DefaultAccountTemplate` | Template catalog of common default accounts per system type (database, PMS, workstation image, RHG special). New systems auto-seed from this list. |

### Key Fields Captured

- `status` (`Pending`, `Active - Password Changed`, `Removed`, `Not Applicable`, `In Review`)
- `password_changed_in_external_system`, `password_changed_date`, `password_changed_by`, `password_change_reference`
- `removal_required`, `removed_from_external_system`, `removal_date`, `removal_confirmed_by`, `removal_reference`
- `installation_checklist_completed`, `installation_checklist_completed_date`, `installation_documented_by`, `installation_notes`
- `last_verified_date`, `last_verified_by`, `verification_artifact`
- `hosted_not_applicable_reason` (e.g., EMMA hosted databases)
- `is_rhg_special_account` (legacy accounts specifically called out by RHG)

## Default Account Dashboard

Route: `/default-accounts/`

Features:

- Summary cards for total accounts, pending remediation, password-changed, removed, N/A, RHG special, and attention required.
- Filtering by system, status, account type, quick filters (needs action, RHG, hosted/N/A).
- Table showing per-system account status, removal requirement, password reset/ removal evidence, verifier, and quick access to detail/action logging.
- Export button (`Export Evidence`) produces Excel file containing all captured metadata for auditors.

## Action Logging Workflow

1. Navigate to a specific default account (`/default-accounts/<id>/`).
2. Use **Log Action** to capture:
   - Action type (Password Reset, Removal, Not Applicable, Installation Checklist, Verification, Note)
   - Action date/time (when work occurred in external system)
   - Evidence reference (ticket #, screenshot path, vendor confirmation)
   - Notes / checklist details
3. System automatically updates parent `DefaultAccount` record (status, timestamps, responsible party) ensuring no double data entry.

## Template Registry

Route: `/default-accounts/templates/`

- Maintains the canonical library of default accounts per system type.
- Includes pre-populated entries for:
  - Oracle/Opera/VISION database accounts
  - PMS `supervisor`/`Interface`
  - Workstation `LocalAdmin`/`Technician`
  - Server `Administrator`, ILO
  - Network `admin`, `cisco`
  - Printers (`printer_admin`)
  - RHG-specific `michael.brandt`, `roger.bergh`
  - Hosted EMMA database entry (N/A)
- Administrators can add/update templates without touching Django admin.
- Templates flagged with **“applies to all systems”** automatically instantiate for every new system.

## System Installation Integration

- Whenever a new `System` is created, the `default_accounts` app seeds `DefaultAccount` rows using templates:
  - All matching `system_type` templates.
  - Any template marked `applies_to_all`.
- Each seeded record starts in `Pending` status with `removal_required` set according to the template.
- Run `/default-accounts/seed/system/<system_id>/` to backfill older systems.

## Evidence Checklist

| Requirement | Evidence in App |
|-------------|-----------------|
| Document password resets or removals for default accounts | `DefaultAccountAction` entries of type `password_reset` or `removal` with timestamps and references. |
| Track procedure for new installs | `installation_checklist_completed*` fields + `installation` action type per default account. |
| Maintain registry of default accounts | Dashboard export + `DefaultAccount` list filtered by system/account type. |
| RHG-specific account removal | `is_rhg_special_account` flag + quick filter to prove removal progress. |
| Hosted exceptions (EMMA) documented as N/A | Status = `Not Applicable` + `hosted_not_applicable_reason`. |

## Reporting & Exports

- **Excel Export**: `/default-accounts/export/` provides a full evidence sheet (system, statuses, timestamps, references).
- **Dashboard filters**: create on-screen reports for pending remediation, RHG legacy accounts, or hosted systems flagged N/A.
- **Template stats**: Template page shows counts of total/global/RHG templates for governance reviews.

## Operational Guidance

1. **During system onboarding:** confirm auto-generated default accounts, complete installation checklist, and record password resets/removals before go-live.
2. **During periodic reviews:** run dashboard quick filter `Needs Action` to ensure no pending entries; log verification actions quarterly.
3. **Prior to audits:** export Excel evidence and attach to audit packages alongside SOP references.
4. **Template maintenance:** update templates when new vendor defaults are discovered to keep auto-seeding accurate.

---
For questions or enhancements, contact the Security Engineering team or open an issue referencing *Default Account Management (4.7)*.


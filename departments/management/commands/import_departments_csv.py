from __future__ import annotations

import csv
import itertools
import re
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from departments.models import Department


class Command(BaseCommand):
    help = (
        "Import hierarchical departments from a CSV exported from another system.\n"
        "Accepted headers (case-insensitive):\n"
        "- division, department, section\n"
        "- or: 'Division E', 'Department En Name', 'Section En Name'\n"
        "Columns beyond these are ignored.\n\n"
        "Each row represents a path like Division → Department → Section.\n"
        "Blank deeper levels are allowed.\n\n"
        "Example usage:\n"
        "  python manage.py import_departments_csv path/to/file.csv\n"
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file")
        parser.add_argument(
            "--encoding",
            default="utf-8-sig",
            help="CSV encoding (default: utf-8-sig to handle BOM from Excel)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and show what would be created without saving",
        )
        parser.add_argument(
            "--delimiter",
            default=",",
            help="CSV delimiter (default: ,)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        encoding = options["encoding"]
        delimiter = options["delimiter"]
        dry_run = options["dry_run"]

        path = Path(csv_path)
        if not path.exists():
            raise CommandError(f"File not found: {csv_path}")

        with path.open(newline="", encoding=encoding) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            if not reader.fieldnames:
                raise CommandError("CSV file has no headers.")

            normalized_headers = [self._normalize(h) for h in reader.fieldnames]
            header_map = self._resolve_header_map(normalized_headers)
            if not header_map:
                raise CommandError(
                    "CSV must include headers for division/department/section.\n"
                    "Accepted header sets:\n"
                    " - division, department, section\n"
                    " - division e, department en name, section en name"
                )

            created = {"divisions": 0, "departments": 0, "teams": 0}
            seen_rows = 0
            for row_index, raw_row in enumerate(reader, start=2):
                seen_rows += 1
                values = {
                    key: (raw_row.get(original, "") or "").strip()
                    for key, original in header_map.items()
                }
                division = values.get("division") or ""
                department = values.get("department") or ""
                section = values.get("section") or ""

                if not division and not department and not section:
                    # skip empty line
                    continue

                if not division:
                    raise CommandError(f"Row {row_index}: 'division' is required")

                # Upsert Division (level 0)
                div_obj, div_created = self._get_or_create_department(
                    name=division,
                    parent=None,
                    level_type="Division",
                )
                if div_created:
                    created["divisions"] += 1

                parent = div_obj
                if department:
                    dep_obj, dep_created = self._get_or_create_department(
                        name=department,
                        parent=parent,
                        level_type="Department",
                    )
                    if dep_created:
                        created["departments"] += 1
                    parent = dep_obj

                if section:
                    team_obj, team_created = self._get_or_create_department(
                        name=section,
                        parent=parent,
                        level_type="Team",
                    )
                    if team_created:
                        created["teams"] += 1

            summary = (
                f"Processed {seen_rows} row(s). "
                f"Created: {created['divisions']} divisions, "
                f"{created['departments']} departments, "
                f"{created['teams']} teams."
            )
            if dry_run:
                self.stdout.write(self.style.WARNING("[DRY RUN] " + summary))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS(summary))

    # ----- helpers ---------------------------------------------------------
    def _normalize(self, header: str) -> str:
        return re.sub(r"\s+", " ", (header or "").strip().lower())

    def _resolve_header_map(self, headers: Iterable[str]) -> Optional[Dict[str, str]]:
        """
        Return a mapping from canonical keys to original header strings found in CSV.
        Canonical keys: division, department, section
        """
        header_list = list(headers)

        candidates = [
            # canonical
            {"division": "division", "department": "department", "section": "section"},
            # example given in screenshot
            {
                "division": "division e",
                "department": "department en name",
                "section": "section en name",
            },
        ]
        for cand in candidates:
            if all(cand[k] in header_list for k in ("division", "department", "section")):
                # map canonical key -> original header as in the file
                return {
                    key: next(
                        orig for orig in itertools.chain([cand[key]], []) if orig in header_list
                    )
                    or cand[key]
                    for key in ["division", "department", "section"]
                }

        # Try fuzzy resolution: pick best-effort matches
        fuzzy_map: Dict[str, Optional[str]] = {"division": None, "department": None, "section": None}
        for h in header_list:
            if fuzzy_map["division"] is None and any(k in h for k in ["division", "div"]):
                fuzzy_map["division"] = h
            elif fuzzy_map["department"] is None and any(k in h for k in ["department", "dept"]):
                fuzzy_map["department"] = h
            elif fuzzy_map["section"] is None and any(k in h for k in ["section", "team", "unit"]):
                fuzzy_map["section"] = h
        if all(v is not None for v in fuzzy_map.values()):
            return fuzzy_map  # type: ignore[return-value]
        return None

    def _get_or_create_department(
        self, *, name: str, parent: Optional[Department], level_type: str
    ) -> Tuple[Department, bool]:
        """
        Get or create a Department by name and parent, generating a unique code if needed.
        """
        existing = Department.objects.filter(name=name, parent_department=parent).first()
        if existing:
            # Make sure type matches the intended level if it's unset/mismatched
            if existing.department_type != level_type:
                existing.department_type = level_type
                existing.save(update_fields=["department_type"])
            return existing, False

        code = self._generate_unique_code(name)
        obj = Department.objects.create(
            name=name,
            code=code,
            parent_department=parent,
            department_type=level_type,
        )
        return obj, True

    def _generate_unique_code(self, name: str) -> str:
        """
        Create a short, unique code from the name within 50 chars, appending a counter if needed.
        """
        base = slugify(name).upper().replace("-", "")
        if not base:
            base = "DEPT"
        base = base[:50]
        code = base
        counter = 1
        while Department.objects.filter(code=code).exists():
            suffix = f"-{counter}"
            code = (base[: (50 - len(suffix))] + suffix)
            counter += 1
        return code



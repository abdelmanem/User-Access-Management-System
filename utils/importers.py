import csv
import io
from typing import Iterable, Tuple, List

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.dateparse import parse_date

from departments.models import Department
from systems.models import System

User = get_user_model()


class ImportErrorCollection(Exception):
    """Aggregate multiple validation errors for CSV imports."""

    def __init__(self, errors: Iterable[str]):
        self.errors = list(errors)
        message = '\n'.join(self.errors)
        super().__init__(message)


def _csv_reader(uploaded_file) -> csv.DictReader:
    """
    Normalise uploaded files/in-memory file-like objects into a CSV DictReader.
    Ensures UTF-8 decoding (with BOM support) and positions the pointer at the start.
    """
    if hasattr(uploaded_file, 'seek'):
        uploaded_file.seek(0)
    raw_data = uploaded_file.read()

    if isinstance(raw_data, bytes):
        raw_data = raw_data.decode('utf-8-sig')

    return csv.DictReader(io.StringIO(raw_data))


def _parse_bool(value, default=False):
    if value in (None, ''):
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'true', '1', 'yes', 'y', 't'}


def _collect_row_errors(row_number: int, errors: Iterable[str]) -> str:
    return f"Row {row_number}: " + '; '.join(errors)


def import_users_from_csv(file):
    """Import or update user records from a CSV file."""
    reader = _csv_reader(file)
    required_columns = {
        'username',
        'email',
        'first_name',
        'last_name',
        'employee_id',
        'phone_primary',
        'position',
    }
    errors = []

    with transaction.atomic():
        for index, row in enumerate(reader, start=2):  # Header is row 1
            missing_columns = [col for col in required_columns if not row.get(col)]
            if missing_columns:
                errors.append(_collect_row_errors(index, [f"Missing required columns: {', '.join(missing_columns)}"]))
                continue

            department = None
            department_code = row.get('department_code')
            if department_code:
                department = Department.objects.filter(code=department_code).first()
                if department is None:
                    errors.append(_collect_row_errors(index, [f"Department with code '{department_code}' not found"]))
                    continue

            join_date = parse_date(row.get('join_date') or '')

            defaults = {
                'username': row['username'].strip(),
                'email': row['email'].strip(),
                'first_name': row['first_name'].strip(),
                'last_name': row['last_name'].strip(),
                'employee_id': row['employee_id'].strip(),
                'phone_primary': row['phone_primary'].strip(),
                'position': row['position'].strip(),
                'employment_type': (row.get('employment_type') or 'Full-time').strip(),
                'employment_status': (row.get('employment_status') or 'Active').strip(),
                'department': department,
                'is_active': _parse_bool(row.get('is_active'), default=True),
            }

            optional_fields = [
                'phone_secondary',
                'personal_email',
                'job_title',
                'office_location',
                'office_room',
                'work_address',
                'city',
                'state_province',
                'country',
                'postal_code',
                'notes',
            ]

            for field_name in optional_fields:
                if row.get(field_name) not in (None, ''):
                    defaults[field_name] = row[field_name].strip()

            if join_date:
                defaults['join_date'] = join_date

            user, created = User.objects.update_or_create(
                employee_id=defaults['employee_id'],
                defaults=defaults,
            )

            password = row.get('password')
            if password:
                user.set_password(password)
                user.save(update_fields=['password'])
            elif created and not user.has_usable_password():
                user.set_unusable_password()
                user.save(update_fields=['password'])

        if errors:
            raise ImportErrorCollection(errors)


def import_departments_from_csv(file):
    """Import or update department records from a CSV file."""
    reader = _csv_reader(file)
    required_columns = {'name', 'code', 'department_type'}
    errors = []
    parent_links: List[Tuple[Department, str]] = []

    with transaction.atomic():
        for index, row in enumerate(reader, start=2):
            missing_columns = [col for col in required_columns if not row.get(col)]
            if missing_columns:
                errors.append(_collect_row_errors(index, [f"Missing required columns: {', '.join(missing_columns)}"]))
                continue

            defaults = {
                'name': row['name'].strip(),
                'description': (row.get('description') or '').strip(),
                'department_type': row['department_type'].strip(),
                'is_active': _parse_bool(row.get('is_active'), default=True),
            }

            optional_fields = [
                'cost_center',
                'budget_code',
                'office_location',
                'phone',
                'email',
            ]
            for field_name in optional_fields:
                if row.get(field_name) not in (None, ''):
                    defaults[field_name] = row[field_name].strip()

            department, _ = Department.objects.update_or_create(
                code=row['code'].strip(),
                defaults=defaults,
            )

            parent_code = row.get('parent_department_code')
            if parent_code:
                parent_links.append((department, parent_code.strip()))

        # Resolve parent relationships outside the main loop to ensure all departments exist.
        if not errors and parent_links:
            for department, parent_code in parent_links:
                parent = Department.objects.filter(code=parent_code).first()
                if parent is None:
                    errors.append(f"Parent department with code '{parent_code}' not found for department '{department.code}'")
                else:
                    if department.parent_department_id != parent.id:
                        department.parent_department = parent
                        department.save(update_fields=['parent_department'])

        if errors:
            raise ImportErrorCollection(errors)


def import_systems_from_csv(file):
    """Import or update system records from a CSV file."""
    reader = _csv_reader(file)
    required_columns = {'name', 'code', 'system_type', 'criticality_level', 'environment_type'}
    errors = []

    with transaction.atomic():
        for index, row in enumerate(reader, start=2):
            missing_columns = [col for col in required_columns if not row.get(col)]
            if missing_columns:
                errors.append(_collect_row_errors(index, [f"Missing required columns: {', '.join(missing_columns)}"]))
                continue

            system_owner = None
            owner_employee_id = row.get('system_owner_employee_id')
            if owner_employee_id:
                system_owner = User.objects.filter(employee_id=owner_employee_id.strip()).first()
                if system_owner is None:
                    errors.append(_collect_row_errors(index, [f"System owner with employee ID '{owner_employee_id}' not found"]))
                    continue

            technical_lead = None
            technical_lead_employee_id = row.get('technical_lead_employee_id')
            if technical_lead_employee_id:
                technical_lead = User.objects.filter(employee_id=technical_lead_employee_id.strip()).first()
                if technical_lead is None:
                    errors.append(_collect_row_errors(index, [f"Technical lead with employee ID '{technical_lead_employee_id}' not found"]))
                    continue

            defaults = {
                'name': row['name'].strip(),
                'description': (row.get('description') or '').strip(),
                'system_type': row['system_type'].strip(),
                'criticality_level': row['criticality_level'].strip(),
                'environment_type': row['environment_type'].strip(),
                'system_owner': system_owner,
                'technical_lead': technical_lead,
                'requires_approval': _parse_bool(row.get('requires_approval'), default=True),
                'is_active': _parse_bool(row.get('is_active'), default=True),
                'is_monitored': _parse_bool(row.get('is_monitored'), default=True),
            }

            optional_fields = [
                'url',
                'ip_address',
                'server_name',
                'version',
                'vendor',
                'vendor_contact',
                'support_contact',
                'documentation_url',
                'authentication_type',
                'data_classification',
                'backup_frequency',
                'maintenance_window',
            ]

            for field_name in optional_fields:
                if row.get(field_name) not in (None, ''):
                    defaults[field_name] = row[field_name].strip()

            System.objects.update_or_create(
                code=row['code'].strip(),
                defaults=defaults,
            )

        if errors:
            raise ImportErrorCollection(errors)
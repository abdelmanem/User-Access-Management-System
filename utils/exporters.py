import csv
import io
from django.http import HttpResponse


def _resolve_attribute(instance, attribute_path):
    """
    Resolve dotted or double-underscore attribute paths on a model instance.
    Supports attribute access, dictionary-style access, and callables.
    """
    current = instance
    for segment in attribute_path.split('__'):
        if current is None:
            break

        if isinstance(current, dict):
            current = current.get(segment)
        else:
            current = getattr(current, segment, None)

        if callable(current):
            current = current()

    return current


def export_to_csv(queryset, filename, fields):
    """
    Export a queryset to CSV.

    `fields` accepts either a sequence of strings or a sequence of
    `(header, attribute_path)` tuples. When a string is provided, it is
    used for both the header and the attribute path.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'

    writer = csv.writer(response)

    normalised_fields = []
    headers = []

    for field in fields:
        if isinstance(field, (list, tuple)) and len(field) == 2:
            header, attribute_path = field
        else:
            header = attribute_path = field

        headers.append(header)
        normalised_fields.append(attribute_path)

    writer.writerow(headers)

    for obj in queryset:
        row = []
        for attribute_path in normalised_fields:
            value = _resolve_attribute(obj, attribute_path)
            if isinstance(value, io.BytesIO):
                value = value.getvalue().decode('utf-8', errors='ignore')
            row.append(value if value is not None else '')
        writer.writerow(row)

    return response
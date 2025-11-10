from django import template

register = template.Library()


@register.filter
def percentage(value, total):
    """Return percentage (value / total * 100) rounded to one decimal place."""
    try:
        value = float(value)
        total = float(total)
    except (TypeError, ValueError):
        return 0

    if total == 0:
        return 0
    return round((value / total) * 100, 1)


@register.filter
def ratio(value, divisor):
    """Return ratio (value / divisor) rounded to one decimal place."""
    try:
        value = float(value)
        divisor = float(divisor)
    except (TypeError, ValueError):
        return 0

    if divisor == 0:
        return 0
    return round(value / divisor, 1)


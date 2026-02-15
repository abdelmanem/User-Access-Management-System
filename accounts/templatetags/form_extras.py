from django import template
from django.utils.safestring import mark_safe

register = template.Library()


def _merge_attrs(field, new_classes):
    """Helper to merge new classes with existing widget attrs."""
    if not hasattr(field, 'as_widget'):
        return None
    existing_attrs = field.field.widget.attrs.copy()
    existing_class = existing_attrs.get('class', '').strip()
    if existing_class:
        existing_attrs['class'] = f"{existing_class} {new_classes}".strip()
    else:
        existing_attrs['class'] = new_classes
    return existing_attrs


@register.filter(name='add_class')
def add_class(field, css_class):
    """Add CSS class(es) to a form field widget."""
    try:
        attrs = _merge_attrs(field, css_class)
        if attrs:
            return mark_safe(field.as_widget(attrs=attrs))
    except Exception:
        pass
    return field


@register.filter(name='add_error_class')
def add_error_class(field, css_class='is-invalid'):
    """Add error class only if field has errors."""
    try:
        if hasattr(field, 'errors') and field.errors and hasattr(field, 'as_widget'):
            attrs = _merge_attrs(field, css_class)
            if attrs:
                return mark_safe(field.as_widget(attrs=attrs))
    except Exception:
        pass
    return field


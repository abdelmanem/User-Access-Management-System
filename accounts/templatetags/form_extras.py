from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={**field.field.widget.attrs, 'class': css_class})
    return field


@register.filter(name='add_error_class')
def add_error_class(field, css_class='is-invalid'):
    if hasattr(field, 'errors') and field.errors and hasattr(field, 'as_widget'):
        existing = field.field.widget.attrs.get('class', '').strip()
        classes = f"{existing} {css_class}".strip() if existing else css_class
        return field.as_widget(attrs={**field.field.widget.attrs, 'class': classes})
    return field


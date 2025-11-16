from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key."""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def get_nested_item(dictionary, keys):
    """Get a nested item from a dictionary using dot-separated keys."""
    if dictionary is None:
        return None
    keys_list = keys.split('.')
    value = dictionary
    for key in keys_list:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
        if value is None:
            return None
    return value


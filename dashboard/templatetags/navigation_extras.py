from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active_class(context, *patterns):
    """
    Return ' active' when the current view name matches one of the provided patterns.

    Patterns support either exact view names (including namespace) or a trailing '*'
    wildcard to match prefixes (e.g. 'accounts:user_*').
    """
    request = context.get('request')
    if not request:
        return ''

    resolver_match = getattr(request, 'resolver_match', None)
    if not resolver_match:
        return ''

    view_name = resolver_match.view_name or ''

    for pattern in patterns:
        if not pattern:
            continue
        if pattern.endswith('*'):
            if view_name.startswith(pattern[:-1]):
                return ' active'
        elif view_name == pattern:
            return ' active'

    return ''


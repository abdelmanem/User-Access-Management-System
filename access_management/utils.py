"""
Utility functions for access management, including generic account detection
"""

# Generic username patterns that should not be used per RHG Access Control Policy
GENERIC_USERNAME_PATTERNS = [
    'admin',
    'administrator',
    'root',
    'user',
    'test',
    'guest',
    'demo',
    'temp',
    'temporary',
    'service',
    'system',
    'default',
    'operator',
    'support',
    'helpdesk',
    'help',
    'info',
    'mail',
    'postmaster',
    'webmaster',
    'noreply',
    'no-reply',
    'supervisor',  # Common in PMS systems
    'interface',  # Common in PMS systems
    'michael.brandt',  # Specific RHG account to be removed
    'roger.bergh',  # Specific RHG account to be removed
]


def is_generic_username(username):
    """
    Check if a username matches generic account patterns.
    
    Args:
        username: The username to check (string)
    
    Returns:
        bool: True if the username is generic, False otherwise
    """
    if not username:
        return False
    
    username_lower = username.lower().strip()
    
    # Check exact matches
    if username_lower in GENERIC_USERNAME_PATTERNS:
        return True
    
    # Check if username starts with generic patterns (e.g., "admin1", "test_user")
    for pattern in GENERIC_USERNAME_PATTERNS:
        if username_lower.startswith(pattern + '_') or username_lower.startswith(pattern + '.'):
            return True
        # Check if it's a variation like "admin1", "test123"
        if username_lower.startswith(pattern) and len(username_lower) > len(pattern):
            # Check if the rest is just numbers or common suffixes
            suffix = username_lower[len(pattern):]
            if suffix.isdigit() or suffix in ['_', '.', '-', '1', '2', '3']:
                return True
    
    return False


def detect_generic_accounts(queryset=None):
    """
    Detect all generic accounts in a queryset of UserSystemAccess objects.
    
    Args:
        queryset: QuerySet of UserSystemAccess objects (optional)
    
    Returns:
        QuerySet: Filtered queryset containing only generic accounts
    """
    from .models import UserSystemAccess
    
    if queryset is None:
        queryset = UserSystemAccess.objects.all()
    
    # Filter accounts where system_username matches generic patterns
    generic_accounts = []
    for access in queryset:
        if access.system_username and is_generic_username(access.system_username):
            generic_accounts.append(access.id)
    
    return queryset.filter(id__in=generic_accounts)


def get_generic_accounts_by_system(system=None):
    """
    Get all generic accounts for a specific system or all systems.
    
    Args:
        system: System object (optional)
    
    Returns:
        QuerySet: Generic accounts for the system
    """
    from .models import UserSystemAccess
    
    queryset = UserSystemAccess.objects.filter(is_generic_account=True)
    if system:
        queryset = queryset.filter(system=system)
    
    return queryset


def get_unremediated_generic_accounts():
    """
    Get all generic accounts that have not been remediated.
    
    Returns:
        QuerySet: Generic accounts that need remediation
    """
    from .models import UserSystemAccess
    
    return UserSystemAccess.objects.filter(
        is_generic_account=True,
        generic_account_remediated=False
    )


def validate_no_generic_username(username):
    """
    Validate that a username is not generic. Raises ValidationError if generic.
    
    Args:
        username: The username to validate
    
    Raises:
        ValidationError: If the username is generic
    """
    from django.core.exceptions import ValidationError
    
    if is_generic_username(username):
        raise ValidationError(
            f"Generic usernames are not allowed per RHG Access Control Policy. "
            f"'{username}' matches a generic account pattern."
        )


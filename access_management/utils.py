"""
Utility functions for access management, including generic account detection
and compliance helpers.
"""

from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

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


def identify_obsolete_accounts():
    """
    Identify accounts that should be reviewed for deactivation.

    Heuristics (can be extended with external data imports):
    - Users with employment_status = 'Terminated'
    - Users flagged inactive or with last_login older than 90 days
    - Assignments with expired end dates that are still Active/Approved
    - Assignments without recent reviews (>180 days)
    """
    from accounts.models import CustomUser
    from .models import UserSystemAccess

    now = timezone.now()
    inactive_threshold = now - timedelta(days=90)
    stale_review_threshold = now - timedelta(days=180)

    terminated_users = CustomUser.objects.filter(
        Q(employment_status__iexact='Terminated') | Q(is_active=False)
    )
    inactive_users = CustomUser.objects.filter(
        last_login__isnull=False,
        last_login__lt=inactive_threshold,
        is_active=True,
    )

    expired_assignments = UserSystemAccess.objects.filter(
        access_end_date__isnull=False,
        access_end_date__lt=now,
        status__in=['Active', 'Approved'],
    )

    stale_reviews = UserSystemAccess.objects.filter(
        last_review_date__lt=stale_review_threshold,
        status__in=['Active', 'Approved'],
    )

    return {
        'terminated_users': terminated_users,
        'inactive_users': inactive_users,
        'expired_assignments': expired_assignments,
        'stale_reviews': stale_reviews,
    }


def get_unapproved_access_records():
    """
    Identify active assignments that appear to be missing approvals.
    """
    from .models import UserSystemAccess

    return UserSystemAccess.objects.select_related('user', 'system').filter(
        status__in=['Active', 'Approved'],
    ).filter(
        Q(approved_by__isnull=True)
        | Q(system_owner_approved=False)
        | Q(approval_date__isnull=True)
    )


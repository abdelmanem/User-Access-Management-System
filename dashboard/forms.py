from django import forms

from systems.models import System


class ActiveDirectorySettingsForm(forms.Form):
    """
    Allows privileged users to configure basic AD integration metadata.
    """

    enabled = forms.BooleanField(
        required=False,
        label='Enable directory sync',
        help_text='When enabled, scheduled sync jobs will run using the settings below.',
    )
    domain_controller = forms.CharField(
        required=False,
        max_length=255,
        label='Domain Controller',
        help_text='Hostname or IP of the preferred domain controller.',
    )
    base_dn = forms.CharField(
        required=False,
        max_length=255,
        label='Base DN',
        help_text='LDAP base distinguished name (e.g., DC=corp,DC=example,DC=com).',
    )
    service_account = forms.CharField(
        required=False,
        max_length=255,
        label='Service Account',
        help_text='Account used to perform LDAP lookups. Stored securely elsewhere.',
    )
    sync_frequency = forms.ChoiceField(
        choices=[
            ('hourly', 'Hourly'),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
        ],
        initial='daily',
        label='Sync Frequency',
    )


class DatabaseMaintenanceForm(forms.Form):
    """
    Captures retention preferences before running purge jobs.
    """

    retention_days = forms.IntegerField(
        min_value=30,
        max_value=3650,
        initial=365,
        label='Retention Window (days)',
        help_text='Records older than this will be purged.',
    )
    confirm = forms.BooleanField(
        required=True,
        label='Confirm purge',
        help_text='Acknowledge that the purge operation cannot be undone.',
    )


class SystemSeedForm(forms.Form):
    """
    Lets admins trigger seed utilities either for templates or per-system data.
    """

    SEED_SCOPE_CHOICES = [
        ('template_catalog', 'Template Catalog'),
        ('system_defaults', 'Specific System Defaults'),
    ]

    seed_scope = forms.ChoiceField(
        choices=SEED_SCOPE_CHOICES,
        initial='template_catalog',
        label='Seed Scope',
    )
    target_system = forms.ModelChoiceField(
        queryset=System.objects.none(),
        required=False,
        label='Target System',
        help_text='Required when seeding defaults for a specific system.',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['target_system'].queryset = System.objects.order_by('name')


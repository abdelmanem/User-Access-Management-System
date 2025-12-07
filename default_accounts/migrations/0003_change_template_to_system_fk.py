# Generated manually for changing DefaultAccountTemplate from system_type to System FK

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('default_accounts', '0002_seed_default_account_templates'),
        ('systems', '0001_initial'),
    ]

    operations = [
        # First, drop the old unique_together constraint that uses system_type
        migrations.AlterUniqueTogether(
            name='defaultaccounttemplate',
            unique_together=set(),
        ),
        # Add the new system ForeignKey field (nullable)
        migrations.AddField(
            model_name='defaultaccounttemplate',
            name='system',
            field=models.ForeignKey(
                blank=True,
                help_text="Specific system this template applies to. Leave blank and enable 'Applies to all' for global templates.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='default_account_templates',
                to='systems.system',
            ),
        ),
        # Remove the old system_type field
        migrations.RemoveField(
            model_name='defaultaccounttemplate',
            name='system_type',
        ),
        # Add the new unique_together constraint with system
        migrations.AlterUniqueTogether(
            name='defaultaccounttemplate',
            unique_together={('system', 'account_name')},
        ),
    ]


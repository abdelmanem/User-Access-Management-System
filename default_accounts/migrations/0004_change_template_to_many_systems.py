# Generated manually for changing DefaultAccountTemplate from single System FK to ManyToMany

from django.db import migrations, models
import django.db.models.deletion


def migrate_system_to_systems(apps, schema_editor):
    """Migrate data from system FK to systems M2M."""
    DefaultAccountTemplate = apps.get_model('default_accounts', 'DefaultAccountTemplate')
    System = apps.get_model('systems', 'System')
    
    # Use order_by() to avoid issues with model's default ordering
    for template in DefaultAccountTemplate.objects.all().order_by('id'):
        if hasattr(template, 'system_id') and template.system_id:  # If template had a system FK
            template.systems.add(template.system_id)
        # Templates with system=None and applies_to_all=True remain as global templates


class Migration(migrations.Migration):

    dependencies = [
        ('default_accounts', '0003_change_template_to_system_fk'),
        ('systems', '0001_initial'),
    ]

    operations = [
        # Add the new systems ManyToMany field
        migrations.AddField(
            model_name='defaultaccounttemplate',
            name='systems',
            field=models.ManyToManyField(
                blank=True,
                help_text="Specific systems this template applies to. Leave empty and enable 'Applies to all' for global templates.",
                related_name='default_account_templates',
                to='systems.system',
            ),
        ),
        # Remove the old unique_together constraint first (before removing field)
        migrations.AlterUniqueTogether(
            name='defaultaccounttemplate',
            unique_together=set(),
        ),
        # Migrate data: copy system FK to systems M2M (before removing the field)
        migrations.RunPython(
            code=migrate_system_to_systems,
            reverse_code=migrations.RunPython.noop,
        ),
        # Remove the old system ForeignKey field
        migrations.RemoveField(
            model_name='defaultaccounttemplate',
            name='system',
        ),
        # Update ordering after all field changes are complete
        migrations.AlterModelOptions(
            name='defaultaccounttemplate',
            options={'ordering': ['account_name'], 'verbose_name': 'Default Account Template', 'verbose_name_plural': 'Default Account Templates'},
        ),
    ]


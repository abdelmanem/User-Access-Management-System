from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_ldapconfiguration'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ldapconfiguration',
            name='bind_password',
        ),
    ]



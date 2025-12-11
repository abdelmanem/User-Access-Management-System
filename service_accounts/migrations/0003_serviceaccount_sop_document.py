from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('service_accounts', '0002_serviceaccount_admin_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='serviceaccount',
            name='sop_document',
            field=models.FileField(blank=True, help_text='Upload SOP file for this account', null=True, upload_to='service_accounts/sop_documents/'),
        ),
    ]


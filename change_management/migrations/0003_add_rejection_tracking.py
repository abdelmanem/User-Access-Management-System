"""
Migration for adding rejection tracking fields to AccountChangeRequest.

This migration adds explicit rejection tracking with timestamps and user tracking
for both System Owner and IT rejections.
"""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('change_management', '0005_alter_accountchangerequest_system'),  # Latest migration
        ('accounts', '0001_initial'),  # Adjust as needed
    ]

    operations = [
        # System Owner rejection fields
        migrations.AddField(
            model_name='accountchangerequest',
            name='system_owner_rejected',
            field=models.BooleanField(
                default=False,
                help_text='System Owner has rejected this change request'
            ),
        ),
        migrations.AddField(
            model_name='accountchangerequest',
            name='system_owner_rejection_date',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='When the System Owner rejected this change request'
            ),
        ),
        migrations.AddField(
            model_name='accountchangerequest',
            name='system_owner_rejection_reason',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Reason for System Owner rejection'
            ),
        ),
        migrations.AddField(
            model_name='accountchangerequest',
            name='system_owner_rejected_by',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='system_owner_rejections',
                to='accounts.customuser',
                help_text='User who rejected as System Owner'
            ),
        ),
        
        # IT rejection fields
        migrations.AddField(
            model_name='accountchangerequest',
            name='it_rejected',
            field=models.BooleanField(
                default=False,
                help_text='IT has rejected this change request'
            ),
        ),
        migrations.AddField(
            model_name='accountchangerequest',
            name='it_rejection_date',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='When IT rejected this change request'
            ),
        ),
        migrations.AddField(
            model_name='accountchangerequest',
            name='it_rejection_reason',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Reason for IT rejection'
            ),
        ),
        migrations.AddField(
            model_name='accountchangerequest',
            name='it_rejected_by',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='it_rejections',
                to='accounts.customuser',
                help_text='User who rejected as IT approver'
            ),
        ),
        
        # Add updated_at timestamp
        migrations.AddField(
            model_name='accountchangerequest',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                help_text='Last updated timestamp'
            ),
        ),
        
        # Create indexes for rejection tracking
        migrations.AddIndex(
            model_name='accountchangerequest',
            index=models.Index(
                fields=['system_owner_rejected', '-created_at'],
                name='chg_mgmt_owner_rejected_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='accountchangerequest',
            index=models.Index(
                fields=['it_rejected', '-created_at'],
                name='chg_mgmt_it_rejected_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='accountchangerequest',
            index=models.Index(
                fields=['status', 'system_owner_rejected', '-created_at'],
                name='chg_mgmt_status_owner_rejected_idx'
            ),
        ),
    ]

"""
API Serializers for Change Management integration with REST endpoints.

Provides serializers for:
- Change requests
- Change approvals
- Change workflows
"""

from rest_framework import serializers
from .models import AccountChangeRequest
from accounts.models import CustomUser
from systems.models import System


class CustomUserBriefSerializer(serializers.ModelSerializer):
    """Brief user serializer for nested representation."""
    full_name = serializers.CharField(source='get_full_name')
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email', 'department']


class SystemBriefSerializer(serializers.ModelSerializer):
    """Brief system serializer for nested representation."""
    
    class Meta:
        model = System
        fields = ['id', 'name', 'code', 'system_type', 'criticality_level']


class AccountChangeRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing account change requests."""
    user = CustomUserBriefSerializer(read_only=True)
    system = SystemBriefSerializer(read_only=True)
    requested_by = CustomUserBriefSerializer(read_only=True)
    system_owner = CustomUserBriefSerializer(read_only=True)
    
    class Meta:
        model = AccountChangeRequest
        fields = [
            'id',
            'change_type',
            'user',
            'system',
            'requested_by',
            'business_justification',
            'status',
            'system_owner_approved',
            'system_owner_approval_date',
            'completed_in_external_system',
            'created_at',
        ]
        read_only_fields = fields


class AccountChangeRequestDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for account change request detail view."""
    user = CustomUserBriefSerializer(read_only=True)
    system = SystemBriefSerializer(read_only=True)
    requested_by = CustomUserBriefSerializer(read_only=True)
    system_owner = CustomUserBriefSerializer(read_only=True)
    it_approval = CustomUserBriefSerializer(read_only=True)
    
    class Meta:
        model = AccountChangeRequest
        fields = [
            'id',
            'change_type',
            'user',
            'system',
            'requested_by',
            'business_justification',
            'system_owner',
            'system_owner_approved',
            'system_owner_approval_date',
            'system_owner_approval_notes',
            'it_approval',
            'it_approval_date',
            'status',
            'completed_in_external_system',
            'completed_date',
            'created_at',
        ]
        read_only_fields = [
            'id', 'created_at', 'user', 'system', 'requested_by'
        ]


class ChangeApprovalSerializer(serializers.Serializer):
    """Serializer for approving/rejecting change requests."""
    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'mark_completed'],
        help_text="Action to take on the change request"
    )
    approval_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notes for approval/rejection"
    )
    
    def validate(self, data):
        if data.get('action') == 'reject' and not data.get('approval_notes'):
            raise serializers.ValidationError(
                "Rejection requires approval_notes"
            )
        return data


class ChangeWorkflowStatusSerializer(serializers.Serializer):
    """Serializer for changing change request workflow status."""
    status = serializers.ChoiceField(
        choices=AccountChangeRequest.STATUS_CHOICES,
        help_text="New status for the change request"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notes for the status change"
    )


class ChangeRequestStatisticsSerializer(serializers.Serializer):
    """Serializer for change request statistics."""
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    approved_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()
    rejected_requests = serializers.IntegerField()
    average_approval_time_hours = serializers.FloatField()
    by_system = serializers.DictField()
    by_change_type = serializers.DictField()
    by_status = serializers.DictField()


class BulkChangeRequestSerializer(serializers.Serializer):
    """Serializer for bulk operations on change requests."""
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of change request IDs"
    )
    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'complete', 'cancel'],
        help_text="Bulk action to perform"
    )
    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Notes for the bulk action"
    )

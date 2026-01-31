"""
Additional Django forms for new IAM models: Approval, Evidence, Attestation.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Approval, ApprovalWorkflow, EvidenceArtifact, 
    Attestation, UserSystemAccess
)


class ApprovalForm(forms.ModelForm):
    """Form for approving or rejecting an access request with SOD awareness."""
    
    class Meta:
        model = Approval
        fields = ['approved', 'comments']
        widgets = {
            'approved': forms.RadioSelect(choices=[(True, 'Approve'), (False, 'Reject')]),
            'comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Approval comments or rejection reason...'
            })
        }
    
    def __init__(self, *args, workflow=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.workflow = workflow
        if 'approved' in self.fields:
            self.fields['approved'].widget.attrs['class'] = 'form-check-input'
    
    def clean(self):
        cleaned_data = super().clean()
        approved = cleaned_data.get('approved')
        
        # Check for COI if approving
        if approved and self.workflow:
            approver = self.instance.approver
            if approver and self.workflow.has_conflict_of_interest(approver):
                raise ValidationError(
                    'You have a conflict of interest and cannot approve this access.'
                )
        
        return cleaned_data


class EvidenceArtifactForm(forms.ModelForm):
    """Form for uploading evidence (screenshots, documents, etc.)."""
    
    class Meta:
        model = EvidenceArtifact
        fields = ['artifact_type', 'file_artifact']
        widgets = {
            'artifact_type': forms.Select(attrs={'class': 'form-select'}),
            'file_artifact': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.png,.jpg,.jpeg,.gif,.doc,.docx,.xls,.xlsx'
            })
        }
    
    def clean_file_artifact(self):
        file = self.cleaned_data.get('file_artifact')
        if file:
            # Max 50MB
            if file.size > 50 * 1024 * 1024:
                raise ValidationError('File size cannot exceed 50MB')
        return file


class AttestationForm(forms.ModelForm):
    """Form for formal attestation with legal acknowledgments."""
    
    agree_to_statement = forms.BooleanField(
        required=True,
        label='I attest that the above information is correct and complete.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    agree_to_legal = forms.BooleanField(
        required=True,
        label='I understand that false attestation may result in legal consequences.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Attestation
        fields = ['signature_method']
        widgets = {
            'signature_method': forms.RadioSelect(attrs={'class': 'form-check-input'})
        }
    
    def __init__(self, *args, statement_text=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.statement_text = statement_text or ''
    
    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('agree_to_statement'):
            raise ValidationError('You must attest to the statement.')
        if not cleaned_data.get('agree_to_legal'):
            raise ValidationError('You must acknowledge the legal consequences.')
        return cleaned_data


class AccessApproveForm(forms.Form):
    """Quick approve/reject form for access assignments."""
    
    DECISION_CHOICES = [
        ('approve', 'Approve'),
        ('reject', 'Reject'),
    ]
    
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional comments...'
        })
    )
    
    acknowledge_risk = forms.BooleanField(
        required=False,
        label='I acknowledge the access risk assessment',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class RevokeAccessForm(forms.Form):
    """Form for revoking access with documentation."""
    
    REVOKE_REASONS = [
        ('role_change', 'Role Change'),
        ('termination', 'Employee Termination'),
        ('security', 'Security Violation'),
        ('unused', 'Unused Access'),
        ('other', 'Other'),
    ]
    
    reason = forms.ChoiceField(
        choices=REVOKE_REASONS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    details = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Details about the revocation...'
        })
    )
    
    verified_removal = forms.BooleanField(
        required=False,
        label='I have verified that access has been removed from the external system',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

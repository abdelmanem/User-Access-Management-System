# Copilot Integration

This guide covers integrating UAMS with Copilot for AI-assisted access management and recommendations.

![Copilot Integration](../images/copilot-integration.png)

## Overview

Copilot integration provides AI-powered assistance for access management decisions, recommendations, and automation.

## What is Copilot?

Copilot integration offers:

- AI-powered access recommendations
- Automated access review suggestions
- Anomaly detection
- Access pattern analysis
- Risk assessment

## Integration Architecture

### Components

```
UAMS Application
    ↓
Copilot API Client
    ↓
Copilot Service
    ↓
AI/ML Models
```

## Configuration

### Installation

```bash
# Install Copilot client
pip install copilot-client
```

### Settings Configuration

```python
# settings.py
COPILOT_ENABLED = True
COPILOT_API_KEY = 'your-api-key'
COPILOT_ENDPOINT = 'https://copilot.example.com/api'
COPILOT_MODEL = 'access-management-v1'
```

### Environment Variables

```env
COPILOT_ENABLED=True
COPILOT_API_KEY=your-api-key
COPILOT_ENDPOINT=https://copilot.example.com/api
COPILOT_MODEL=access-management-v1
```

## Implementation

### Copilot Client Setup

```python
# utils/copilot_client.py
from copilot_client import CopilotClient
from django.conf import settings

class UAMSCopilotClient:
    def __init__(self):
        if settings.COPILOT_ENABLED:
            self.client = CopilotClient(
                api_key=settings.COPILOT_API_KEY,
                endpoint=settings.COPILOT_ENDPOINT,
                model=settings.COPILOT_MODEL
            )
        else:
            self.client = None
    
    def get_access_recommendation(self, user, system, context=None):
        """Get AI recommendation for access grant"""
        if not self.client:
            return None
        
        prompt = f"""
        Should user {user.username} ({user.get_full_name()}) 
        be granted {context.get('access_level', 'Read')} access 
        to system {system.name}?
        
        User context:
        - Department: {user.department.name if user.department else 'N/A'}
        - Role: {user.role}
        - Current access: {context.get('current_access_count', 0)} systems
        
        System context:
        - Type: {system.system_type}
        - Category: {system.category}
        - Justification: {context.get('justification', 'N/A')}
        """
        
        response = self.client.get_recommendation(prompt)
        return response
    
    def analyze_access_patterns(self, user):
        """Analyze user access patterns"""
        if not self.client:
            return None
        
        access_records = AccessRecord.objects.filter(
            user=user,
            is_active=True
        )
        
        context = {
            'user_id': user.id,
            'access_count': access_records.count(),
            'systems': [ar.system.name for ar in access_records],
            'departments': [ar.user.department.name for ar in access_records],
        }
        
        return self.client.analyze_patterns(context)
    
    def detect_anomalies(self, access_record):
        """Detect anomalies in access grants"""
        if not self.client:
            return None
        
        context = {
            'user_id': access_record.user.id,
            'system_id': access_record.system.id,
            'access_level': access_record.access_level,
            'granted_by': access_record.granted_by.id if access_record.granted_by else None,
        }
        
        return self.client.detect_anomalies(context)
```

## Use Cases

### Access Recommendation

Get AI-powered recommendations for access grants:

```python
# access_management/views.py
from utils.copilot_client import UAMSCopilotClient

def grant_access_with_recommendation(request, user_id, system_id):
    """Grant access with Copilot recommendation"""
    user = User.objects.get(id=user_id)
    system = System.objects.get(id=system_id)
    
    copilot = UAMSCopilotClient()
    recommendation = copilot.get_access_recommendation(
        user=user,
        system=system,
        context={
            'justification': request.POST.get('justification'),
            'access_level': request.POST.get('access_level'),
        }
    )
    
    if recommendation and recommendation.get('risk_level') == 'high':
        # Flag for additional review
        return render(request, 'access_management/high_risk_warning.html', {
            'recommendation': recommendation,
        })
    
    # Proceed with access grant
    # ...
```

### Anomaly Detection

Detect unusual access patterns:

```python
# access_management/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from access_management.models import AccessRecord
from utils.copilot_client import UAMSCopilotClient

@receiver(post_save, sender=AccessRecord)
def check_access_anomalies(sender, instance, created, **kwargs):
    """Check for anomalies when access is granted"""
    if created and instance.is_active:
        copilot = UAMSCopilotClient()
        anomalies = copilot.detect_anomalies(instance)
        
        if anomalies and anomalies.get('is_anomaly'):
            # Flag for review
            send_anomaly_alert(instance, anomalies)
```

### Access Review Assistance

Get AI suggestions for access reviews:

```python
def get_review_suggestions(access_record):
    """Get AI suggestions for access review"""
    copilot = UAMSCopilotClient()
    
    context = {
        'access_record_id': access_record.id,
        'user_id': access_record.user.id,
        'system_id': access_record.system.id,
        'days_since_grant': (timezone.now().date() - access_record.granted_date.date()).days,
        'last_review_date': access_record.last_reviewed_date,
    }
    
    suggestions = copilot.get_review_suggestions(context)
    return suggestions
```

## Risk Assessment

### Risk Scoring

```python
def assess_access_risk(user, system, access_level):
    """Assess risk of access grant"""
    copilot = UAMSCopilotClient()
    
    risk_factors = {
        'user_role': user.role,
        'system_category': system.category,
        'access_level': access_level,
        'user_department': user.department.name if user.department else None,
        'user_access_count': AccessRecord.objects.filter(
            user=user,
            is_active=True
        ).count(),
    }
    
    risk_score = copilot.assess_risk(risk_factors)
    return risk_score
```

## Integration Points

### Access Grant Workflow

```python
def grant_access_with_copilot(user, system, access_level, justification):
    """Grant access with Copilot analysis"""
    copilot = UAMSCopilotClient()
    
    # Get recommendation
    recommendation = copilot.get_access_recommendation(
        user, system, {'justification': justification}
    )
    
    # Assess risk
    risk = copilot.assess_access_risk(user, system, access_level)
    
    # Create access record
    access = AccessRecord.objects.create(
        user=user,
        system=system,
        access_level=access_level,
        justification=justification,
        copilot_recommendation=recommendation,
        risk_score=risk.get('score'),
    )
    
    return access
```

## Security Considerations

### Data Privacy

- User data is sent to Copilot API
- Ensure compliance with data privacy regulations
- Consider data anonymization for sensitive information

### API Security

- Secure API key storage
- Encrypted communications
- Rate limiting
- Access logging

## Best Practices

1. **Review Recommendations**: Always review AI recommendations
2. **Human Oversight**: Maintain human oversight for critical decisions
3. **Continuous Learning**: Update models based on feedback
4. **Privacy**: Protect user privacy
5. **Transparency**: Document AI decisions

## Troubleshooting

### API Connection

```python
# Test Copilot connection
from utils.copilot_client import UAMSCopilotClient

client = UAMSCopilotClient()
if client.client:
    try:
        response = client.client.health_check()
        print(f"Connected: {response}")
    except Exception as e:
        print(f"Connection failed: {e}")
```

### Recommendation Quality

Monitor recommendation quality and adjust prompts/models as needed.

## Next Steps

- [Integrations](integrations.md) - General integration guide
- [Best Practices](../best_practices.md) - Recommended practices
- [Configuration](../configuration.md) - System configuration

---

For additional AI/ML integration options, see [Integrations Overview](integrations.md).


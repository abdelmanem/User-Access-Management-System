# MCP Server Integration

This guide covers integrating UAMS with Model Context Protocol (MCP) servers for enhanced AI and automation capabilities.

![MCP Server Integration](../images/mcp-server-integration.png)

## Overview

MCP Server integration enables UAMS to interact with Model Context Protocol servers, providing structured access to UAMS data and functionality for AI models and automation tools.

## What is MCP?

Model Context Protocol (MCP) is a protocol for:

- Structured data access
- AI model integration
- Automation workflows
- Context-aware operations

## Integration Architecture

### Components

```
UAMS Application
    ↓
MCP Server
    ↓
MCP Protocol
    ↓
AI Models / Automation Tools
```

## Configuration

### Installation

```bash
# Install MCP server library
pip install mcp-server
```

### Settings Configuration

```python
# settings.py
MCP_SERVER_ENABLED = True
MCP_SERVER_PORT = 8001
MCP_SERVER_HOST = 'localhost'
MCP_SERVER_AUTH_TOKEN = 'your-auth-token'
```

### Environment Variables

```env
MCP_SERVER_ENABLED=True
MCP_SERVER_PORT=8001
MCP_SERVER_HOST=localhost
MCP_SERVER_AUTH_TOKEN=your-auth-token
```

## Implementation

### MCP Server Setup

```python
# mcp_server/server.py
from mcp_server import MCPServer
from django.conf import settings

class UAMSMCPServer:
    def __init__(self):
        if settings.MCP_SERVER_ENABLED:
            self.server = MCPServer(
                host=settings.MCP_SERVER_HOST,
                port=settings.MCP_SERVER_PORT,
                auth_token=settings.MCP_SERVER_AUTH_TOKEN
            )
            self.setup_handlers()
        else:
            self.server = None
    
    def setup_handlers(self):
        """Setup MCP protocol handlers"""
        # User operations
        self.server.register_handler('get_user', self.get_user)
        self.server.register_handler('list_users', self.list_users)
        self.server.register_handler('create_user', self.create_user)
        
        # Access operations
        self.server.register_handler('get_access', self.get_access)
        self.server.register_handler('list_access', self.list_access)
        self.server.register_handler('grant_access', self.grant_access)
        
        # System operations
        self.server.register_handler('get_system', self.get_system)
        self.server.register_handler('list_systems', self.list_systems)
    
    def get_user(self, user_id):
        """Get user information"""
        from accounts.models import User
        try:
            user = User.objects.get(id=user_id)
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'department': user.department.name if user.department else None,
                'role': user.role,
            }
        except User.DoesNotExist:
            return {'error': 'User not found'}
    
    def list_users(self, filters=None):
        """List users with optional filters"""
        from accounts.models import User
        queryset = User.objects.filter(is_active=True)
        
        if filters:
            if 'department' in filters:
                queryset = queryset.filter(department__name=filters['department'])
            if 'role' in filters:
                queryset = queryset.filter(role=filters['role'])
        
        return [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'full_name': user.get_full_name(),
        } for user in queryset]
    
    def get_access(self, access_id):
        """Get access record information"""
        from access_management.models import AccessRecord
        try:
            access = AccessRecord.objects.get(id=access_id)
            return {
                'id': access.id,
                'user': {
                    'id': access.user.id,
                    'username': access.user.username,
                    'full_name': access.user.get_full_name(),
                },
                'system': {
                    'id': access.system.id,
                    'name': access.system.name,
                },
                'access_level': access.access_level,
                'is_active': access.is_active,
                'granted_date': access.granted_date.isoformat(),
            }
        except AccessRecord.DoesNotExist:
            return {'error': 'Access record not found'}
    
    def list_access(self, filters=None):
        """List access records with optional filters"""
        from access_management.models import AccessRecord
        queryset = AccessRecord.objects.filter(is_active=True)
        
        if filters:
            if 'user_id' in filters:
                queryset = queryset.filter(user_id=filters['user_id'])
            if 'system_id' in filters:
                queryset = queryset.filter(system_id=filters['system_id'])
        
        return [{
            'id': access.id,
            'user': access.user.username,
            'system': access.system.name,
            'access_level': access.access_level,
        } for access in queryset]
    
    def grant_access(self, user_id, system_id, access_level, justification=None):
        """Grant access via MCP"""
        from access_management.models import AccessRecord
        from accounts.models import User
        from systems.models import System
        from django.utils import timezone
        
        try:
            user = User.objects.get(id=user_id)
            system = System.objects.get(id=system_id)
            
            access = AccessRecord.objects.create(
                user=user,
                system=system,
                access_level=access_level,
                granted_date=timezone.now(),
                justification=justification or 'Granted via MCP',
            )
            
            return {
                'id': access.id,
                'status': 'granted',
                'message': f'Access granted to {user.username} for {system.name}',
            }
        except Exception as e:
            return {'error': str(e)}
    
    def start(self):
        """Start MCP server"""
        if self.server:
            self.server.start()
```

### Management Command

```python
# management/commands/start_mcp_server.py
from django.core.management.base import BaseCommand
from mcp_server.server import UAMSMCPServer

class Command(BaseCommand):
    help = 'Start MCP server'

    def handle(self, *args, **options):
        server = UAMSMCPServer()
        if server.server:
            self.stdout.write(self.style.SUCCESS('Starting MCP server...'))
            server.start()
        else:
            self.stdout.write(self.style.WARNING('MCP server not enabled'))
```

## MCP Protocol Handlers

### User Operations

```python
# Get user
{
    "method": "get_user",
    "params": {"user_id": 1}
}

# List users
{
    "method": "list_users",
    "params": {"filters": {"department": "IT Department"}}
}

# Create user
{
    "method": "create_user",
    "params": {
        "username": "jdoe",
        "email": "jdoe@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

### Access Operations

```python
# Get access record
{
    "method": "get_access",
    "params": {"access_id": 1}
}

# List access records
{
    "method": "list_access",
    "params": {"filters": {"user_id": 1}}
}

# Grant access
{
    "method": "grant_access",
    "params": {
        "user_id": 1,
        "system_id": 1,
        "access_level": "Read",
        "justification": "Project work"
    }
}
```

## Use Cases

### AI Model Integration

Provide structured access to UAMS data for AI models:

```python
# AI model can query users
response = mcp_client.call('list_users', {'filters': {'role': 'employee'}})

# AI model can analyze access patterns
access_records = mcp_client.call('list_access', {'filters': {'user_id': 1}})
```

### Automation Workflows

Automate access management tasks:

```python
# Automated access grant
result = mcp_client.call('grant_access', {
    'user_id': user_id,
    'system_id': system_id,
    'access_level': 'Read',
    'justification': 'Automated grant based on role'
})
```

### Reporting and Analytics

Generate reports via MCP:

```python
# Get access statistics
users = mcp_client.call('list_users')
access_records = mcp_client.call('list_access')

# Analyze data
# ...
```

## Security Considerations

### Authentication

- Token-based authentication
- Secure token storage
- Token rotation

### Authorization

- Role-based access control
- Permission checks
- Audit logging

### Data Protection

- Encrypted communications
- Data validation
- Input sanitization

## Best Practices

1. **Authentication**: Use strong authentication tokens
2. **Validation**: Validate all inputs
3. **Error Handling**: Handle errors gracefully
4. **Logging**: Log all MCP operations
5. **Rate Limiting**: Implement rate limiting
6. **Documentation**: Document all MCP endpoints
7. **Testing**: Test MCP handlers thoroughly

## Troubleshooting

### Server Connection

```python
# Test MCP server connection
from mcp_server.server import UAMSMCPServer

server = UAMSMCPServer()
if server.server:
    try:
        server.server.health_check()
        print("MCP server is running")
    except Exception as e:
        print(f"MCP server error: {e}")
```

### Handler Errors

Monitor handler execution and log errors for debugging.

## Next Steps

- [Integrations](integrations.md) - General integration guide
- [Configuration](../configuration.md) - System configuration
- [Development](../development.md) - Development guidelines

---

For additional protocol integrations, see [Integrations Overview](integrations.md).


#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a test client with a valid host
client = Client(HTTP_HOST='127.0.0.1:8000')

# Try to request the page
try:
    response = client.get('/service-accounts/1/password-history/add/', HTTP_HOST='127.0.0.1')
    
    if response.status_code == 200:
        print('✓ Page returns HTTP 200 (OK)')
        if 'TemplateSyntaxError' not in response.content.decode('utf-8', errors='ignore'):
            print('✓ No TemplateSyntaxError in response')
        else:
            print('✗ TemplateSyntaxError still present')
    elif response.status_code == 302:
        print('✓ Page redirects (likely login required)')
        print(f'  → Redirect URL: {response.url}')
    else:
        print(f'? Page returns HTTP {response.status_code}')
        
except Exception as e:
    print(f'✗ Error: {type(e).__name__}: {e}')

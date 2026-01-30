import os
import sys
import django
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_access_management.settings')
django.setup()
from access_management.models import UserSystemAccess
print('total:', UserSystemAccess.objects.count())
print("active (Active or Approved):", UserSystemAccess.objects.filter(status__in=['Active','Approved']).count())
for row in UserSystemAccess.objects.values('id','status')[:20]:
    print(row)

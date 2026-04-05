import os
import django
import traceback
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rm_system.settings')
django.setup()

from django.test import Client
from accounts.models import User
import sys

teacher = User.objects.filter(role='teacher').first()
if not teacher:
    teacher = User.objects.first()

if not teacher:
    print("No users found.")
    sys.exit()

print(f"Logging in as {teacher.username} ({teacher.role})")
c = Client()
c.force_login(teacher)

try:
    response = c.get('/dashboard/teacher/report/', SERVER_NAME='127.0.0.1')
    if response.status_code == 500:
        html = response.content.decode('utf-8', errors='replace')
        # Try to find Exception text
        if "Exception Value:" in html:
            start = html.find("Exception Value:")
            print("\n" + "="*50)
            print(html[start:start+1000])
        else:
            print("500 ERROR BUT NO TRACEBACK FOUND. HTML snippet:")
            print(html[:2000])
    else:
        print(f"SUCCESS: {response.status_code}")
except Exception as e:
    print("FATAL EXCEPTION:")
    traceback.print_exc()

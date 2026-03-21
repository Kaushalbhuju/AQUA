"""
Script to create a teacher user for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rm_system.settings')
django.setup()

from accounts.models import User

# Check if teacher role exists
print("Available roles:", User.ROLE_CHOICES)

# Create a teacher user
username = input("Enter username for teacher account (or press Enter to skip): ").strip()

if username:
    try:
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            print(f"User '{username}' already exists. Updating role to teacher...")
            user = User.objects.get(username=username)
            user.role = 'teacher'
            user.save()
            print(f"✓ Successfully updated {username} to teacher role")
        else:
            # Create new teacher user
            email = input(f"Enter email for {username}: ").strip() or f"{username}@example.com"
            password = input(f"Enter password for {username} (default: teacher123): ").strip() or "teacher123"
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='teacher',
                first_name='Teacher',
                last_name='User'
            )
            print(f"✓ Successfully created teacher user: {username}")
            print(f"  Email: {email}")
            print(f"  Password: {password}")
        
        print("\nYou can now login with this account!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
else:
    print("No user created. To manually create a teacher user:")
    print("  python manage.py createsuperuser")
    print("Then update the user's role to 'teacher' in the admin panel")

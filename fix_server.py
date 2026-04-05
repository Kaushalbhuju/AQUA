import os
import shutil

# Fix urls.py by replacing with fixed content
with open('dashboard/urls_fixed.py', 'r') as f:
    fixed_content = f.read()

with open('dashboard/urls.py', 'w') as f:
    f.write(fixed_content)

print("Fixed dashboard/urls.py")

# Backup old
shutil.move('dashboard/urls.py', 'dashboard/urls_fixed.py')
shutil.move('dashboard/urls_old.py', 'dashboard/urls.py') if os.path.exists('dashboard/urls_old.py') else None

print("Server files fixed. Run 'python manage.py runserver'")


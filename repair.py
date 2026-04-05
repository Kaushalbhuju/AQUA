import re
import os

files = [
    'templates/dashboards/class_list.html',
    'templates/dashboards/student_records.html',
    'templates/dashboards/student_attendance.html',
    'templates/dashboards/teacher_report.html',
    'templates/dashboards/teacher_dashboard.html',
]

for file in files:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix: {% \n any_tag -> {% any_tag
        content = re.sub(r'\{%\s*\n\s*', '{% ', content)
        
        # Fix: {% selected \n endif %} -> selected{% endif %}
        content = re.sub(r'selected\{%\s*\n\s*endif\s*%\}', 'selected{% endif %}', content)
        
        # Fix: {% if language.code == LANGUAGE_CODE %}selected{% \n endif %}
        # The first regex should handle the {% \n
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)

print("Repair completed.")

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rm_system.settings')
django.setup()

from django.template.loader import render_to_string
from django.test import RequestFactory
import traceback

templates_to_test = [
    'dashboards/class_list.html',
    'dashboards/student_records.html',
    'dashboards/student_attendance.html',
    'dashboards/teacher_report.html',
]

request = RequestFactory().get('/')

with open('render_test_output.txt', 'w', encoding='utf-8') as f:
    for tmpl in templates_to_test:
        f.write(f"--- Rendering {tmpl} ---\n")
        try:
            render_to_string(tmpl, request=request)
            f.write(f"SUCCESS: {tmpl}\n")
        except Exception as e:
            f.write(f"ERROR in {tmpl}: {str(e)}\n")
            f.write(traceback.format_exc())

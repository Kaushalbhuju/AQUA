# dashboard/migrations/0002_fix_student_stages.py
from django.db import migrations

def fix_student_stages(apps, schema_editor):
    Student = apps.get_model('dashboard', 'Student')
    
    # Valid stage choices
    valid_stages = [
        'candidate_info',
        'select_candidate', 
        'interview_pattern',
        'pass_interview',
        'ceo_approval',
        'visa_arrival',
        'completed'
    ]
    
    # Fix any students with invalid stages
    for student in Student.objects.all():
        if student.stage not in valid_stages:
            print(f"Fixing stage for student {student.id}: {student.stage} -> candidate_info")
            student.stage = 'candidate_info'
            student.save()

class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(fix_student_stages),
    ]
import os

files_to_fix = [
    'templates/dashboards/student_attendance.html',
    'templates/dashboards/teacher_report.html',
    'templates/dashboards/student_records.html',
    'templates/dashboards/class_list.html'
]

for file in files_to_fix:
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Make sure no spaces around == are fixed
        content = content.replace('language.code==LANGUAGE_CODE', 'language.code == LANGUAGE_CODE')
        content = content.replace('selected_classroom.id==c.id', 'selected_classroom.id == c.id')
        
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)

print('Syntax fixed.')

import re

file = 'templates/dashboards/teacher_report.html'
with open(file, 'r', encoding='utf-8') as f:
    text = f.read()

# Fix month==1, month==2, etc
text = re.sub(r'\{%\s*if\s+(month)==(\d+)\s*%\}', r'{% if \1 == \2 %}', text)

with open(file, 'w', encoding='utf-8') as f:
    f.write(text)

print("Repaired teacher_report.html syntax")

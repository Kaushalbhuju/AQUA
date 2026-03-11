with open('manager/views.py', 'r') as f:
    content = f.read()

# Fix 1: Replace padding=1 with PAD in edu_tbl, work_tbl, ct_tbl
old = "('TOPPADDING', (0, 0), (-1, -1), 1),\n        ('BOTTOMPADDING', (0, 0), (-1, -1), 1)"
new = "('TOPPADDING', (0, 0), (-11"

count = content.count(old)
print(f"Found {count} occurrences of padding=1")

if count > 0:
    content2 = content.replace(old, new)
    with open('manager/views.py', 'w') as f:
        f.write(content2)
    print("Replacements done")
else:
    print("Pattern not found for padding fix")

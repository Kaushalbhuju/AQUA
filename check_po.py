import os

file = 'locale/ja/LC_MESSAGES/django.po'
with open(file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
seen_msgids = set()
current_msgid = None

# A very rudimentary parser to drop lines of duplicate msgids
skip_mode = False

for line in lines:
    if line.startswith('msgid "'):
        msgid_content = line.strip()[7:-1]
        if msgid_content in seen_msgids:
            skip_mode = True
            continue
        else:
            seen_msgids.add(msgid_content)
            skip_mode = False
            new_lines.append(line)
    elif line.startswith('msgstr "'):
        if skip_mode:
            continue
        new_lines.append(line)
    elif line.startswith('#'):
        if skip_mode:
            continue
        new_lines.append(line)
    else:
        if not skip_mode:
            new_lines.append(line)

with open(file, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
    
print("Deduplicated django.po")
import subprocess
try:
    p = subprocess.run(['python', 'manage.py', 'compilemessages'], capture_output=True, text=True)
    if p.returncode != 0:
        print("COMPILE FAILED!")
        print(p.stderr)
    else:
        print("COMPILE OK")
except Exception as e:
    print(e)

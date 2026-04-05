file = 'locale/ja/LC_MESSAGES/django.po'
with open(file, 'r', encoding='utf-8') as f:
    data = f.read()

data = data.replace('\\nmsgid', '\nmsgid')
data = data.replace('"\n\\n', '"\n\n')
data = data.replace('\\nmsgstr', '\nmsgstr')
data = data.replace('"\n\n\n', '"\n\n')

# Actually, if I wrote \n literally as text:
data = data.replace('\\n', '\n')

with open(file, 'w', encoding='utf-8') as f:
    f.write(data)

# Check and fix padding + add bank info

with open('manager/views.py', 'r') as f:
    content = f.read()

# Check if padding was fixed
if "'TOPPADDING', (0, 0), (-1, -1), PAD)" in content:
    print('Padding fix applied')
else:
    print('Padding NOT fixed')

# Check for bank info section
if 'BANK INFORMATION' in content:
    print('Bank Info section exists')
else:
    print('Bank Info NOT added yet')

print("Done checking")

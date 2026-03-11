# Script to fix padding and add Bank Information section

with open('manager/views.py', 'r') as f:
    content = f.read()

# Fix padding from 1 to PAD in edu_tbl and work_tbl setStyle calls
old_padding = "'TOPPADDING', (0, 0), (-1, -1), 1),\n        ('BOTTOMPADDING', (0, 0), (-1, -1), 1)"
new_padding = "'TOPPADDING', (0, 0), (-1, -1), PAD),\n        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD)"

content = content.replace(old_padding, new_padding)

# Add Bank Information section after Driving License
bank_section = '''
    # ── BANK INFORMATION ──
    bank_qs = list(staff.bank_info.all())
    
    if bank_qs:
        elements.append(_grid(
            [[_p('BANK INFORMATION', 8, True)]],
            [W], [('BACKGROUND', (0, 0), (-1,-true)), true))]
        ))
        
        for bank in bank_qs:
            bdata = [[
                _p('Bank Name:', True),
                _p(_val(bank.bank_name)),
                _p('Branch:', True),
                _p(_val(bank.branch_name)),
                _p('Account No:', True),
                _p(_val(bank.account_no)),
            ],
            [
                _p('Holder Name:', True),
                _p(_val(bank.account_holder_name)),
                '', '', '', ''
            ]
            
            
            
            
            
            
                
                
                
                
                
                

'''

search_pattern = "elements.append(Spacer(1, 4))\n\n    # ── HOBBIES"
if search_pattern in content:
    print("Found location for Bank Info")
else:
    print("Location not found")

with open('manager/views.py', 'w') as f:
    f.write(content)
print("Done")

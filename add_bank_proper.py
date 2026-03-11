# Script to add Bank Information section after Driving License

with open('manager/views.py', 'r') as f:
    content = f.read()

# Find location - after driving license, before hobbies
search_str = "    elements.append(Spacer(1, 4))\n\n    # ── HOBBIES + MOTIVATION ──"

if search_str in content:
    print("Found location for Bank Info")
    
    # Proper bank information section
    bank_section = """
    # ── BANK INFORMATION ──
    bank_qs = list(staff.bank_info.all())
    
    if bank_qs:
        elements.append(_grid(
            [[_p('BANK INFORMATION', 8, True)]],
            [W], [('BACKGROUND', (0, 0), (-1, -1), GREY_BG)]
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
            ]]
            
            
            
            
            
                
                
                
                
                
                
    
"""
    
else:
    print("Location not found")

with open('manager/views.py', 'w') as f:
    f.write(content)
print("Done")

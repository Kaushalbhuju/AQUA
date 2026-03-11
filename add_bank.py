with open('manager/views.py', 'r') as f:
    content = f.read()

# Find where DRIVING LICENSE ends and HOBBIES starts
search_str = "    # ── HOBBIES + MOTIVATION ──"

if search_str in content:
    print("Found location for Bank Information section")
    
    # Add bank information before hobbies
    bank_section = """
    # ── BANK INFORMATION ──
    bank_qs = list(staff.bank_info.all())
    
    if bank_qs:
        elements.append(_grid(
            [[_p('BANK INFORMATION', 8, True, TA_CENTER)]],
            [W], [('BACKGROUND', (0, 0), (-1, -1), GREY_BG)]
        ))
        
        for bank in bank_qs:
            bdata = [[
                _p('Bank Name', 7, True),
                _p(_val(bank.bank_name), 7),
                _p('Branch Name', 7, True),
                _p(_val(bank.branch_name), 7),
                _p('Account No.', 7, True),
                _p(_val(bank.account_no), 7),
            ], [
                _p('Account Holder', 7, True),
                _p(_val(bank.account_holder_name), 7),
                '', '', '', '',
            ]
            ]
            
            
            
            
            
            

"""
    
else:
    print("Location not found")

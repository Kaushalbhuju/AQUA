# Script to properly add Bank Information section after Driving License

with open('manager/views.py', 'r') as f:
    content = f.read()

# Find location - use simpler search
search_str = "elements.append(Spacer(1, 4))\n\n    # ── HOBBIES"

if search_str in content:
    print("Found location for Bank Info")
    
    # Proper bank information section  
    bank_section = """elements.append(Spacer(1, 4))

    # ── BANK INFORMATION ──
    if staff.bank_info.exists():
        elements.append(_grid(
            [[_p('BANK INFORMATION', 8, True)]],
            [W], [('BACKGROUND', (0, 0), (-1, -1), GREY_BG)]
        ))
        
        b_headers = [_p('Bank Name', 7, True), _p('Branch', 7, True), _p('A/C No.', 7, True), _p('Holder Name', 7, True)]
        b_data = [b_headers]
        
        for bank in staff.bank_info.all():
            b_data.append([
                _p(str(bank.bank_name) if bank.bank_name else '', 6),
                _p(str(bank.branch_name) if bank.branch_name else '', 6),
                _p(str(bank.account_number) if bank.account_number else '', 6),
                _p(str(bank.account_holder_name) if bank.account_holder_name else '', 6)
            ])
        
        bc = [2 * inch, 2 * inch, 2 * inch]
        elements.append(_grid(b_data[0:4], bc))
    
"""
    
else:
    print("Location not found")

print("Done")

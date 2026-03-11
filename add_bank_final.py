# Script to add Bank Information section after Driving License

with open('manager/views.py', 'r') as f:
    content = f.read()

# Find location - use simpler search
search_str = "elements.append(Spacer(1, 4))\n\n    # ── HOBBIES"

if search_str in content:
    print("Found location for Bank Info")
    
    # Proper bank information section  
    bank_section = """
    # ── BANK INFORMATION ──
    bank_qs = list(staff.bank_info.all())
    
"""
    
else:
    print("Location not found")

with open('manager/views.py', 'w') as f:
    f.write(content)
print("Done")

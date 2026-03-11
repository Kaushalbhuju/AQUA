import re

with open('e:/down/AQUA/manager/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "    # ── BIG TABLE (Row 0 to 9) ──"
end_marker = "    # Build\n    doc.build(elements)"

new_block = """    # ── BIG TABLE (Row 0 to 9) ──
    photo_content = _p('CANDIDATE\\nPHOTO', 7, True, TA_CENTER)
    if staff.candidate_photo:
        try:
            photo_content = Image(staff.candidate_photo.path, width=1.1 * inch, height=1.3 * inch)
        except Exception:
            pass

    gender_display = staff.get_gender_display() if staff.gender else ''
    dob = str(staff.date_of_birth) if staff.date_of_birth else ''
    
    # Proportional column widths matching exactly W to prevent horizontal overflow and wrapping congestion
    big_c = [W * 0.09, W * 0.05, W * 0.26, W * 0.12, W * 0.13, W * 0.10, W * 0.13, W * 0.12]
    
    big_data = [
        # 0
        [_p('STAFF ID', 7, True), '', _p(_val(staff.staff_id), 7), _p('Gender', 7, True), _p(gender_display, 7), photo_content, '', ''],
        # 1
        [_p('Full Name', 7, True), '', _p(_val(staff.full_name), 7), _p('Marital Status', 7, True), _p(_val(staff.marital_status), 7), '', '', ''],
        # 2
        [_p('Address', 7, True), _p('Permanent', 6, True), _p(_val(staff.permanent_address), 7), '', '', '', '', ''],
        # 3
        ['', _p('Present', 6, True), _p(_val(staff.present_address), 7), '', '', '', '', ''],
        # 4
        [_p('ID / Passport No.', 7, True), '', _p(_val(staff.id_passport_no), 7), _p('Date of Issue', 7, True), _p(str(staff.date_of_issue) if staff.date_of_issue else '', 7), _p('Issue From', 7, True), _p(_val(staff.issue_from), 7), ''],
        # 5
        [_p('Personal\\nInformation', 7, True, TA_CENTER), '', _p('Date of Birth', 6, True, TA_CENTER), _p('Eye Lense', 6, True, TA_CENTER), '', _p('Blood Group', 6, True, TA_CENTER), _p('Phone No.', 6, True, TA_CENTER), _p('Email ID', 6, True, TA_CENTER)],
        # 6
        ['', '', _p(dob, 7, align=TA_CENTER), _p('Right', 6, True, TA_CENTER), _p(_val(staff.eye_lense_right), 6, align=TA_CENTER), _p(_val(staff.blood_group), 7, align=TA_CENTER), _p(_val(staff.phone_no), 7, align=TA_CENTER), _p(_val(staff.email_id), 6, align=TA_CENTER)],
        # 7
        ['', '', '', _p('Left', 6, True, TA_CENTER), _p(_val(staff.eye_lense_left), 6, align=TA_CENTER), '', '', ''],
        # 8
        [_p('Family Records', 7, True), '', '', '', '', _p('CONTACT NO', 7, True, TA_CENTER), '', ''],
        # 9
        [_p('Spouse Name', 7, True), '', _p(_val(staff.spouse_name), 7), '', '', _p(_val(staff.contact_no), 7), '', ''],
    ]

    PAD_MIN = 3
    PAD_V = 1

    big_tbl = Table(big_data, colWidths=big_c)
    big_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD_MIN),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD_MIN),
        ('TOPPADDING', (0, 0), (-1, -1), PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V),

        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (5, 0), (7, 3)),
        ('SPAN', (0, 1), (1, 1)),
        ('SPAN', (2, 2), (4, 2)),
        ('SPAN', (0, 2), (0, 3)),
        ('SPAN', (2, 3), (4, 3)),
        ('SPAN', (0, 4), (1, 4)),
        ('SPAN', (6, 4), (7, 4)),
        ('SPAN', (0, 5), (1, 7)),
        ('SPAN', (3, 5), (4, 5)),
        ('SPAN', (2, 6), (2, 7)),
        ('SPAN', (5, 6), (5, 7)),
        ('SPAN', (6, 6), (6, 7)),
        ('SPAN', (7, 6), (7, 7)),
        ('SPAN', (0, 8), (1, 8)),
        ('SPAN', (2, 8), (4, 8)),
        ('SPAN', (5, 8), (7, 8)),
        ('SPAN', (0, 9), (1, 9)),
        ('SPAN', (2, 9), (4, 9)),
        ('SPAN', (5, 9), (7, 9)),
        
        ('BACKGROUND', (0, 0), (1, 0), GREY_BG),
        ('BACKGROUND', (3, 0), (3, 0), GREY_BG),
        ('BACKGROUND', (0, 1), (1, 1), GREY_BG),
        ('BACKGROUND', (3, 1), (3, 1), GREY_BG),
        ('BACKGROUND', (0, 2), (1, 3), GREY_BG),
        ('BACKGROUND', (0, 4), (1, 4), GREY_BG),
        ('BACKGROUND', (3, 4), (3, 4), GREY_BG),
        ('BACKGROUND', (5, 4), (5, 4), GREY_BG),
        ('BACKGROUND', (0, 5), (7, 5), GREY_BG),
        ('BACKGROUND', (0, 5), (1, 7), GREY_BG),
        ('BACKGROUND', (0, 8), (1, 8), GREY_BG),
        ('BACKGROUND', (5, 8), (7, 8), GREY_BG),
        ('BACKGROUND', (0, 9), (1, 9), GREY_BG),
        
        ('ALIGN', (5, 0), (7, 3), 'CENTER'),
        ('VALIGN', (0, 5), (1, 7), 'MIDDLE'),
        ('ALIGN', (0, 5), (7, 5), 'CENTER'),
    ]))
    elements.append(big_tbl)
    elements.append(Spacer(1, 3))

    # ── BANK INFORMATION ──
    bank_header = [[_p('BANK INFORMATION', 8, True, TA_CENTER)]]
    elements.append(_grid(bank_header, [W], [('BACKGROUND', (0, 0), (-1, -1), GREY_BG)]))
    
    bank_qs = list(staff.bank_info.all())
    bank_data = [[_p('Bank Name', 7, True, TA_CENTER), _p('Branch', 7, True, TA_CENTER), _p('Account No.', 7, True, TA_CENTER), _p('Account Holder', 7, True, TA_CENTER)]]
    for _ in range(max(1 - len(bank_qs), 0)):
        bank_qs.append(None)
    for b in bank_qs:
        if b:
            bank_data.append([_p(_val(b.bank_name), 7), _p(_val(b.branch_name), 7), _p(_val(b.account_no), 7, align=TA_CENTER), _p(_val(b.account_holder_name), 7)])
        else:
            bank_data.append(['', '', '', ''])
    
    bank_c = [W*0.25, W*0.25, W*0.25, W*0.25]
    elements.append(_grid(bank_data, bank_c, [
        ('BACKGROUND', (0, 0), (-1, 0), GREY_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD_MIN),
        ('TOPPADDING', (0, 0), (-1, -1), PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V),
    ]))
    elements.append(Spacer(1, 3))

    # ── EDUCATIONAL HISTORY ──
    elements.append(_grid([[_p('EDUCATIONAL HISTORY', 8, True, TA_CENTER)]], [W], [('BACKGROUND', (0, 0), (-1, -1), GREY_BG)]))
    
    edu_c = [W * 0.16, W * 0.35, W * 0.09, W * 0.09, W * 0.09, W * 0.09, W * 0.13]
    edu_all = [
        [_p('Pass Level', 7, True, TA_CENTER), _p('Name of School', 7, True, TA_CENTER), _p('Admission & Graduation', 7, True, TA_CENTER), '', '', '', _p('Enrolled Years', 7, True, TA_CENTER)],
        ['', '', _p('Year', 6, True, TA_CENTER), _p('Month', 6, True, TA_CENTER), _p('Year', 6, True, TA_CENTER), _p('Month', 6, True, TA_CENTER), '']
    ]

    edu_levels = ['Primary School', 'Junior H. School', 'Higher S. School', 'College / University', 'Graduate University', 'Graduate University', 'Other School']
    edu_map = {edu.pass_level: edu for edu in staff.education_history.all()}
    level_keys = ['Primary', 'Junior', 'Higher', 'College', 'Graduate', 'PostGraduate', 'Other']
    
    for i, key in enumerate(level_keys):
        edu_obj = edu_map.get(key)
        if edu_obj:
            edu_all.append([
                _p(edu_levels[i], 7, align=TA_CENTER), _p(_val(edu_obj.name_of_school), 7),
                _p(_val(edu_obj.admission_year), 7, align=TA_CENTER),
                _p(_val(edu_obj.admission_month), 7, align=TA_CENTER),
                _p(_val(edu_obj.graduation_year), 7, align=TA_CENTER),
                _p(_val(edu_obj.graduation_month), 7, align=TA_CENTER),
                _p(f'{_val(edu_obj.enrolled_years)} Years' if edu_obj.enrolled_years else 'Years', 7, align=TA_CENTER),
            ])
        else:
            edu_all.append([_p(edu_levels[i], 7, align=TA_CENTER), '', '', '', '', '', _p('Years', 7, align=TA_CENTER)])

    edu_tbl = Table(edu_all, colWidths=edu_c)
    edu_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD_MIN),
        ('TOPPADDING', (0, 0), (-1, -1), PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V),
        ('BACKGROUND', (0, 0), (-1, 1), GREY_BG),
        ('SPAN', (2, 0), (5, 0)),
        ('SPAN', (6, 0), (6, 1)),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(edu_tbl)
    elements.append(Spacer(1, 3))

    # ── WORKING EXPERIENCE ──
    elements.append(_grid([[_p('WORKING EXPERIENCE', 8, True, TA_CENTER)]], [W], [('BACKGROUND', (0, 0), (-1, -1), GREY_BG)]))

    work_all = [
        [_p('Type of Work', 7, True, TA_CENTER), _p('Name of Working Company', 7, True, TA_CENTER), _p('Date of Join & Resign', 7, True, TA_CENTER), '', '', '', _p('Working Years', 7, True, TA_CENTER)],
        ['', '', _p('Year', 6, True, TA_CENTER), _p('Month', 6, True, TA_CENTER), _p('Year', 6, True, TA_CENTER), _p('Month', 6, True, TA_CENTER), '']
    ]

    work_qs = list(staff.work_experience.all())
    for _ in range(max(3 - len(work_qs), 0)):
        work_qs.append(None)
    for w in work_qs:
        if w:
            work_all.append([
                _p(_val(w.type_of_work), 7, align=TA_CENTER), _p(_val(w.name_of_company), 7),
                _p(_val(w.join_year), 7, align=TA_CENTER), _p(_val(w.join_month), 7, align=TA_CENTER),
                _p(_val(w.resign_year), 7, align=TA_CENTER), _p(_val(w.resign_month), 7, align=TA_CENTER),
                _p(f'{_val(w.working_years)} Years' if w.working_years else 'Years', 7, align=TA_CENTER),
            ])
        else:
            work_all.append(['', '', '', '', '', '', _p('Years', 7, align=TA_CENTER)])

    work_tbl = Table(work_all, colWidths=edu_c)
    work_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD_MIN),
        ('TOPPADDING', (0, 0), (-1, -1), PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V),
        ('BACKGROUND', (0, 0), (-1, 1), GREY_BG),
        ('SPAN', (2, 0), (5, 0)),
        ('SPAN', (6, 0), (6, 1)),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(work_tbl)
    elements.append(Spacer(1, 3))

    # ── CERTIFICATE OF SKILLS + SKILLS TRAINING STATUS ──
    ct_data = [
        [_p('CERTIFICATE OF SKILLS', 8, True, TA_CENTER), '', _p('SKILLS TRAINING STATUS', 8, True, TA_CENTER), ''],
        [_p('Pass Year & Month', 6, True, TA_CENTER), _p('Name of Certificate', 6, True, TA_CENTER), _p('Join Year and Month', 6, True, TA_CENTER), _p('Organization', 6, True, TA_CENTER)]
    ]
    
    cert_qs = list(staff.certificates.all())
    train_qs = list(staff.training_status.all())
    max_rows = max(len(cert_qs), len(train_qs), 3)
    for _ in range(max_rows - len(cert_qs)): cert_qs.append(None)
    for _ in range(max_rows - len(train_qs)): train_qs.append(None)

    for i in range(max_rows):
        c = cert_qs[i]
        t = train_qs[i]
        ct_data.append([
            _p(f'{_val(c.pass_year)}/{_val(c.pass_month)}' if c and (c.pass_year or c.pass_month) else '', 6, align=TA_CENTER),
            _p(_val(c.name_of_certificate) if c else '', 6),
            _p(f'{_val(t.join_year)}/{_val(t.join_month)}' if t and (t.join_year or t.join_month) else '', 6, align=TA_CENTER),
            _p(_val(t.organization) if t else '', 6),
        ])
    
    ct_c = [W * 0.15, W * 0.35, W * 0.15, W * 0.35]
    ct_tbl = Table(ct_data, colWidths=ct_c)
    ct_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('BACKGROUND', (0, 0), (-1, 1), GREY_BG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD_MIN),
        ('TOPPADDING', (0, 0), (-1, -1), PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V),
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (2, 0), (3, 0)),
    ]))
    elements.append(ct_tbl)
    elements.append(Spacer(1, 3))

    # ── DRIVING LICENSE ──
    license = None
    try: license = staff.driving_license
    except DrivingLicense.DoesNotExist: pass

    dl_data = [
        [_p('DRIVING LICENSE', 7, True, TA_CENTER), _p('Pass Year & Month', 6, True, TA_CENTER), _p('Discretion of License', 6, True, TA_CENTER)],
        ['', _p(f'{_val(license.pass_year)} / {_val(license.pass_month)}' if license else '', 7, align=TA_CENTER), _p(_val(license.discretion_of_license) if license else '', 7)]
    ]
    dl_c = [W * 0.3, W * 0.2, W * 0.5]
    dl_tbl = Table(dl_data, colWidths=dl_c)
    dl_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (0, -1), GREY_BG),
        ('BACKGROUND', (1, 0), (2, 0), GREY_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD_MIN),
        ('TOPPADDING', (0, 0), (-1, -1), PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V),
        ('SPAN', (0, 0), (0, 1)),
    ]))
    elements.append(dl_tbl)
    elements.append(Spacer(1, 3))

    # ── HOBBIES + MOTIVATION ──
    hm_data = [
        [_p('Hobbies, Special skills, etc.', 7, True), _p('Motivation, Self-promotion', 7, True)],
        [_p(_val(staff.hobbies), 7), _p(_val(staff.motivation), 7)],
    ]
    hm_tbl = Table(hm_data, colWidths=[W / 2, W / 2], rowHeights=[None, 0.5 * inch])
    hm_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, 0), GREY_BG),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD_MIN),
        ('TOPPADDING', (0, 0), (-1, -1), PAD_V),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD_V),
    ]))
    elements.append(hm_tbl)
"""

if start_marker in content and end_marker in content:
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    new_content = content[:start_idx] + new_block + "\n" + content[end_idx:]
    with open('e:/down/AQUA/manager/views.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully replaced formatting sizes with decongested proportional widths.")
else:
    print("Could not find markers.")

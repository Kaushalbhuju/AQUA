# ============================================
# views.py - FIXED VERSION
# ============================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from .models import StaffRegistration, DrivingLicense
from .forms import (
    StaffRegistrationForm, EducationalHistoryFormSet, WorkingExperienceFormSet,
    CertificateFormSet, TrainingFormSet, DrivingLicenseForm, BankFormSet

)
from .models import (
    StaffRegistration, EducationalHistory, WorkingExperience,
    CertificateOfSkills, SkillsTrainingStatus, DrivingLicense, BankInformation
)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime


def staff_registration_create(request):
    form_valid = education_valid = work_valid = certificate_valid = training_valid = license_valid = bank_valid = True
    if request.method == 'POST':
        print("POST Data:", request.POST)  # Debug
        print("FILES Data:", request.FILES)  # Debug
        
        form = StaffRegistrationForm(request.POST, request.FILES)
        education_formset = EducationalHistoryFormSet(request.POST, prefix='education')
        work_formset = WorkingExperienceFormSet(request.POST, prefix='work')
        certificate_formset = CertificateFormSet(request.POST, prefix='certificate')
        training_formset = TrainingFormSet(request.POST, prefix='training')
        license_form = DrivingLicenseForm(request.POST, prefix='license')
        bank_formset = BankFormSet(request.POST, prefix='bank')
        
        # Check all forms validity
        form_valid = form.is_valid()
        education_valid = education_formset.is_valid()
        work_valid = work_formset.is_valid()
        certificate_valid = certificate_formset.is_valid()
        training_valid = training_formset.is_valid()
        license_valid = license_form.is_valid()
        bank_valid = bank_formset.is_valid()


        print("Bank Valid:", bank_valid)                          # ✅ NEW
        if not bank_valid:
            print("Bank Errors:", bank_formset.errors)            # ✅ NEW
        print("Form Valid:", form_valid)
        print("Education Valid:", education_valid)
        print("Work Valid:", work_valid)
        print("Certificate Valid:", certificate_valid)
        print("Training Valid:", training_valid)
        print("License Valid:", license_valid)

        
        if not form_valid:
            print("Form Errors:", form.errors)
        if not education_valid:
            print("Education Errors:", education_formset.errors)
        if not work_valid:
            print("Work Errors:", work_formset.errors)
        if not certificate_valid:
            print("Certificate Errors:", certificate_formset.errors)
        if not training_valid:
            print("Training Errors:", training_formset.errors)
        if not license_valid:
            print("License Errors:", license_form.errors)
        
        if form_valid and education_valid and work_valid and certificate_valid and training_valid and license_valid and bank_valid:
            try:
                with transaction.atomic():
                    # Save main staff form
                    staff = form.save()
                    
                    # Save education formset
                    education_instances = education_formset.save(commit=False)
                    for edu in education_instances:
                        edu.staff = staff
                        edu.save()
                    
                    # Save work formset
                    work_instances = work_formset.save(commit=False)
                    for work in work_instances:
                        work.staff = staff
                        work.save()
                    
                    # Save certificate formset
                    certificate_instances = certificate_formset.save(commit=False)
                    for cert in certificate_instances:
                        cert.staff = staff
                        cert.save()
                    
                    # Save training formset
                    training_instances = training_formset.save(commit=False)
                    for train in training_instances:
                        train.staff = staff
                        train.save()
                    
                    # Save license
                    if license_form.cleaned_data.get('pass_year') or license_form.cleaned_data.get('pass_month') or license_form.cleaned_data.get('discretion_of_license'):
                        license = license_form.save(commit=False)
                        license.staff = staff
                        license.save()
                        #Bank Information 
                    bank_instances = bank_formset.save(commit=False)
                    if not bank_instances:
                        raise ValueError("At least one bank information record is required.")
                    for bank in bank_instances:
                        bank.staff = staff
                        bank.save()

                    
                messages.success(request, 'Staff registration completed successfully!')
                return redirect('staff_detail', pk=staff.pk)
            except Exception as e:
                messages.error(request, f'Error saving data: {str(e)}')
                print("Exception:", str(e))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffRegistrationForm()
        education_formset = EducationalHistoryFormSet(prefix='education', queryset=EducationalHistory.objects.none())
        work_formset = WorkingExperienceFormSet(prefix='work', queryset=WorkingExperience.objects.none())
        certificate_formset = CertificateFormSet(prefix='certificate', queryset=CertificateOfSkills.objects.none())
        training_formset = TrainingFormSet(prefix='training', queryset=SkillsTrainingStatus.objects.none())
        license_form = DrivingLicenseForm(prefix='license')
        bank_formset = BankFormSet(instance=None, prefix='bank', queryset=BankInformation.objects.none())  # ✅ NEW

    
    context = {
        'form': form,
        'education_formset': education_formset,
        'work_formset': work_formset,
        'certificate_formset': certificate_formset,
        'training_formset': training_formset,
        'license_form': license_form,
        'bank_formset': bank_formset, 
        'has_errors': (not form_valid or not education_valid or not work_valid or 
                        not certificate_valid or not training_valid or not license_valid or not bank_valid),
    }
    
    return render(request, 'dashboards/staff_registration.html', context)


def staff_registration_update(request, pk):
    form_valid = education_valid = work_valid = certificate_valid = training_valid = license_valid = bank_valid = True
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    if request.method == 'POST':
        form = StaffRegistrationForm(request.POST, request.FILES, instance=staff)
        education_formset = EducationalHistoryFormSet(request.POST, instance=staff, prefix='education')
        work_formset = WorkingExperienceFormSet(request.POST, instance=staff, prefix='work')
        certificate_formset = CertificateFormSet(request.POST, instance=staff, prefix='certificate')
        training_formset = TrainingFormSet(request.POST, instance=staff, prefix='training')
        bank_formset = BankFormSet(request.POST,instance=staff, prefix='bank')

        
        try:
            license = staff.driving_license
            license_form = DrivingLicenseForm(request.POST, instance=license, prefix='license')
        except DrivingLicense.DoesNotExist:
            license_form = DrivingLicenseForm(request.POST, prefix='license')
        
        # Check validity
        form_valid = form.is_valid()
        education_valid = education_formset.is_valid()
        work_valid = work_formset.is_valid()
        certificate_valid = certificate_formset.is_valid()
        training_valid = training_formset.is_valid()
        license_valid = license_form.is_valid()
        bank_valid = bank_formset.is_valid()

        if form_valid and education_valid and work_valid and certificate_valid and training_valid and license_valid and bank_valid:
            try:
                with transaction.atomic():
                    staff = form.save()
                    
                    # Save formsets
                    education_formset.instance = staff
                    education_formset.save()
                    
                    work_formset.instance = staff
                    work_formset.save()
                    
                    certificate_formset.instance = staff
                    certificate_formset.save()
                    
                    training_formset.instance = staff
                    training_formset.save()
                    
                    # Save license
                    if license_form.cleaned_data.get('pass_year') or license_form.cleaned_data.get('pass_month') or license_form.cleaned_data.get('discretion_of_license'):
                        license = license_form.save(commit=False)
                        license.staff = staff
                        license.save()
                     # ✅ NEW — Save bank formset
                    bank_formset.save()

                    
                messages.success(request, 'Staff registration updated successfully!')
                return redirect('staff_detail', pk=staff.pk)
            except Exception as e:
                messages.error(request, f'Error updating data: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffRegistrationForm(instance=staff)
        education_formset = EducationalHistoryFormSet(instance=staff, prefix='education')
        work_formset = WorkingExperienceFormSet(instance=staff, prefix='work')
        certificate_formset = CertificateFormSet(instance=staff, prefix='certificate')
        training_formset = TrainingFormSet(instance=staff, prefix='training')
        # Use instance so management_form counts stay consistent on POST
        bank_formset = BankFormSet(instance=staff, prefix='bank')


        
        try:
            license = staff.driving_license
            license_form = DrivingLicenseForm(instance=license, prefix='license')
        except DrivingLicense.DoesNotExist:
            license_form = DrivingLicenseForm(prefix='license')
    
    context = {
        'form': form,
        'education_formset': education_formset,
        'work_formset': work_formset,
        'certificate_formset': certificate_formset,
        'training_formset': training_formset,
        'license_form': license_form,
        'staff': staff,
        'bank_formset': bank_formset,
        'has_errors': (request.method == 'POST' and (
            not form_valid or not education_valid or not work_valid or 
            not certificate_valid or not training_valid or not license_valid or not bank_valid
        )),
    }
    
    return render(request, 'dashboards/staff_registration.html', context)


def staff_list(request):
    staff_list = StaffRegistration.objects.all()
    context = {'staff_list': staff_list}
    return render(request, 'dashboards/staff_list.html', context)


def staff_detail(request, pk):
    staff = get_object_or_404(StaffRegistration, pk=pk)
    context = {'staff': staff}
    return render(request, 'dashboards/staff_detail.html', context)


def staff_delete(request, pk):
    staff = get_object_or_404(StaffRegistration, pk=pk)
    if request.method == 'POST':
        staff.delete()
        messages.success(request, 'Staff deleted successfully!')
        return redirect('staff_list')
    context = {'staff': staff}
    return render(request, 'dashboards/staff_confirm_delete.html', context)


#New
def generate_staff_registration_pdf(request, pk):
    """Generate Staff Registration PDF matching the exact form layout - fits on single A4 page."""
    staff = get_object_or_404(StaffRegistration, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="staff_registration_{staff.staff_id}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=0.35 * inch, rightMargin=0.35 * inch,
        topMargin=0.3 * inch, bottomMargin=0.3 * inch,
    )
    elements = []
    W = 7.77 * inch  # usable width on A4 with 0.35" margins each side

    BLACK = colors.black
    PEACH = colors.HexColor('#F5C9A0')
    GREY  = colors.HexColor('#E8E8E8')
    WHITE = colors.white
    LN    = 0.5
    PAD   = 2

    def p(text, size=7, bold=False, align=TA_LEFT):
        font = 'Helvetica-Bold' if bold else 'Helvetica'
        return Paragraph(
            str(text) if text else '',
            ParagraphStyle('s', fontName=font, fontSize=size, leading=size + 2,
                           alignment=align, spaceAfter=0, spaceBefore=0),
        )

    def _val(v, fallback=''):
        return str(v) if v and str(v).strip() else fallback

    BASE_STYLE = [
        ('GRID',         (0, 0), (-1, -1), LN,  BLACK),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING',   (0, 0), (-1, -1), PAD),
        ('BOTTOMPADDING',(0, 0), (-1, -1), PAD),
    ]

    # ── TITLE ──────────────────────────────────────────────────────────────────
    title_tbl = Table([[p('STAFF MANAGEMENT', 14, True, TA_CENTER)]], colWidths=[W])
    title_tbl.setStyle(TableStyle([
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('LINEBELOW',     (0, 0), (-1, -1), 0, WHITE),
    ]))
    elements.append(title_tbl)

    sub_tbl = Table([[p('STAFF REGISTRATION', 9, True, TA_CENTER)]], colWidths=[W])
    sub_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), PEACH),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(sub_tbl)
    elements.append(Spacer(1, 2))

    # ── MAIN INFO (STAFF ID / FULL NAME / ADDRESS / PHOTO) ────────────────────
    main_c = [
        W * 0.085,   # col0: STAFF ID / Full Name / Address label
        W * 0.070,   # col1: Permanent / Present sub-label
        W * 0.290,   # col2: main value
        W * 0.105,   # col3: Gender / Marital Status label
        W * 0.310,   # col4: Gender / Marital Status value combined with empty space
        W * 0.140,   # col5: CANDIDATE PHOTO
    ]

    photo_cell = p('CANDIDATE\nPHOTO', 7, True, TA_CENTER)
    if staff.candidate_photo:
        try:
            photo_cell = Image(staff.candidate_photo.path, width=0.95 * inch, height=1.05 * inch)
        except Exception:
            pass

    gender_display   = staff.get_gender_display() if staff.gender else ''
    marital_display  = _val(staff.marital_status)

    main_data = [
        [p('STAFF ID',  7, True), '', p(_val(staff.staff_id), 7),
         p('Gender', 7, True), p(gender_display, 7), photo_cell],
        [p('Full Name', 7, True), '', p(_val(staff.full_name), 7),
         p('Marital Status', 7, True), p(marital_display, 7), ''],
        [p('Address', 7, True), p('Permanent', 6, True), p(_val(staff.permanent_address), 7),
         '', '', ''],
        ['', p('Present', 6, True), p(_val(staff.present_address), 7), '', '', ''],
    ]

    main_tbl = Table(main_data, colWidths=main_c, rowHeights=[0.28 * inch] * 4)
    main_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (1, 0)),        # STAFF ID spans cols 0-1
        ('SPAN', (0, 1), (1, 1)),        # Full Name spans cols 0-1
        ('SPAN', (5, 0), (5, 3)),        # Photo spans all 4 rows
        ('SPAN', (0, 2), (0, 3)),        # Address label spans rows 2-3
        ('SPAN', (2, 2), (4, 2)),        # Permanent address value spans cols 2-4
        ('SPAN', (2, 3), (4, 3)),        # Present address value spans cols 2-4
        ('BACKGROUND', (0, 0), (1, 0), GREY),
        ('BACKGROUND', (3, 0), (3, 0), GREY),
        ('BACKGROUND', (0, 1), (1, 1), GREY),
        ('BACKGROUND', (3, 1), (3, 1), GREY),
        ('BACKGROUND', (0, 2), (1, 3), GREY),
        ('ALIGN',  (5, 0), (5, 3), 'CENTER'),
        ('VALIGN', (5, 0), (5, 3), 'MIDDLE'),
    ]))
    elements.append(main_tbl)

    # ── ID / PASSPORT ─────────────────────────────────────────────────────────
    id_c = [W*0.115, W*0.225, W*0.095, W*0.175, W*0.095, W*0.295]
    id_data = [[
        p('Passport No', 7, True),
        p(_val(staff.id_passport_no), 7),
        p('Date of Issue', 7, True),
        p(str(staff.date_of_issue) if staff.date_of_issue else '', 7),
        p('Issue From', 7, True),
        p(_val(staff.issue_from), 7),
    ]]
    id_tbl = Table(id_data, colWidths=id_c, rowHeights=[0.28 * inch])
    id_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('BACKGROUND', (0, 0), (0, 0), GREY),
        ('BACKGROUND', (2, 0), (2, 0), GREY),
        ('BACKGROUND', (4, 0), (4, 0), GREY),
    ]))
    elements.append(id_tbl)

    # ── PERSONAL INFORMATION ──────────────────────────────────────────────────
    dob = staff.date_of_birth.strftime('%d-%m-%Y') if staff.date_of_birth else ''
    pi_c = [W*0.115, W*0.155, W*0.065, W*0.095, W*0.095, W*0.165, W*0.165, W*0.145]
    pi_data = [
        # Header row
        [p('Personal Information', 7, True),
         p('Date of Birth',  7, True, TA_CENTER),
         p('Eye Lense',      7, True, TA_CENTER), '',
         p('Blood Group',    7, True, TA_CENTER),
         p('Phone No.',      7, True, TA_CENTER), '',
         p('Email ID',       7, True, TA_CENTER)],
        # Value row (Right / Left eye sub-labels + data)
        ['',
         p(dob, 7, align=TA_CENTER),
         p('Right', 6, True, TA_CENTER),
         p('Left',  6, True, TA_CENTER),
         p(_val(staff.blood_group), 7, align=TA_CENTER),
         p(_val(staff.phone_no),    7, align=TA_CENTER), '',
         p(_val(staff.email_id),    7, align=TA_CENTER)],
        # Eye-lens value row
        ['', '',
         p(_val(staff.eye_lense_right), 7, align=TA_CENTER),
         p(_val(staff.eye_lense_left),  7, align=TA_CENTER),
         '', '', '', ''],
    ]
    pi_tbl = Table(pi_data, colWidths=pi_c, rowHeights=[0.22 * inch] * 3)
    pi_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (0, 2)),   # Personal Information label spans 3 rows
        ('SPAN', (1, 0), (1, 0)),   # DOB header
        ('SPAN', (1, 1), (1, 2)),   # DOB value spans rows 1-2
        ('SPAN', (2, 0), (3, 0)),   # Eye Lense header spans 2 cols
        ('SPAN', (4, 0), (4, 0)),   # Blood Group header
        ('SPAN', (4, 1), (4, 2)),   # Blood Group value spans rows 1-2
        ('SPAN', (5, 0), (6, 0)),   # Phone No header spans 2 cols
        ('SPAN', (5, 1), (6, 2)),   # Phone value spans 2 cols x 2 rows
        ('SPAN', (7, 0), (7, 0)),   # Email header
        ('SPAN', (7, 1), (7, 2)),   # Email value spans rows 1-2
        ('BACKGROUND', (0, 0), (0, 2), GREY),
        ('BACKGROUND', (1, 0), (1, 0), GREY),
        ('BACKGROUND', (2, 0), (3, 0), GREY),
        ('BACKGROUND', (4, 0), (4, 0), GREY),
        ('BACKGROUND', (5, 0), (6, 0), GREY),
        ('BACKGROUND', (7, 0), (7, 0), GREY),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(pi_tbl)

    # ── FAMILY RECORDS ────────────────────────────────────────────────────────
    fam_c = [W*0.115, W*0.490, W*0.115, W*0.280]
    fam_data = [
        [p('Family Records', 7, True), p('', 7),
         p('CONTACT NO', 7, True, TA_CENTER), p(_val(staff.contact_no), 7)],
        [p('Spouse Name',   7, True), p(_val(staff.spouse_name), 7), '', ''],
    ]
    fam_tbl = Table(fam_data, colWidths=fam_c, rowHeights=[0.25 * inch, 0.25 * inch])
    fam_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (3, 0), (3, 1)),   # CONTACT NO value spans 2 rows
        ('SPAN', (1, 1), (2, 1)),   # Spouse Name value spans 2 cols
        ('BACKGROUND', (0, 0), (0, 0), GREY),
        ('BACKGROUND', (2, 0), (2, 0), GREY),
        ('BACKGROUND', (0, 1), (0, 1), GREY),
    ]))
    elements.append(fam_tbl)
    elements.append(Spacer(1, 3))

    # ── BANK INFORMATION ──────────────────────────────────────────────────────
    bank_hdr = Table([[p('BANK INFORMATION', 9, True, TA_CENTER)]], colWidths=[W])
    bank_hdr.setStyle(TableStyle([
        ('GRID',         (0, 0), (-1, -1), LN, BLACK),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING',  (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
    ]))
    elements.append(bank_hdr)

    bank_c = [W*0.145, W*0.355, W*0.145, W*0.355]
    bank_info = staff.bank_info.first()
    
    bank_data = [
        [p('Bank Name', 7, True), p(_val(bank_info.bank_name) if bank_info else '', 7),
         p('Branch Name', 7, True), p(_val(bank_info.branch_name) if bank_info else '', 7)],
        [p('Account No.', 7, True), p(_val(bank_info.account_no) if bank_info else '', 7),
         p('Account Holder', 7, True), p(_val(bank_info.account_holder_name) if bank_info else '', 7)]
    ]
    
    bank_tbl = Table(bank_data, colWidths=bank_c, rowHeights=[0.25 * inch, 0.25 * inch])
    bank_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('BACKGROUND', (0, 0), (0, 1), GREY),
        ('BACKGROUND', (2, 0), (2, 1), GREY),
    ]))
    elements.append(bank_tbl)
    elements.append(Spacer(1, 3))

    # ── EDUCATIONAL HISTORY ───────────────────────────────────────────────────
    edu_hdr = Table([[p('EDUCATIONAL HISTORY', 9, True, TA_CENTER)]], colWidths=[W])
    edu_hdr.setStyle(TableStyle([
        ('GRID',         (0, 0), (-1, -1), LN, BLACK),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING',  (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
    ]))
    elements.append(edu_hdr)

    edu_c = [W*0.135, W*0.355, W*0.075, W*0.075, W*0.075, W*0.075, W*0.095, W*0.115]
    edu_levels_display = [
        'Primary School', 'Junior H. School', 'Higher S. School',
        'College / University', 'Graduate University', 'Graduate University', 'Other School',
    ]
    edu_level_keys = ['Primary', 'Junior', 'Higher', 'College', 'Graduate', 'PostGraduate', 'Other']
    edu_map = {e.pass_level: e for e in staff.education_history.all()}

    edu_data = [
        [p('Pass Level', 7, True, TA_CENTER),
         p('Name of School', 7, True, TA_CENTER),
         p('Admission & Graduation', 7, True, TA_CENTER), '', '', '',
         p('Enrolled Years', 7, True, TA_CENTER), ''],
        ['', '',
         p('Year', 7, True, TA_CENTER), p('Month', 7, True, TA_CENTER),
         p('Year', 7, True, TA_CENTER), p('Month', 7, True, TA_CENTER),
         '', ''],
    ]
    for label, key in zip(edu_levels_display, edu_level_keys):
        e = edu_map.get(key)
        edu_data.append([
            p(label, 7),
            p(_val(e.name_of_school) if e else '', 7),
            p(_val(e.admission_year)  if e else '', 7, align=TA_CENTER),
            p(_val(e.admission_month) if e else '', 7, align=TA_CENTER),
            p(_val(e.graduation_year) if e else '', 7, align=TA_CENTER),
            p(_val(e.graduation_month)if e else '', 7, align=TA_CENTER),
            p(_val(e.enrolled_years)  if e else '', 7, align=TA_CENTER),
            p('Years', 7, align=TA_RIGHT),
        ])

    edu_tbl = Table(edu_data, colWidths=edu_c, rowHeights=[0.22 * inch] * len(edu_data))
    edu_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (5, 0)),   # Admission & Graduation header
        ('SPAN', (6, 0), (7, 0)),   # Enrolled Years header
        ('SPAN', (6, 1), (7, 1)),
        ('BACKGROUND', (0, 0), (-1, 1), GREY),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(edu_tbl)
    elements.append(Spacer(1, 3))

    # ── WORKING EXPERIENCE ────────────────────────────────────────────────────
    work_hdr = Table([[p('WORKING EXPERIENCE', 9, True, TA_CENTER)]], colWidths=[W])
    work_hdr.setStyle(TableStyle([
        ('GRID',         (0, 0), (-1, -1), LN, BLACK),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        ('LEFTPADDING',  (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
    ]))
    elements.append(work_hdr)

    work_c = [W*0.135, W*0.355, W*0.075, W*0.075, W*0.075, W*0.075, W*0.095, W*0.115]
    work_qs = list(staff.work_experience.all())
    while len(work_qs) < 3:
        work_qs.append(None)

    work_data = [
        [p('Type of Work',           7, True, TA_CENTER),
         p('Name of Working Company',7, True, TA_CENTER),
         p('Date of Join & Resign',  7, True, TA_CENTER), '', '', '',
         p('Working Years',          7, True, TA_CENTER), ''],
        ['', '',
         p('Years', 7, True, TA_CENTER), p('Months', 7, True, TA_CENTER),
         p('Years', 7, True, TA_CENTER), p('Months', 7, True, TA_CENTER),
         '', ''],
    ]
    for w in work_qs[:3]:
        work_data.append([
            p(_val(w.type_of_work)    if w else '', 7, align=TA_CENTER),
            p(_val(w.name_of_company) if w else '', 7),
            p(_val(w.join_year)       if w else '', 7, align=TA_CENTER),
            p(_val(w.join_month)      if w else '', 7, align=TA_CENTER),
            p(_val(w.resign_year)     if w else '', 7, align=TA_CENTER),
            p(_val(w.resign_month)    if w else '', 7, align=TA_CENTER),
            p(_val(w.working_years)   if w else '', 7, align=TA_CENTER),
            p('Years', 7, align=TA_RIGHT),
        ])

    work_tbl = Table(work_data, colWidths=work_c, rowHeights=[0.22 * inch] * len(work_data))
    work_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('SPAN', (2, 0), (5, 0)),
        ('SPAN', (6, 0), (7, 0)),
        ('SPAN', (6, 1), (7, 1)),
        ('BACKGROUND', (0, 0), (-1, 1), GREY),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(work_tbl)
    elements.append(Spacer(1, 3))

    # ── CERTIFICATE OF SKILLS + SKILLS TRAINING STATUS ───────────────────────
    half = W / 2
    cert_qs  = list(staff.certificates.all())
    train_qs = list(staff.training_status.all())
    max_rows = max(len(cert_qs), len(train_qs), 3)

    cert_c_inner  = [half * 0.28, half * 0.72]
    train_c_inner = [half * 0.35, half * 0.65]

    cert_data = [
        [p('CERTIFICATE OF SKILLS',  8, True, TA_CENTER), ''],
        [p('Pass Year & Month',       7, True, TA_CENTER),
         p('Name of Certificate',     7, True, TA_CENTER)],
    ]
    train_data = [
        [p('SKILLS TRAINING STATUS', 8, True, TA_CENTER), ''],
        [p('Join Year and Month',     7, True, TA_CENTER),
         p('Organization',            7, True, TA_CENTER)],
    ]
    for i in range(max_rows):
        c = cert_qs[i]  if i < len(cert_qs)  else None
        t = train_qs[i] if i < len(train_qs) else None
        cert_data.append([
            p(f'{_val(c.pass_year)}/{_val(c.pass_month)}' if c else '', 7, align=TA_CENTER),
            p(_val(c.name_of_certificate) if c else '', 7),
        ])
        train_data.append([
            p(f'{_val(t.join_year)}/{_val(t.join_month)}' if t else '', 7, align=TA_CENTER),
            p(_val(t.organization) if t else '', 7),
        ])

    cert_tbl = Table(cert_data, colWidths=cert_c_inner,
                     rowHeights=[0.22 * inch] * len(cert_data))
    cert_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 1), GREY),
    ]))

    train_tbl = Table(train_data, colWidths=train_c_inner,
                      rowHeights=[0.22 * inch] * len(train_data))
    train_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (-1, 1), GREY),
    ]))

    skills_row = Table([[cert_tbl, train_tbl]], colWidths=[half, half])
    skills_row.setStyle(TableStyle([
        ('LEFTPADDING',  (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 0),
        ('VALIGN',       (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(skills_row)
    elements.append(Spacer(1, 3))

    # ── DRIVING LICENSE ───────────────────────────────────────────────────────
    license = None
    try:
        license = staff.driving_license
    except Exception:
        pass

    dl_c = [W*0.18, W*0.22, W*0.60]
    dl_data = [
        [p('DRIVING LICENSE', 8, True, TA_CENTER),
         p('Pass Year & Month', 7, True, TA_CENTER),
         p('Discretion of License', 7, True, TA_CENTER)],
        ['',
         p(f'{_val(license.pass_year)}/{_val(license.pass_month)}' if license else '', 7, align=TA_CENTER),
         p(_val(license.discretion_of_license) if license else '', 7)],
    ]
    dl_tbl = Table(dl_data, colWidths=dl_c, rowHeights=[0.25 * inch, 0.25 * inch])
    dl_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('SPAN', (0, 0), (0, 1)),   # Driving License label spans 2 rows
        ('BACKGROUND', (0, 0), (0, 1), GREY),
        ('BACKGROUND', (1, 0), (1, 0), GREY),
        ('BACKGROUND', (2, 0), (2, 0), GREY),
        ('ALIGN', (0, 0), (0, 1), 'CENTER'),
    ]))
    elements.append(dl_tbl)
    elements.append(Spacer(1, 3))

    # ── HOBBIES & MOTIVATION ──────────────────────────────────────────────────
    hm_c = [W / 2, W / 2]
    hm_data = [
        [p('Hobbies, Special skills, etc.', 8, True),
         p('Motivation, Self-promotion',    8, True)],
        [p(_val(staff.hobbies),    7),
         p(_val(staff.motivation), 7)],
    ]
    hm_tbl = Table(hm_data, colWidths=hm_c, rowHeights=[0.25 * inch, 0.65 * inch])
    hm_tbl.setStyle(TableStyle(BASE_STYLE + [
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1,  0), GREY),
    ]))
    elements.append(hm_tbl)

    # ── BUILD ─────────────────────────────────────────────────────────────────
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response
def generate_staff_id_card_pdf(request, pk):
    """Generate Staff ID Card PDF"""
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_id_card_{staff.staff_id}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=28, textColor=colors.HexColor('#ff9966'), alignment=TA_CENTER)
    
    elements.append(Paragraph("STAFF ID CARD", title_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # ID Card Design (Front)
    card_data = [
        ['', 'AQUA GROUP'],
        ['', 'STAFF IDENTIFICATION CARD'],
        ['Photo', ''],
        ['', f"Name: {staff.full_name}"],
        ['', f"ID: {staff.staff_id}"],
        ['', f"Position: Staff Member"],
        ['', f"Department: General"],
        ['', f"Valid Until: {datetime.now().year + 5}"],
    ]
    
    card_table = Table(card_data, colWidths=[2*inch, 4*inch])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 1), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 1), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 1), 16),
        ('FONTSIZE', (0, 2), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#667eea')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    elements.append(card_table)
    elements.append(Spacer(1, 0.5*inch))
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)
    elements.append(Paragraph("This card is property of Aqua Group", footer_style))
    elements.append(Paragraph("If found, please return to HR Department", footer_style))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


def generate_staff_login_report_pdf(request, pk):
    """Generate Staff Login Report PDF"""
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_login_report_{staff.staff_id}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=24, textColor=colors.HexColor('#667eea'), alignment=TA_CENTER)
    
    elements.append(Paragraph("STAFF LOGIN REPORT", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Report Header
    report_data = [
        ['Staff ID:', staff.staff_id],
        ['Full Name:', staff.full_name],
        ['Email:', staff.email_id],
        ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
    ]
    
    report_table = Table(report_data, colWidths=[2*inch, 4*inch])
    report_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(report_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Sample Login Activity (you can customize this based on your actual login tracking)
    elements.append(Paragraph("LOGIN ACTIVITY SUMMARY", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    activity_data = [
        ['Date', 'Login Time', 'Logout Time', 'Duration', 'Status'],
        [datetime.now().strftime('%Y-%m-%d'), '09:00 AM', '05:00 PM', '8 hours', 'Active'],
        ['Sample data', 'Coming soon', 'Coming soon', '-', 'Pending'],
    ]
    
    activity_table = Table(activity_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1*inch])
    activity_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))
    
    elements.append(activity_table)
    elements.append(Spacer(1, 0.5*inch))
    
    elements.append(Paragraph("Note: Implement actual login tracking system for real data", styles['Normal']))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


def generate_staff_login_id_pdf(request, pk):
    """Generate Staff Login ID PDF"""
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_login_id_{staff.staff_id}.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=28, textColor=colors.HexColor('#667eea'), alignment=TA_CENTER)
    
    elements.append(Paragraph("STAFF LOGIN CREDENTIALS", title_style))
    elements.append(Spacer(1, 0.5*inch))
    
    # Login credentials box
    login_data = [
        ['STAFF LOGIN INFORMATION'],
        [''],
        ['Full Name:', staff.full_name],
        ['Staff ID:', staff.staff_id],
        ['Email/Username:', staff.email_id],
        ['Default Password:', 'staff@' + staff.staff_id],
        [''],
        ['Portal URL:', 'https://staff.aquagroup.com'],
        [''],
        ['Please change your password after first login'],
    ]
    
    login_table = Table(login_data, colWidths=[6*inch])
    login_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 18),
        ('FONTSIZE', (0, 2), (-1, -2), 14),
        ('FONTNAME', (0, 2), (0, -2), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 2, colors.HexColor('#667eea')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('TOPPADDING', (0, 0), (-1, -1), 15),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
    ]))
    
    elements.append(login_table)
    elements.append(Spacer(1, 0.5*inch))
    
    elements.append(Paragraph("IMPORTANT SECURITY NOTES:", styles['Heading3']))
    elements.append(Spacer(1, 0.2*inch))
    
    notes = [
        "1. Keep your login credentials confidential",
        "2. Do not share your password with anyone",
        "3. Change your password regularly",
        "4. Contact IT support if you forget your password",
        "5. Report any suspicious activity immediately",
    ]
    
    for note in notes:
        elements.append(Paragraph(note, styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
    
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response



#Manger redirect to SSW AND STUDENTS
# views.py
from django.shortcuts import render

def ssw_working_visa(request):
    return render(request, 'canstud/managerssw.html')

def student_visa(request):
    return render(request, 'canstud/manager_student.html')

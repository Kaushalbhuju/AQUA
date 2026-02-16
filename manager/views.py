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
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from io import BytesIO
from datetime import datetime

def staff_registration_create(request):
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
    }
    
    return render(request, 'dashboards/staff_registration.html', context)


def staff_registration_update(request, pk):
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
        
        if form.is_valid() and education_formset.is_valid() and work_formset.is_valid() and certificate_formset.is_valid() and training_formset.is_valid() and license_form.is_valid() and bank_formset.is_valid():
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
    """Generate Staff Registration PDF matching the exact form layout from the image - fits on single A4 page."""
    staff = get_object_or_404(StaffRegistration, pk=pk)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="staff_registration_{staff.staff_id}.pdf"'

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=0.35 * inch, rightMargin=0.35 * inch,
        topMargin=0.25 * inch, bottomMargin=0.2 * inch,
    )
    elements = []
    W = 7.4 * inch  # total usable width

    BLACK = colors.black
    LIGHT_BG = colors.HexColor('#FDE8D0')  # peach header background
    GREY_BG = colors.HexColor('#f8f9fa')
    LN = 0.5  # thinner line for compact layout

    # Compact paragraph helper - smaller leading for tight fit
    def _p(text, size=7, bold=False, align=TA_LEFT):
        font = 'Helvetica-Bold' if bold else 'Helvetica'
        return Paragraph(
            str(text) if text else '',
            ParagraphStyle('c', fontName=font, fontSize=size, leading=size + 2, alignment=align),
        )

    def _val(v, fallback=''):
        return str(v) if v else fallback

    # Compact grid helper with minimal padding
    PAD = 2
    def _grid(t, col_widths, extra_style=None):
        ts = [
            ('GRID', (0, 0), (-1, -1), LN, BLACK),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), PAD),
            ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
            ('TOPPADDING', (0, 0), (-1, -1), PAD),
            ('BOTTOMPADDING', (0, 0), (-1, -1), PAD),
        ]
        if extra_style:
            ts.extend(extra_style)
        tbl = Table(t, colWidths=col_widths, hAlign='LEFT')
        tbl.setStyle(TableStyle(ts))
        return tbl

    # ── HEADER ──
    header_data = [[_p('STAFF MANAGEMENT', 14, True, TA_CENTER)]]
    header = Table(header_data, colWidths=[W])
    header.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(header)

    sub_header_data = [[_p('STAFF REGISTRATION', 9, True, TA_CENTER)]]
    sub_header = Table(sub_header_data, colWidths=[W])
    sub_header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(sub_header)
    elements.append(Spacer(1, 3))

    # ── PHOTO ──
    photo_content = _p('CANDIDATE\nPHOTO', 7, True, TA_CENTER)
    if staff.candidate_photo:
        try:
            photo_content = Image(staff.candidate_photo.path, width=0.9 * inch, height=1.1 * inch)
        except Exception:
            pass

    # ── ROW 1: Staff ID, Gender, Photo + Full Name, Marital Status ──
    gender_display = staff.get_gender_display() if staff.gender else ''
    row1 = [
        [_p('STAFF ID', 7, True), _p(_val(staff.staff_id), 7), _p('Gender', 7, True), _p(gender_display, 7), photo_content],
        [_p('Full Name', 7, True), _p(_val(staff.full_name), 7), _p('Marital Status', 7, True), _p(_val(staff.marital_status), 7), ''],
    ]
    c1 = [0.7 * inch, 2.5 * inch, 0.9 * inch, 1.5 * inch, 1.8 * inch]
    top_tbl = Table(row1, colWidths=c1)
    top_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD),
        ('RIGHTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING', (0, 0), (-1, -1), PAD),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD),
        ('BACKGROUND', (0, 0), (0, -1), GREY_BG),
        ('BACKGROUND', (2, 0), (2, -1), GREY_BG),
        ('SPAN', (4, 0), (4, 1)),
        ('ALIGN', (4, 0), (4, 1), 'CENTER'),
        ('VALIGN', (4, 0), (4, 1), 'MIDDLE'),
    ]))
    elements.append(top_tbl)

    # ── Address rows ──
    addr_data = [
        [_p('Address', 7, True), _p('Permanent', 6, True), _p(_val(staff.permanent_address), 7)],
        ['', _p('Present', 6, True), _p(_val(staff.present_address), 7)],
    ]
    addr_c = [0.7 * inch, 0.7 * inch, 6.0 * inch]
    addr_tbl = Table(addr_data, colWidths=addr_c)
    addr_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING', (0, 0), (-1, -1), PAD),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD),
        ('BACKGROUND', (0, 0), (0, -1), GREY_BG),
        ('BACKGROUND', (1, 0), (1, -1), GREY_BG),
        ('SPAN', (0, 0), (0, 1)),
    ]))
    elements.append(addr_tbl)

    # ── ID / Passport ──
    id_data = [[
        _p('ID / Passport No.', 7, True),
        _p(_val(staff.id_passport_no), 7),
        _p('Date of Issue', 7, True),
        _p(str(staff.date_of_issue) if staff.date_of_issue else '', 7),
        _p('Issue From', 7, True),
        _p(_val(staff.issue_from), 7),
    ]]
    id_c = [1.0 * inch, 1.7 * inch, 0.8 * inch, 1.0 * inch, 0.8 * inch, 2.1 * inch]
    elements.append(_grid(id_data, id_c, [
        ('BACKGROUND', (0, 0), (0, 0), GREY_BG),
        ('BACKGROUND', (2, 0), (2, 0), GREY_BG),
        ('BACKGROUND', (4, 0), (4, 0), GREY_BG),
    ]))

    # ── Personal Information ──
    dob = str(staff.date_of_birth) if staff.date_of_birth else ''
    pi_data = [
        [_p('Personal\nInformation', 7, True), _p('Date of Birth', 6, True), '', _p('Eye Lense', 6, True), '', _p('Blood Group', 6, True), _p('Phone No.', 6, True), _p('Email ID', 6, True)],
        ['', _p(dob, 7), _p('Height', 6, True), _p(f'R: {_val(staff.eye_lense_right)}', 6), _p(f'L: {_val(staff.eye_lense_left)}', 6), _p(_val(staff.blood_group), 7), _p(_val(staff.phone_no), 7), _p(_val(staff.email_id), 6)],
    ]
    pi_c = [0.9 * inch, 1.0 * inch, 0.6 * inch, 0.9 * inch, 0.6 * inch, 0.8 * inch, 1.1 * inch, 2.1 * inch]
    pi_tbl = Table(pi_data, colWidths=pi_c)
    pi_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING', (0, 0), (-1, -1), PAD),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD),
        ('BACKGROUND', (0, 0), (0, -1), GREY_BG),
        ('BACKGROUND', (2, 0), (2, 0), GREY_BG),
        ('BACKGROUND', (3, 0), (4, 0), GREY_BG),
        ('BACKGROUND', (5, 0), (5, 0), GREY_BG),
        ('BACKGROUND', (6, 0), (6, 0), GREY_BG),
        ('BACKGROUND', (7, 0), (7, 0), GREY_BG),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 0)),
        ('SPAN', (3, 0), (4, 0)),
    ]))
    elements.append(pi_tbl)

    # ── Family Records ──
    fr_data = [[
        _p('Family Records', 7, True),
        _p(_val(staff.spouse_name), 7),
        _p('CONTACT NO', 7, True), _p(_val(staff.contact_no), 7),
    ]]
    fr_sub = [[
        _p('Spouse Name', 7, True), '', '', '',
    ]]
    # Combine as two rows
    fr_all = [
        [_p('Family Records', 7, True), '', '', _p('CONTACT NO', 7, True)],
        [_p('Spouse Name', 7, True), _p(_val(staff.spouse_name), 7), '', _p(_val(staff.contact_no), 7)],
    ]
    fr_c = [0.9 * inch, 3.3 * inch, 0.8 * inch, 2.4 * inch]
    # Simpler: single row matching image
    fr_all = [[
        _p('Family Records', 7, True), '', _p('CONTACT NO', 7, True), '',
    ], [
        _p('Spouse Name', 7, True), _p(_val(staff.spouse_name), 7), '', _p(_val(staff.contact_no), 7),
    ]]
    fr_c = [1.0 * inch, 3.2 * inch, 1.0 * inch, 2.2 * inch]
    fr_tbl = Table(fr_all, colWidths=fr_c)
    fr_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING', (0, 0), (-1, -1), PAD),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD),
        ('BACKGROUND', (0, 0), (0, -1), GREY_BG),
        ('BACKGROUND', (2, 0), (2, 0), GREY_BG),
        ('SPAN', (0, 0), (1, 0)),  # "Family Records" spans first row
        ('SPAN', (2, 0), (3, 0)),  # "CONTACT NO" label spans
    ]))
    elements.append(fr_tbl)
    elements.append(Spacer(1, 4))

    # ── EDUCATIONAL HISTORY ──
    elements.append(_grid(
        [[_p('EDUCATIONAL HISTORY', 8, True, TA_CENTER)]],
        [W], [('BACKGROUND', (0, 0), (-1, -1), GREY_BG)]
    ))

    edu_top = [
        _p('Pass Level', 6, True), _p('Name of School', 6, True),
        _p('Admission & Graduation', 6, True, TA_CENTER), '', '', '',
        _p('Enrolled\nYears', 6, True, TA_CENTER),
    ]
    edu_sub = [
        '', '',
        _p('Year', 6, True, TA_CENTER), _p('Month', 6, True, TA_CENTER),
        _p('Year', 6, True, TA_CENTER), _p('Month', 6, True, TA_CENTER),
        '',
    ]
    edu_c = [1.05 * inch, 2.05 * inch, 0.65 * inch, 0.65 * inch, 0.65 * inch, 0.65 * inch, 1.0 * inch]
    edu_all = [edu_top, edu_sub]

    edu_levels = ['Primary School', 'Junior H. School', 'Higher S. School',
                  'College / University', 'Graduate University', 'Graduate University', 'Other School']
    edu_map = {}
    for edu in staff.education_history.all():
        edu_map[edu.pass_level] = edu

    level_keys = ['Primary', 'Junior', 'Higher', 'College', 'Graduate', 'PostGraduate', 'Other']
    for i, key in enumerate(level_keys):
        edu_obj = edu_map.get(key)
        if edu_obj:
            edu_all.append([
                _p(edu_levels[i], 6), _p(_val(edu_obj.name_of_school), 6),
                _p(_val(edu_obj.admission_year), 6, align=TA_CENTER),
                _p(_val(edu_obj.admission_month), 6, align=TA_CENTER),
                _p(_val(edu_obj.graduation_year), 6, align=TA_CENTER),
                _p(_val(edu_obj.graduation_month), 6, align=TA_CENTER),
                _p(f'{_val(edu_obj.enrolled_years)} Yrs' if edu_obj.enrolled_years else 'Years', 6, align=TA_CENTER),
            ])
        else:
            edu_all.append([
                _p(edu_levels[i], 6), '', '', '', '', '',
                _p('Years', 6, align=TA_CENTER),
            ])

    edu_tbl = Table(edu_all, colWidths=edu_c)
    edu_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('BACKGROUND', (0, 0), (-1, 1), GREY_BG),
        ('SPAN', (2, 0), (5, 0)),
        ('SPAN', (6, 0), (6, 1)),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(edu_tbl)
    elements.append(Spacer(1, 4))

    # ── WORKING EXPERIENCE ──
    elements.append(_grid(
        [[_p('WORKING EXPERIENCE', 8, True, TA_CENTER)]],
        [W], [('BACKGROUND', (0, 0), (-1, -1), GREY_BG)]
    ))

    work_top = [
        _p('Type of Work', 6, True), _p('Name of Working Company', 6, True),
        _p('Date of Join & Resign', 6, True, TA_CENTER), '', '', '',
        _p('Working\nYears', 6, True, TA_CENTER),
    ]
    work_sub = ['', '', _p('Year', 6, True, TA_CENTER), _p('Month', 6, True, TA_CENTER),
                _p('Year', 6, True, TA_CENTER), _p('Month', 6, True, TA_CENTER), '']
    work_c = edu_c  # same widths
    work_all = [work_top, work_sub]

    work_qs = list(staff.work_experience.all())
    for _ in range(max(3 - len(work_qs), 0)):
        work_qs.append(None)
    for w in work_qs:
        if w:
            work_all.append([
                _p(_val(w.type_of_work), 6), _p(_val(w.name_of_company), 6),
                _p(_val(w.join_year), 6, align=TA_CENTER), _p(_val(w.join_month), 6, align=TA_CENTER),
                _p(_val(w.resign_year), 6, align=TA_CENTER), _p(_val(w.resign_month), 6, align=TA_CENTER),
                _p(f'{_val(w.working_years)} Yrs' if w.working_years else 'Years', 6, align=TA_CENTER),
            ])
        else:
            work_all.append(['', '', '', '', '', '', _p('Years', 6, align=TA_CENTER)])

    work_tbl = Table(work_all, colWidths=work_c)
    work_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('BACKGROUND', (0, 0), (-1, 1), GREY_BG),
        ('SPAN', (2, 0), (5, 0)),
        ('SPAN', (6, 0), (6, 1)),
        ('SPAN', (0, 0), (0, 1)),
        ('SPAN', (1, 0), (1, 1)),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
    ]))
    elements.append(work_tbl)
    elements.append(Spacer(1, 4))

    # ── CERTIFICATE OF SKILLS + SKILLS TRAINING STATUS (side by side) ──
    cert_train_header = [[
        _p('CERTIFICATE OF SKILLS', 8, True, TA_CENTER),
        _p('SKILLS TRAINING STATUS', 8, True, TA_CENTER),
    ]]
    ct_header = Table(cert_train_header, colWidths=[W / 2, W / 2])
    ct_header.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('BACKGROUND', (0, 0), (-1, -1), GREY_BG),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(ct_header)

    cert_qs = list(staff.certificates.all())
    train_qs = list(staff.training_status.all())
    max_rows = max(len(cert_qs), len(train_qs), 3)
    for _ in range(max_rows - len(cert_qs)):
        cert_qs.append(None)
    for _ in range(max_rows - len(train_qs)):
        train_qs.append(None)

    ct_c = [0.85 * inch, 1.65 * inch, 0.85 * inch, 1.65 * inch, 0.85 * inch, 1.55 * inch]
    ct_header_row = [
        _p('Pass Year\n& Month', 5, True, TA_CENTER), _p('Name of Certificate', 6, True, TA_CENTER),
        _p('Join Year\nand Month', 5, True, TA_CENTER), '',
        _p('Organization', 6, True, TA_CENTER), '',
    ]
    ct_all = [ct_header_row]

    for i in range(max_rows):
        c = cert_qs[i]
        t = train_qs[i]
        ct_all.append([
            _p(f'{_val(c.pass_year)}/{_val(c.pass_month)}' if c and (c.pass_year or c.pass_month) else '', 6, align=TA_CENTER) if c else '',
            _p(_val(c.name_of_certificate) if c else '', 6),
            _p(f'{_val(t.join_year)}/{_val(t.join_month)}' if t and (t.join_year or t.join_month) else '', 6, align=TA_CENTER) if t else '',
            _p(_val(t.name_of_training) if t else '', 6),
            _p(f'{_val(t.pass_year)}/{_val(t.pass_month)}' if t and (t.pass_year or t.pass_month) else '', 6, align=TA_CENTER) if t else '',
            _p(_val(t.organization) if t else '', 6),
        ])

    ct_tbl = Table(ct_all, colWidths=ct_c)
    ct_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING', (0, 0), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ('BACKGROUND', (0, 0), (-1, 0), GREY_BG),
    ]))
    elements.append(ct_tbl)
    elements.append(Spacer(1, 4))

    # ── DRIVING LICENSE ──
    license = None
    try:
        license = staff.driving_license
    except DrivingLicense.DoesNotExist:
        pass

    dl_data = [[
        _p('DRIVING LICENSE', 7, True),
        _p('Pass Year & Month', 6, True),
        _p(f'{_val(license.pass_year)} / {_val(license.pass_month)}' if license else '', 7),
        _p('Discretion of License', 6, True),
        _p(_val(license.discretion_of_license) if license else '', 7),
    ]]
    dl_c = [1.1 * inch, 1.1 * inch, 0.9 * inch, 1.2 * inch, 3.1 * inch]
    elements.append(_grid(dl_data, dl_c, [
        ('BACKGROUND', (0, 0), (0, 0), GREY_BG),
        ('BACKGROUND', (1, 0), (1, 0), GREY_BG),
        ('BACKGROUND', (3, 0), (3, 0), GREY_BG),
    ]))
    elements.append(Spacer(1, 4))

    # ── HOBBIES + MOTIVATION ──
    hm_data = [
        [_p('Hobbies, Special skills, etc.', 7, True), _p('Motivation, Self-promotion', 7, True)],
        [_p(_val(staff.hobbies), 6), _p(_val(staff.motivation), 6)],
    ]
    hm_c = [W / 2, W / 2]
    hm_tbl = Table(hm_data, colWidths=hm_c, rowHeights=[None, 0.7 * inch])
    hm_tbl.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), LN, BLACK),
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('VALIGN', (0, 1), (-1, 1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), PAD),
        ('TOPPADDING', (0, 0), (-1, -1), PAD),
        ('BOTTOMPADDING', (0, 0), (-1, -1), PAD),
        ('BACKGROUND', (0, 0), (-1, 0), GREY_BG),
    ]))
    elements.append(hm_tbl)

    # Build
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def generate_staff_bio_pdf(request, pk):
    """Generate Staff Bio Data PDF"""
    staff = get_object_or_404(StaffRegistration, pk=pk)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="staff_bio_{staff.staff_id}.pdf"'
    
    # Create the PDF object
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#ff9966'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    # Title
    elements.append(Paragraph("STAFF BIO DATA", title_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Staff Photo (if exists)
    if staff.candidate_photo:
        try:
            img = Image(staff.candidate_photo.path, width=2*inch, height=2.5*inch)
            elements.append(img)
            elements.append(Spacer(1, 0.2*inch))
        except:
            pass
    
    # Basic Information
    elements.append(Paragraph("BASIC INFORMATION", heading_style))
    basic_data = [
        ['Staff ID:', staff.staff_id, 'Gender:', staff.get_gender_display()],
        ['Full Name:', staff.full_name, 'Marital Status:', staff.marital_status],
        ['Phone No:', staff.phone_no, 'Email:', staff.email_id],
        ['Date of Birth:', str(staff.date_of_birth) if staff.date_of_birth else 'N/A', 'Blood Group:', staff.blood_group or 'N/A'],
    ]
    
    basic_table = Table(basic_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    basic_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(basic_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Address Information
    elements.append(Paragraph("ADDRESS INFORMATION", heading_style))
    address_data = [
        ['Permanent Address:', staff.permanent_address],
        ['Present Address:', staff.present_address],
    ]
    address_table = Table(address_data, colWidths=[2*inch, 5*inch])
    address_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(address_table)
    elements.append(Spacer(1, 0.3*inch))

   
    
    # Educational History
    if staff.education_history.exists():
        elements.append(Paragraph("EDUCATIONAL HISTORY", heading_style))
        edu_data = [['Level', 'School/University', 'Admission', 'Graduation', 'Years']]
        for edu in staff.education_history.all():
            edu_data.append([
                edu.get_pass_level_display(),
                edu.name_of_school,
                f"{edu.admission_month}/{edu.admission_year}",
                f"{edu.graduation_month}/{edu.graduation_year}",
                str(edu.enrolled_years) if edu.enrolled_years else 'N/A'
            ])
        
        edu_table = Table(edu_data, colWidths=[1.3*inch, 2.5*inch, 1*inch, 1*inch, 0.8*inch])
        edu_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        elements.append(edu_table)
        elements.append(Spacer(1, 0.3*inch))
    

    
    # Working Experience
    if staff.work_experience.exists():
        elements.append(Paragraph("WORKING EXPERIENCE", heading_style))
        work_data = [['Type of Work', 'Company', 'Join Date', 'Resign Date', 'Years']]
        for work in staff.work_experience.all():
            work_data.append([
                work.type_of_work,
                work.name_of_company,
                f"{work.join_month}/{work.join_year}",
                f"{work.resign_month}/{work.resign_year}",
                str(work.working_years) if work.working_years else 'N/A'
            ])
        
        work_table = Table(work_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch, 0.8*inch])
        work_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        elements.append(work_table)
    # Bank Information
    if staff.bank_info.exists():
        elements.append(Paragraph("BANK INFORMATION", heading_style))

    bank_data = [['Bank Name', 'Branch', 'Account No', 'Account Holder']]

    for bank in staff.bank_info.all():
        bank_data.append([
            bank.bank_name,
            bank.branch_name,
            bank.account_no,
            bank.account_holder_name
        ])

    bank_table = Table(bank_data, colWidths=[1.8*inch, 1.8*inch, 1.5*inch, 2*inch])
    bank_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))

    elements.append(bank_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", footer_style))
    elements.append(Paragraph("Copyright © Aqua Group, All Rights Reserved", footer_style))
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
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

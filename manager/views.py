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
        
        if form_valid and education_valid and work_valid and certificate_valid and training_valid and license_valid:
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
        bank_formset = BankFormSet(prefix='bank', queryset=BankInformation.objects.none())  # ✅ NEW

    
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
        bank_formset = BankFormSet(prefix='bank', queryset=BankInformation.objects.filter(staff=staff))


        
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

from tkinter import Image
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.template.loader import get_template
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

from dashboard.models import Student, EducationalHistory, WorkExperience, StudentDocument, Agent
from dashboard.forms import StudentForm

# -----------------------
# Utility functions
# -----------------------
def calculate_age(dob):
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def check_role(*allowed_roles):
    """Decorator to check multiple user roles"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            user_role = getattr(request.user, 'role', None)
            
            if user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            return redirect('no_permission')
        return wrapper
    return decorator

# -----------------------
# Student Registration
# -----------------------
@login_required(login_url='login')
@check_role('staff', 'manager')
def student_registration(request):
    # Get agent based on logged-in user or request
    agent = None
    
    # Try to get agent from user profile
    if hasattr(request.user, 'agent'):
        agent = request.user.agent
    # Or get from query parameter
    elif request.GET.get('agent_code'):
        try:
            agent = Agent.objects.get(agent_code=request.GET.get('agent_code'))
        except Agent.DoesNotExist:
            messages.error(request, 'Invalid agent code')
            return redirect('home')
    # For staff/manager, they can select agent
    elif request.user.role in ['staff', 'manager']:
        # If no agent specified, show list of agents or handle accordingly
        agents = Agent.objects.all()
        if not agent and agents.exists():
            # You might want to redirect to agent selection or use first agent
            # For now, we'll use the first available agent
            agent = agents.first()

    if request.method == 'POST':
        print("=" * 50)
        print("FORM SUBMISSION RECEIVED")
        print("=" * 50)
        print("POST data:", dict(request.POST))
        print("FILES:", dict(request.FILES))
        print("Agent:", agent)
        
        form = StudentForm(request.POST, request.FILES, agent=agent)
        
        if form.is_valid():
            print("FORM IS VALID!")
            print("Cleaned data:", form.cleaned_data)
            try:
                student = form.save()
                print(f"Student saved successfully: {student.student_id}")
                
                messages.success(request, f'Student {student.full_name} registered successfully with ID: {student.student_id}!')
                return redirect('dashboard:registration_success', student_id=student.id)
            except Exception as e:
                print(f"Error saving student: {str(e)}")
                messages.error(request, f'Error saving student: {str(e)}')
        else:
            print("=" * 50)
            print("FORM IS INVALID")
            print("=" * 50)
            print("Form errors:", form.errors)
            print("Form non-field errors:", form.non_field_errors())
            print("=" * 50)
            
            for field_name, errors in form.errors.items():
                print(f"Field: {field_name}, Errors: {errors}")
            
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(agent=agent)
        print("Form created for GET request")
    
    return render(request, 'dashboards/StudentRegistrationForm.html', {
        'form': form,
        'agent': agent
    })

# -----------------------
# Agent Student Registration (for agent portal)
# -----------------------
@login_required
def agent_student_registration(request):
    """Student registration specifically for agents"""
    # Ensure user is an agent
    if not hasattr(request.user, 'agent'):
        messages.error(request, 'Access denied. Agent account required.')
        return redirect('dashboard:agent_login')
    
    agent = request.user.agent
    
    if request.method == 'POST':
        print("Agent form submission")
        print("POST data:", dict(request.POST))
        
        form = StudentForm(request.POST, request.FILES, agent=agent)
        if form.is_valid():
            print("Agent form is valid")
            try:
                student = form.save()
                
                messages.success(request, f'Student {student.full_name} registered successfully with ID: {student.student_id}!')
                return redirect('dashboard:agent_dashboard')
            except Exception as e:
                print(f"Error saving student: {str(e)}")
                messages.error(request, f'Error saving student: {str(e)}')
        else:
            print("Agent form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(agent=agent)
    
    return render(request, 'dashboards/agent_student_registration.html', {
        'form': form,
        'agent': agent
    })

# -----------------------
# Student Management Views
# -----------------------
@login_required
def registration_success(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'dashboards/registration_success.html', {'student': student})

@login_required
def student_list(request):
    students = Student.objects.all().order_by('-created_at')
    return render(request, 'dashboards/student_list.html', {'students': students})

@login_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'dashboards/student_detail.html', {'student': student})

@login_required
def agent_student_detail(request, student_id):
    """Student detail view for agents (only shows their students)"""
    if not hasattr(request.user, 'agent'):
        messages.error(request, 'Access denied. Agent account required.')
        return redirect('dashboard:agent_login')
    
    agent = request.user.agent
    student = get_object_or_404(Student, id=student_id, agent=agent)
    return render(request, 'dashboards/agent_student_detail.html', {'student': student})

@login_required
def student_application_detail(request, student_id):
    student = get_object_or_404(
        Student.objects.prefetch_related('education_history', 'work_experience', 'documents'),
        id=student_id
    )
    documents_by_type = {
        'bio_data': student.documents.filter(document_type='bio_data'),
        'id_info': student.documents.filter(document_type='id_info'),
        'educational_doc': student.documents.filter(document_type='educational_doc'),
        'report': student.documents.filter(document_type='report'),
        'other': student.documents.filter(document_type='other'),
    }
    return render(request, 'dashboards/student_application_detail.html', {
        'student': student,
        'education_history': student.education_history.all(),
        'work_experience': student.work_experience.all(),
        'documents_by_type': documents_by_type,
        'all_documents': student.documents.all(),
    })

@login_required
def generate_student_pdf(request, student_id):
    """
    Generate PDF using ReportLab with all student data
    """
    try:
        # Get student with all related data
        student = get_object_or_404(
            Student.objects.select_related('agent').prefetch_related(
                'education_history', 'work_experience'
            ),
            id=student_id
        )
        
        # Create response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="student_{student.student_id}_application.pdf"'
        
        # Create PDF buffer
        buffer = BytesIO()
        
        # Create document with A4 size
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20
        )
        
        # Content container - MUST BE CREATED BEFORE ADDING ANY ELEMENTS
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=1,  # Center
            spaceAfter=5,
            textColor=colors.black
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            alignment=1,  # Center
            spaceAfter=10,
            textColor=colors.black
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=12,
            textColor=colors.black,
            spaceAfter=8,
            spaceBefore=10
        )
        
        # ============================================
        # HEADER SECTION
        # ============================================
        elements.append(Paragraph("AQUA EDUCATION AND TRAINING ACADEMY", title_style))
        elements.append(Paragraph("Lazimpat-02, Kathmandu, Nepal", styles['Normal']))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph("CO TO: ZEISSHO HOLDINGS / SUKIYA JAPAN / AEON GROUP / TORVU GROUP / TORVUSYUKAI JAPAN", 
                                 ParagraphStyle(name='Recipients', parent=styles['Normal'], fontSize=9)))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("ADMISSION FORM FOR SSW AND WORKING", header_style))
        elements.append(Spacer(1, 15))
        
        # ============================================
        # SECTION WITH PHOTO AND BASIC INFO (SIDE BY SIDE)
        # ============================================
        elements.append(Paragraph("1. BASIC INFORMATION WITH PHOTO", section_style))
        
        # Create a table that will have photo on right and info on left
        from reportlab.platypus import Image
        
        # Create the data for the table: 2 columns, multiple rows
        photo_info_data = []
        
        # Add student photo if available
        photo_cell = None
        if student.photo:
            try:
                # Try to open the photo file
                photo_path = student.photo.path
                if os.path.exists(photo_path):
                    photo_cell = Image(photo_path, width=1.5*inch, height=2*inch)
                else:
                    photo_cell = Paragraph("PHOTO<br/>(Not available)", styles['Normal'])
            except Exception as photo_error:
                photo_cell = Paragraph("PHOTO<br/>(Error loading)", styles['Normal'])
        else:
            photo_cell = Paragraph("PHOTO<br/>(Not uploaded)", styles['Normal'])
        
        # Create a 2-column layout table
        # Column 1: Information, Column 2: Photo
        
        # Row 1: Student ID and Photo (spanning multiple rows)
        basic_info_with_photo = [
            # Column 0: Information (6 rows)
            [
                ['Student ID NO:', student.student_id or 'N/A'],
                ['Full Name:', student.full_name or 'N/A'],
                ['Date of Birth:', str(student.date_of_birth) if student.date_of_birth else 'N/A'],
                ['Age:', str(student.age) if student.age else 'N/A'],
                ['Gender:', student.get_gender_display() if hasattr(student, 'get_gender_display') else 'N/A'],
                ['Marital Status:', student.get_marital_status_display() if hasattr(student, 'get_marital_status_display') else 'N/A']
            ],
            # Column 1: Photo (will span all 6 rows)
            photo_cell
        ]
        
        # We need to create a custom table structure
        # Since we can't easily mix Paragraphs and Images in simple Table, let's create a nested table
        
        # First, create the info table (6 rows, 2 columns)
        info_table_data = [
            ['Student ID NO:', student.student_id or 'N/A'],
            ['Full Name:', student.full_name or 'N/A'],
            ['Date of Birth:', str(student.date_of_birth) if student.date_of_birth else 'N/A'],
            ['Age:', str(student.age) if student.age else 'N/A'],
            ['Gender:', student.get_gender_display() if hasattr(student, 'get_gender_display') else 'N/A'],
            ['Marital Status:', student.get_marital_status_display() if hasattr(student, 'get_marital_status_display') else 'N/A']
        ]
        
        info_table = Table(info_table_data, colWidths=[1.5*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        # Now create a main table with 2 columns: info_table and photo
        main_layout_data = [[info_table, photo_cell]]
        main_layout_table = Table(main_layout_data, colWidths=[4.5*inch, 1.5*inch])
        main_layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        
        elements.append(main_layout_table)
        elements.append(Spacer(1, 10))
        
        # ============================================
        # SECTION 2: CONTACT INFORMATION
        # ============================================
        elements.append(Paragraph("2. CONTACT INFORMATION", section_style))
        
        contact_data = [
            ['Email:', student.email or 'N/A'],
            ['Phone:', student.phone or 'N/A'],
        ]
        
        contact_table = Table(contact_data, colWidths=[1.5*inch, 4*inch])
        contact_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(contact_table)
        elements.append(Spacer(1, 10))
        
        # ============================================
        # SECTION 3: ADDRESS INFORMATION
        # ============================================
        elements.append(Paragraph("3. ADDRESS INFORMATION", section_style))
        
        address_data = [
            ['Permanent Address:', student.permanent_address or 'N/A'],
            ['Present Address:', student.present_address or 'N/A'],
        ]
        
        address_table = Table(address_data, colWidths=[1.5*inch, 4*inch])
        address_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(address_table)
        elements.append(Spacer(1, 10))
        
        # ============================================
        # SECTION 4: PASSPORT INFORMATION
        # ============================================
        elements.append(Paragraph("4. PASSPORT INFORMATION", section_style))
        
        passport_data = [
            ['Passport No.:', student.passport_no or 'N/A'],
            ['Date of Issue:', str(student.passport_issue_date) if student.passport_issue_date else 'N/A'],
            ['Date of Expiry:', str(student.passport_expiry_date) if student.passport_expiry_date else 'N/A'],
        ]
        
        passport_table = Table(passport_data, colWidths=[1.5*inch, 4*inch])
        passport_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(passport_table)
        elements.append(Spacer(1, 10))
        
        # ============================================
        # SECTION 5: PHYSICAL INFORMATION
        # ============================================
        elements.append(Paragraph("5. PHYSICAL INFORMATION", section_style))
        
        physical_data = [
            ['Height:', f"{student.height or 'N/A'} cm"],
            ['Weight:', f"{student.weight or 'N/A'} kg"],
            ['Blood Group:', student.blood_group or 'N/A'],
            ['Eye Lens (Right):', getattr(student, 'eye_lens_right', 'N/A')],
            ['Eye Lens (Left):', getattr(student, 'eye_lens_left', 'N/A')],
        ]
        
        physical_table = Table(physical_data, colWidths=[1.5*inch, 4*inch])
        physical_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(physical_table)
        elements.append(Spacer(1, 10))
        
        # ============================================
        # SECTION 6: VISA INFORMATION
        # ============================================
        elements.append(Paragraph("6. VISA INFORMATION", section_style))
        
        visa_data = [
            ['Past Visa Apply Record:', getattr(student, 'visa_apply_record', 'N/A')],
            ['Visa Result (if applied):', getattr(student, 'visa_result', 'N/A')],
        ]
        
        visa_table = Table(visa_data, colWidths=[1.5*inch, 4*inch])
        visa_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(visa_table)
        elements.append(Spacer(1, 10))
        
        # ============================================
        # SECTION 7: FAMILY INFORMATION
        # ============================================
        elements.append(Paragraph("7. FAMILY INFORMATION", section_style))
        
        family_data = [
            ['Spouse Name:', student.spouse_name or 'N/A'],
            ['Spouse Contact:', student.spouse_contact or 'N/A'],
        ]
        
        family_table = Table(family_data, colWidths=[1.5*inch, 4*inch])
        family_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(family_table)
        elements.append(Spacer(1, 15))
        
        # ============================================
        # SECTION 8: EDUCATIONAL HISTORY (TABLE FORMAT)
        # ============================================
        elements.append(Paragraph("8. EDUCATIONAL HISTORY", header_style))
        
        # Create education table
        edu_headers = [['Level', 'School Name', 'Admission', 'Graduation', 'Years']]
        edu_data = edu_headers.copy()
        
        if hasattr(student, 'education_history') and student.education_history.exists():
            for edu in student.education_history.all():
                # Safely get education data
                admission_info = ''
                if edu.admission_year:
                    admission_info = str(edu.admission_year)
                    if edu.admission_month:
                        admission_info += f" {edu.admission_month}"
                
                graduation_info = ''
                if edu.graduation_year:
                    graduation_info = str(edu.graduation_year)
                    if edu.graduation_month:
                        graduation_info += f" {edu.graduation_month}"
                
                edu_data.append([
                    edu.pass_level or 'N/A',
                    edu.school_name or 'N/A',
                    admission_info or 'N/A',
                    graduation_info or 'N/A',
                    str(edu.enrolled_years) if edu.enrolled_years else 'N/A'
                ])
        else:
            edu_data.append(['No education records found', '', '', '', ''])
        
        # Create education table
        edu_table = Table(edu_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1*inch, 0.8*inch])
        edu_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(edu_table)
        elements.append(Spacer(1, 15))
        
        # ============================================
        # SECTION 9: WORK EXPERIENCE (TABLE FORMAT)
        # ============================================
        elements.append(Paragraph("9. WORK EXPERIENCE", header_style))
        
        # Create work table
        work_headers = [['Type of Work', 'Company Name', 'Join Date', 'Resign Date', 'Years']]
        work_data = work_headers.copy()
        
        if hasattr(student, 'work_experience') and student.work_experience.exists():
            for work in student.work_experience.all():
                work_data.append([
                    work.work_type or 'N/A',
                    work.company_name or 'N/A',
                    str(work.join_date) if work.join_date else 'N/A',
                    str(work.resign_date) if work.resign_date else 'N/A',
                    str(work.working_years) if work.working_years else 'N/A'
                ])
        else:
            work_data.append(['No work experience found', '', '', '', ''])
        
        # Create work table
        work_table = Table(work_data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch, 0.8*inch])
        work_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(work_table)
        elements.append(Spacer(1, 15))
        
        # ============================================
        # SECTION 10: ADDITIONAL INFORMATION
        # ============================================
        elements.append(Paragraph("10. ADDITIONAL INFORMATION", section_style))
        
        # Helper function to safely get agent name
        def get_agent_name(agent):
            if not agent:
                return 'N/A'
            # Try different possible field names
            for field_name in ['agent_name', 'name', 'full_name', 'agent_code', 'code']:
                if hasattr(agent, field_name):
                    value = getattr(agent, field_name)
                    if value:
                        return str(value)
            return 'Agent #' + str(agent.id) if hasattr(agent, 'id') else 'N/A'
        
        # Safely get all additional fields
        additional_data = [
            ['A-CODE:', getattr(student, 'a_code', 'ABB-0011')],
            ['TB Status:', getattr(student, 'tb_status', 'N/A')],
            ['Medical Report:', getattr(student, 'medical_report', 'N/A')],
            ['Status:', getattr(student, 'status', 'N/A')],
            ['Agent:', get_agent_name(student.agent)],
        ]
        
        # Add created_at if it exists
        if hasattr(student, 'created_at') and student.created_at:
            additional_data.append(['Registration Date:', student.created_at.strftime('%Y-%m-%d')])
        
        additional_table = Table(additional_data, colWidths=[1.5*inch, 4*inch])
        additional_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(additional_table)
        elements.append(Spacer(1, 15))
        
        # ============================================
        # SECTION 11: AGREEMENT
        # ============================================
        elements.append(Paragraph("AGREEMENT", header_style))
        
        agreement_text = """
        I hereby agree to study the Japanese language at the Aqua Education And Training Academy while strictly complying with all rules and regulations. 
        After going to Japan, I promise to follow all Japanese rules and the immigration law. 
        In the event that I fail to company rules and law of Japan, I'm agree to accept the all penalties in according with Japanese rules and Immigration Law.
        """
        
        elements.append(Paragraph(agreement_text, styles['Normal']))
        elements.append(Spacer(1, 15))
        
        # ============================================
        # SECTION 12: REQUIRED DOCUMENTS
        # ============================================
        elements.append(Paragraph("REQUIRED DOCUMENTS FOR ADMISSION", section_style))
        
        documents_data = [
            ['1. PASSPORT', 'Color Copy'],
            ['2. GRADUATION / TRANSCRIPT', 'Color Copy'],
            ['3. CITIZENSHIP / DRIVING LICENSE', 'Color Copy'],
            ['4. MEDICAL REPORT', 'Color Copy'],
        ]
        
        documents_table = Table(documents_data, colWidths=[3*inch, 2*inch])
        documents_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        elements.append(documents_table)
        elements.append(Spacer(1, 10))
        
        # ============================================
        # FOOTER
        # ============================================
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "Copyright © Aqua Group, All Rights Reserved",
            ParagraphStyle(name='Footer', parent=styles['Normal'], fontSize=8, alignment=1, textColor=colors.grey)
        ))
        
        # Add page number
        elements.append(Paragraph(
            f"Page 1 of 1 • Generated on: {date.today().strftime('%Y-%m-%d %H:%M')}",
            ParagraphStyle(name='PageInfo', parent=styles['Normal'], fontSize=7, alignment=2, textColor=colors.grey)
        ))
        
        # ============================================
        # BUILD PDF
        # ============================================
        try:
            doc.build(elements)
            pdf = buffer.getvalue()
            buffer.close()
            
            response.write(pdf)
            return response
            
        except Exception as build_error:
            # Fallback to simple text if table building fails
            return generate_simple_pdf_fallback(student)
            
    except Exception as e:
        import traceback
        error_msg = f"Error generating PDF: {str(e)}\n\n{traceback.format_exc()}"
        return HttpResponse(error_msg, status=500)
    return response
# -----------------------
# Update Student Status
# -----------------------
@login_required
def update_student_status(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        review_notes = request.POST.get('review_notes', '')
        if action in ['approve', 'decline']:
            student.status = 'approved' if action == 'approve' else 'declined'
            student.reviewed_by = request.user
            student.reviewed_at = timezone.now()
            student.review_notes = review_notes
            student.save()
            messages.success(request, f'Student {student.full_name} has been {action}d.')
        return redirect('dashboard:recruitment_client_dashboard')
    

# -----------------------
# Approve / Decline Student
# -----------------------
@login_required
def approve_student_page(request, student_id):
    student = get_object_or_404(Student.objects.prefetch_related('education_history', 'work_experience'), id=student_id)
    return render(request, 'dashboards/approval_page.html', {
        'student': student,
        'action': 'approve',
        'page_title': 'Approve Student Application',
        'button_text': 'Confirm Approval',
        'button_class': 'btn-success'
    })

@login_required
def decline_student_page(request, student_id):
    student = get_object_or_404(Student.objects.prefetch_related('education_history', 'work_experience'), id=student_id)
    return render(request, 'dashboards/approval_page.html', {
        'student': student,
        'action': 'decline',
        'page_title': 'Decline Student Application',
        'button_text': 'Confirm Decline',
        'button_class': 'btn-danger'
    })

@login_required
def approve_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        student.status = 'approved'
        student.reviewed_by = request.user
        student.reviewed_at = timezone.now()
        student.review_notes = request.POST.get('review_notes', '')
        student.save()
        messages.success(request, f'✅ Application for {student.full_name} has been approved!')
        return redirect('dashboard:recruitment_client_dashboard')
    return redirect('dashboard:approve_student_page', student_id=student_id)

@login_required
def decline_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        student.status = 'declined'
        student.reviewed_by = request.user
        student.reviewed_at = timezone.now()
        student.review_notes = request.POST.get('review_notes', '')
        student.save()
        messages.success(request, f'❌ Application for {student.full_name} has been declined.')
        return redirect('dashboard:recruitment_client_dashboard')
    return redirect('dashboard:decline_student_page', student_id=student_id)

# Use Django ORM Counts in Your Template
def all_candidates(request):
    students = Student.objects.all()

    total_count = students.count()
    pending_count = students.filter(status='pending').count()
    approved_count = students.filter(status='approved').count()
    declined_count = students.filter(status='declined').count()

    context = {
        "students": students,
        "total_count": total_count,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "declined_count": declined_count,
    }
    return render(request, "your_template.html", context)

# -----------------------
# Simple Pages
# -----------------------
@login_required
def biodata(request):
    return render(request, 'dashboards/biodata.html')

# -----------------------
# Debug View (for testing)
# -----------------------
def test_form_submission(request):
    """Debug view to test form submission"""
    if request.method == 'POST':
        response_text = []
        response_text.append("=" * 50)
        response_text.append("TEST FORM SUBMISSION")
        response_text.append("=" * 50)
        response_text.append(f"POST data: {dict(request.POST)}")
        response_text.append(f"FILES: {dict(request.FILES)}")
        
        # Test with minimal data
        agent = Agent.objects.first()
        if agent:
            response_text.append(f"Using agent: {agent.agent_code}")
            form = StudentForm(request.POST, request.FILES, agent=agent)
            
            if form.is_valid():
                response_text.append("✓ Form is VALID!")
                try:
                    student = form.save()
                    response_text.append(f"✓ Student saved: {student.student_id}")
                except Exception as e:
                    response_text.append(f"✗ Error saving: {str(e)}")
            else:
                response_text.append("✗ Form is INVALID")
                response_text.append(f"Errors: {form.errors}")
        else:
            response_text.append("✗ No agent found!")
        
        response_text.append("=" * 50)
        return HttpResponse("<br>".join(response_text))
    
    # GET request - show test form
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>Test Form</title></head>
    <body>
        <h1>Test Form Submission</h1>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="csrfmiddlewaretoken" value="TEST_TOKEN">
            <p>Full Name: <input type="text" name="full_name" value="Test Student"></p>
            <p>Email: <input type="email" name="email" value="test@example.com"></p>
            <p>Phone: <input type="text" name="phone" value="1234567890"></p>
            <p>Gender: 
                <select name="gender">
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                </select>
            </p>
            <p>Date of Birth: <input type="date" name="date_of_birth" value="2000-01-01"></p>
            <p>Permanent Address: <textarea name="permanent_address">Test Address</textarea></p>
            <p>Marital Status: 
                <select name="marital_status">
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                </select>
            </p>
            <p>TB Status: 
                <input type="radio" name="tb_status" value="positive" id="tbPositive">
                <label for="tbPositive">Positive</label>
                <input type="radio" name="tb_status" value="negative" id="tbNegative" checked>
                <label for="tbNegative">Negative</label>
            </p>
            <button type="submit">Test Submit</button>
        </form>
    </body>
    </html>
    """
    return HttpResponse(html)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from django.template.loader import render_to_string
from datetime import date
from weasyprint import HTML
from django.db import models

from dashboard.models import Student, EducationalHistory, WorkExperience, StudentDocument, Agent
from dashboard.forms import StudentForm

# -----------------------
# Utility Functions
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
            messages.error(request, "You do not have permission to access this page.")
            return redirect('dashboard:home')
        return wrapper
    return decorator

def save_student_form(form, request):
    """Helper to save student form and handle messages"""
    try:
        student = form.save()
        messages.success(request, f'Student {student.full_name} registered successfully with ID: {student.student_id}!')
        return student
    except Exception as e:
        messages.error(request, f'Error saving student: {str(e)}')
        return None

# -----------------------
# Student Registration
# -----------------------
@login_required(login_url='login')
@check_role('staff', 'manager')
def student_registration(request):
    # Determine agent
    agent = getattr(request.user, 'agent', None)
    if not agent and request.GET.get('agent_code'):
        agent = Agent.objects.filter(agent_code=request.GET.get('agent_code')).first()
        if not agent:
            messages.error(request, 'Invalid agent code')
            return redirect('home')

    if not agent and request.user.role in ['staff', 'manager']:
        agent = Agent.objects.first()  # fallback to first agent if none selected

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, agent=agent)
        if form.is_valid():
            student = save_student_form(form, request)
            if student:
                return redirect('dashboard:registration_success', student_id=student.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(agent=agent)

    return render(request, 'dashboards/StudentRegistrationForm.html', {'form': form, 'agent': agent})

# -----------------------
# Agent Student Registration
# -----------------------
@login_required
def agent_student_registration(request):
    agent = getattr(request.user, 'agent', None)
    if not agent:
        messages.error(request, 'Access denied. Agent account required.')
        return redirect('dashboard:agent_login')

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, agent=agent)
        if form.is_valid():
            student = save_student_form(form, request)
            if student:
                return redirect('dashboard:agent_dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(agent=agent)

    return render(request, 'dashboards/agent_student_registration.html', {'form': form, 'agent': agent})

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

    # Optimize database queries by using aggregation
    status_counts = students.aggregate(
        total_count=models.Count('id'),
        pending_count=models.Sum(models.Case(models.When(status='pending', then=1), default=0, output_field=models.IntegerField())),
        approved_count=models.Sum(models.Case(models.When(status='approved', then=1), default=0, output_field=models.IntegerField())),
        declined_count=models.Sum(models.Case(models.When(status='declined', then=1), default=0, output_field=models.IntegerField())),
    )

    context = {
        'students': students,
        'total_count': status_counts['total_count'] or 0,
        'pending_count': status_counts['pending_count'] or 0,
        'approved_count': status_counts['approved_count'] or 0,
        'declined_count': status_counts['declined_count'] or 0,
    }
    return render(request, 'dashboards/student_list.html', context)

@login_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'dashboards/student_detail.html', {'student': student})

@login_required
def agent_student_detail(request, student_id):
    agent = getattr(request.user, 'agent', None)
    if not agent:
        messages.error(request, 'Access denied. Agent account required.')
        return redirect('dashboard:agent_login')

    student = get_object_or_404(Student, id=student_id, agent=agent)
    return render(request, 'dashboards/agent_student_detail.html', {'student': student})

@login_required
def student_application_detail(request, student_id):
    student = get_object_or_404(
        Student.objects.prefetch_related('education_history', 'work_experience', 'documents'),
        id=student_id
    )
    known_types = ['bio_data', 'id_info', 'educational_doc', 'report']
    documents_by_type = {
        t: student.documents.filter(document_type=t)
        for t in known_types
    }
    documents_by_type['other'] = student.documents.exclude(document_type__in=known_types)
    return render(request, 'dashboards/student_application_detail.html', {
        'student': student,
        'education_history': student.education_history.all(),
        'work_experience': student.work_experience.all(),
        'documents_by_type': documents_by_type,
        'all_documents': student.documents.all(),
    })



import os
import base64
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from weasyprint import HTML
from django.conf import settings

@login_required
def generate_student_pdf(request, student_id):
    """Generate PDF for student - accessible by logged-in users"""
    return _generate_student_pdf_internal(request, student_id)

def generate_student_pdf_portal(request, student_id):
    """Generate PDF for student - accessible by portal users via session"""
    # Check if user is coming from portal (has portal_agent_id in session)
    portal_agent_id = request.session.get('portal_agent_id')
    if not portal_agent_id:
        # If not portal user, redirect to login
        from django.contrib.auth.decorators import login_required
        return login_required(lambda r, sid: _generate_student_pdf_internal(r, sid))(request, student_id)
    
    # Portal user is valid, allow PDF generation
    return _generate_student_pdf_internal(request, student_id)

def _generate_student_pdf_internal(request, student_id):
    """Internal function to generate PDF"""
    try:
        student = get_object_or_404(
            Student.objects.select_related('agent').prefetch_related(
                'education_history', 'work_experience'
            ),
            id=student_id
        )

        # Photo Processing
        photo_html = '<div class="photo-box-inner"><div class="photo-box-content">PHOTO</div></div>'
        if student.photo:
            try:
                photo_path = student.photo.path
                if os.path.exists(photo_path):
                    with open(photo_path, "rb") as f:
                        photo_data = base64.b64encode(f.read()).decode()
                    ext = os.path.splitext(photo_path)[1].lower()
                    mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                    photo_html = f'<div class="photo-box-inner"><img src="data:{mime_type};base64,{photo_data}"></div>'
            except Exception: pass

        # Prepare Loops for Tables
        edu_defaults = ["Primary School", "Junior H. School", "Higher S. School", "College / University", "Graduate University", "Graduate University", "Other School"]
        edu_list = list(student.education_history.all())
        education_rows = ""
        for i in range(7):
            e = edu_list[i] if i < len(edu_list) else None
            education_rows += f"""
            <tr style="height:28px;">
                <td style="padding-left:8px; font-size: 7.5pt;">{e.pass_level if e else edu_defaults[i]}</td>
                <td style="font-size: 7.5pt;">{e.school_name if e else ''}</td>
                <td class="center" style="font-size: 7.5pt;">{e.admission_year if e else ''}</td>
                <td class="center" style="font-size: 7.5pt;">{e.admission_month if e else ''}</td>
                <td class="center" style="font-size: 7.5pt;">{e.graduation_year if e else ''}</td>
                <td class="center" style="font-size: 7.5pt;">{e.graduation_month if e else ''}</td>
                <td class="center" style="position:relative; font-size: 7.5pt;">{e.enrolled_years if e and e.enrolled_years else ''} <span style="position:absolute; right:3px; font-size: 6.5pt;">Years</span></td>
            </tr>"""

        work_list = list(student.work_experience.all())[:3]
        work_rows = ""
        for i in range(3):
            w = work_list[i] if i < len(work_list) else None
            work_rows += f"""
            <tr style="height:22px;">
                <td style="padding-left:8px; font-size: 7.5pt;">{w.work_type if w else ''}</td>
                <td style="font-size: 7.5pt;">{w.company_name if w else ''}</td>
                <td class="center" style="font-size: 7.5pt;">{w.join_date if w else ''} ~ {w.resign_date if w else ''}</td>
                <td class="center" style="position:relative; font-size: 7.5pt;">{w.working_years if w and w.working_years else ''} <span style="position:absolute; right:3px; font-size: 6.5pt;">Years</span></td>
            </tr>"""

        # Context Data
        a_code = student.agent.agent_code if student.agent else ""
        dob = student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else ''
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @page {{ size: A4; margin: 0.5cm 1.25cm; }}
        body {{ font-family: 'Helvetica', 'Arial', sans-serif; font-size: 8pt; line-height: 1.1; color: #000; margin: 0; padding: 0; }}
        .header {{ text-align: center; margin-bottom: 4px; background-color: #E8E8E8; padding: 8px 0; }}
        .header h1 {{ font-size: 15pt; margin: 0; font-weight: bold; letter-spacing: 1px; }}
        .header p {{ font-size: 9.5pt; margin: 2px 0; font-weight: bold; }}
        .cc-to {{ text-align: left; font-size: 6pt; font-weight: bold; margin: 4px 0 2px 10px; }}
        
        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: -1px; }}
        td, th {{ border: 1px solid #000; padding: 3px 5px; vertical-align: middle; overflow: hidden; }}
        
        .bg-beige {{ background-color: #C7BFA3; font-weight: bold; text-align: center; }}
        .center {{ text-align: center; }}
        .bold {{ font-weight: bold; }}
        .lbl-sm {{ font-size: 7pt; }}
        
        .photo-box {{ width: 85px; height: 110px; text-align: center; padding: 1px; vertical-align: middle; background: #fff; border: 1px solid #000; box-sizing: border-box; }}
        .photo-box-inner {{ width: 100%; height: 100%; background: #fff; border: 1px solid #000; box-sizing: border-box; overflow: hidden; }}
        .photo-box-content {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: #fff; color: #999; font-size: 9pt; }}
        .photo-box img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
        .section-title {{ font-size: 10pt; padding: 3px; border: 1px solid #000; border-bottom: none; }}
        
        .vertical-text {{ 
            writing-mode: vertical-rl; 
            transform: rotate(180deg); 
            text-align: center; 
            font-size: 7.5pt; 
            font-weight: bold;
        }}
        
        .sign-box {{ 
            width: 150px; 
            float: right; 
            border: 1px solid #000; 
            border-collapse: collapse;
            margin-right: 10px;
        }}
        .sign-box td {{ 
            border: 1px solid #000; 
            padding: 4px; 
            vertical-align: middle;
        }}
        .sign-box .label {{ 
            background-color: #C7BFA3; 
            font-weight: bold; 
            font-size: 8.5pt; 
            text-align: center; 
            width: 42px; 
        }}
        
        .clearfix::after {{ content: ""; clear: both; display: table; }}
    </style>
</head>
<body>

    <div class="header">
        <h1>AQUA EDUCATION AND TRAINING ACADEMY</h1>
        <p>Lazimpat-02, Kathmandu, Nepal</p>
    </div>
    <div class="cc-to">CC TO: <br> ZENSHO HOLDINGS / SUKIYA JAPAN / AEON GROUP / TOKYU GROUP / TOKYUSYUKAI JAPAN</div>

    <div class="section-title bg-beige">ADMISSION FORM FOR SSW AND WORKING</div>

    <table>
        <tr>
            <td width="15%" class="center">Student ID NO</td>
            <td width="25%">{student.student_id or ''}</td>
            <td width="10%" class="center">A-CODE</td>
            <td width="15%">{a_code}</td>
            <td width="10%" class="center">Gender</td>
            <td width="10%">{student.get_gender_display() if student.gender else ''}</td>
            <td rowspan="4" class="photo-box">{photo_html}</td>
        </tr>
        <tr>
            <td class="center">Full Name</td>
            <td colspan="3" style="font-size: 10.5pt; font-weight: bold;">{student.full_name or ''}</td>
            <td class="center">Date of Birth</td>
            <td class="center">{dob}</td>
        </tr>
        <tr>
            <td rowspan="2" class="center" style="padding:0; font-size: 7.5pt; font-weight: bold;">
                Full<br>Address
            </td>
            <td width="8%" class="center" style="font-size: 7pt;">Permanent</td>
            <td colspan="2" class="lbl-sm" style="height:26px;">{student.permanent_address or ''}</td>
            <td class="center" style="font-size: 7.5pt;">Age</td>
            <td class="center">{student.age or ''}</td>
        </tr>
        <tr>
            <td class="center" style="font-size: 7pt;">Present</td>
            <td colspan="2" class="lbl-sm" style="height:26px;">{student.present_address or ''}</td>
            <td class="center" style="font-size: 7.5pt;">Marital Status</td>
            <td class="center">{student.get_marital_status_display() if student.marital_status else ''}</td>
        </tr>
    </table>

    <table>
        <tr>
            <td width="15%" class="center" style="font-size: 7.5pt;">Passport No.</td>
            <td width="30%" style="font-size: 7.5pt;">{student.passport_no or ''}</td>
            <td width="12%" class="center" style="font-size: 7.5pt;">Date of Issue</td>
            <td width="16%" style="font-size: 7.5pt;">{student.passport_issue_date or ''}</td>
            <td width="14%" class="center" style="font-size: 7.5pt;">Date of Expired</td>
            <td width="13%" class="center" style="font-size: 7.5pt;">{student.passport_expiry_date or ''}</td>
        </tr>
    </table>

    <table>
        <tr class="center lbl-sm" style="height:16px;">
            <td rowspan="3" width="15%" style="font-size: 7pt;">Personal Information</td>
            <td width="10%" style="font-size: 7pt;">Height</td>
            <td width="10%" style="font-size: 7pt;">Weight</td>
            <td colspan="2" width="20%" style="font-size: 7pt;">Eye Lense</td>
            <td width="10%" style="font-size: 7pt;">Blood Group</td>
            <td width="10%" style="font-size: 7pt;">Past Visa Apply Record</td>
            <td style="font-size: 7pt;">Visa Apply if Yes (Apply No. & Result)</td>
        </tr>
        <tr class="center lbl-sm" style="height:14px;">
            <td rowspan="2" style="font-size: 7.5pt;">{student.height or ''}</td>
            <td rowspan="2" style="font-size: 7.5pt;">{student.weight or ''}</td>
            <td width="10%" style="font-size: 7pt;">Right</td><td width="10%" style="font-size: 7pt;">Left</td>
            <td rowspan="2" style="font-size: 7.5pt;">{student.blood_group or ''}</td>
            <td rowspan="2" style="font-size: 7.5pt;">{student.get_visa_apply_record_display() if student.visa_apply_record else ''}</td>
            <td rowspan="2" style="font-size: 7.5pt;">{student.visa_details or ''}</td>
        </tr>
        <tr class="center">
            <td style="font-size: 7.5pt;">{student.eye_lens_right or ''}</td><td style="font-size: 7.5pt;">{student.eye_lens_left or ''}</td>
        </tr>
    </table>

    <table>
        <tr>
            <td width="15%" class="center" style="font-size: 7.5pt;">Email ID</td>
            <td width="50%" style="font-size: 7.5pt;">{student.email or ''}</td>
            <td width="15%" class="center" style="font-size: 7.5pt;">Phone No.</td>
            <td style="font-size: 7.5pt;">{student.phone or ''}</td>
        </tr>
        <tr>
            <td class="center" style="font-size: 7.5pt;">Family Records</td>
            <td colspan="3" style="height:22px; font-size: 7.5pt;">{student.family_records or ''}</td>
        </tr>
        <tr>
            <td class="center" style="font-size: 7.5pt;">Spouse Name</td>
            <td style="font-size: 7.5pt;">{student.spouse_name or ''}</td>
            <td class="center" style="font-size: 7.5pt;">Contact No.</td>
            <td style="font-size: 7.5pt;">{student.spouse_contact or ''}</td>
        </tr>
    </table>

    <div class="bg-beige section-title" style="border-bottom: 1px solid #000; margin-top: 0; font-size: 9pt;">EDUCATIONAL HISTORY</div>
    <table>
        <tr class="center" style="font-size: 7.5pt; height: 22px;">
            <th width="18%" rowspan="2" style="font-size: 7.5pt;">Pass Level</th>
            <th width="40%" rowspan="2" style="font-size: 7.5pt;">Name of School</th>
            <th colspan="4" width="28%" style="font-size: 7.5pt;">Admission & Graduation</th>
            <th width="14%" rowspan="2" style="font-size: 7.5pt;">Enrolled Years</th>
        </tr>
        <tr class="center" style="font-size: 7pt; height: 14px;">
            <td style="font-size: 7pt;">Year</td><td style="font-size: 7pt;">Month</td><td style="font-size: 7pt;">Year</td><td style="font-size: 7pt;">Month</td>
        </tr>
        {education_rows}
    </table>

    <div class="bg-beige section-title" style="border-bottom: 1px solid #000; margin-top: 0; font-size: 9pt;">WORKING EXPERIENCE</div>
    <table>
        <tr class="center" style="font-size: 7.5pt; height: 22px;">
            <th width="18%" style="font-size: 7.5pt;">Type of Work</th>
            <th width="45%" style="font-size: 7.5pt;">Name of Working Company</th>
            <th width="23%" style="font-size: 7.5pt;">Date of Join & Resign</th>
            <th width="14%" style="font-size: 7.5pt;">Working Years</th>
        </tr>
        {work_rows}
    </table>

    <table>
        <tr>
            <td class="bg-beige" width="50%" style="font-size: 7.5pt; text-align: center;">LANGUAGE AND SKILLS PASSED CERTIFICATE</td>
            <td class="bg-beige" style="font-size: 7.5pt; text-align: center;">LANGUAGE & SKILLS TRAINING STATUS</td>
        </tr>
        <tr>
            <td style="padding:0;">
                <table style="border:none;">
                    <tr class="center" style="height:18px;">
                        <td width="20%" style="border:none; border-right: 1px solid #000; border-bottom: 1px solid #000; font-size: 6.5pt;">Pass Year & Month</td>
                        <td style="border:none; border-bottom: 1px solid #000; font-size: 6.5pt;">Name of Pass Exam</td>
                    </tr>
                    <tr style="height:24px;" class="center">
                        <td style="border:none; border-right: 1px solid #000; font-size: 7.5pt;">{student.certificate_pass_year or ''}</td>
                        <td style="border:none; font-size: 7.5pt;">{student.certificate_name or ''}</td>
                    </tr>
                    <tr style="height:24px;" class="center">
                        <td style="border:none; border-right: 1px solid #000; border-top: 1px solid #000; font-size: 7.5pt;"></td>
                        <td style="border:none; border-top: 1px solid #000; font-size: 7.5pt;"></td>
                    </tr>
                </table>
            </td>
            <td style="padding:0;">
                <table style="border:none;">
                    <tr class="center" style="height:18px;">
                        <td width="22%" style="border:none; border-right: 1px solid #000; border-bottom: 1px solid #000; font-size: 6.5pt;">Join Year and Month</td>
                        <td style="border:none; border-bottom: 1px solid #000; font-size: 6.5pt;">Organization</td>
                    </tr>
                    <tr style="height:24px;" class="center">
                        <td style="border:none; border-right: 1px solid #000; font-size: 7.5pt;">{student.language_join_year or ''}</td>
                        <td style="border:none; font-size: 7.5pt;">{student.organization or ''}</td>
                    </tr>
                    <tr style="height:24px;" class="center">
                        <td style="border:none; border-right: 1px solid #000; border-top: 1px solid #000; font-size: 7.5pt;"></td>
                        <td style="border:none; border-top: 1px solid #000; font-size: 7.5pt;"></td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>

    <table style="margin-top:0;">
        <tr>
            <td rowspan="3" width="25%" class="bg-beige center" style="font-size: 9pt;">DRIVING LICENSE</td>
            <td width="37.5%" class="center" style="font-size: 6.5pt;">Pass Year & Month</td>
            <td width="37.5%" class="center" style="font-size: 6.5pt;">Type of License</td>
        </tr>
        <tr style="height:24px;">
            <td class="center" style="font-size: 7.5pt;">{student.license_pass_year or ''}</td>
            <td class="center" style="font-size: 7.5pt;">{student.driving_license or ''}</td>
        </tr>
        <tr style="height:24px;">
            <td class="center" style="font-size: 7.5pt;">{student.license_pass_year_2 or ''}</td>
            <td class="center" style="font-size: 7.5pt;">{student.license_type_2 or ''}</td>
        </tr>
    </table>

    <table>
        <tr style="height: 18px;">
            <td width="50%" style="font-size: 7.5pt;"><b>Hobbies, Special skills, etc.</b></td>
            <td style="font-size: 7.5pt;"><b>Motivation, Self-promotion</b></td>
        </tr>
        <tr style="height: 60px; vertical-align: top;">
            <td style="font-size: 7.5pt;">{student.hobbies or ''}</td>
            <td style="font-size: 7.5pt;">{student.motivation or ''}</td>
        </tr>
    </table>

    <div class="clearfix" style="margin-top: 8px;">
        <div style="width: 70%; float: left; font-size: 7pt; text-align: justify; line-height: 1.15;">
            I hereby agree to study the Japanese language at the Aqua Education And Training Academy while strictly complying with all rules and regulations. After going to Japan, I promise to follow all Japanese rules and the immigration law. In the event that I fail to comply with company rules and law of Japan, I'm agree to accept all penalties in accordance with Japanese rules and Immigration Law.
        </div>
        <div style="width: 28%; float: right;">
            <div style="font-size: 7.5pt; margin-bottom: 4px; text-align: right; padding-right: 18px;">Date : ________________</div>
            <table class="sign-box">
                <tr style="height: 32px;">
                    <td class="label">SIGN</td>
                    <td></td>
                </tr>
            </table>
        </div>
    </div>

</body>
</html>
"""
        pdf = HTML(string=html_content).write_pdf()
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="Admission_Form_{student.student_id}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)

@login_required
def generate_admission_fee_pdf(request, student_id):
    """Generate Admission Fee Invoice PDF - accessible by logged-in users"""
    return _generate_admission_fee_pdf_internal(request, student_id)

def generate_admission_fee_pdf_portal(request, student_id):
    """Generate Admission Fee Invoice PDF - accessible by portal users via session"""
    portal_agent_id = request.session.get('portal_agent_id')
    if not portal_agent_id:
        from django.contrib.auth.decorators import login_required
        return login_required(lambda r, sid: _generate_admission_fee_pdf_internal(r, sid))(request, student_id)
    
    return _generate_admission_fee_pdf_internal(request, student_id)

def _generate_admission_fee_pdf_internal(request, student_id):
    """Internal function to generate Admission Fee Invoice PDF"""
    try:
        student = get_object_or_404(Student, id=student_id)
        
        # Logo Processing
        logo_base64 = ""
        logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
        if os.path.exists(logo_path):
            try:
                with open(logo_path, "rb") as f:
                    logo_base64 = base64.b64encode(f.read()).decode()
            except Exception: pass

        # Background Image Processing
        bg_base64 = ""
        bg_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'admission_fee_invoice_bg.jpg')
        if os.path.exists(bg_path):
            try:
                with open(bg_path, "rb") as f:
                    bg_base64 = base64.b64encode(f.read()).decode()
            except Exception: pass

        context = {
            'student': student,
            'current_date': student.created_at if student.created_at else timezone.now(),
            'logo_base64': logo_base64,
            'bg_base64': bg_base64,
        }
        
        html_string = render_to_string('dashboards/admission_fee_invoice_pdf.html', context)
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="Admission_Fee_Invoice_{student.student_id}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)


@login_required
def approve_student_page(request, student_id):
    return _approval_page(request, student_id, 'approve')

@login_required
def decline_student_page(request, student_id):
    return _approval_page(request, student_id, 'decline')

def _approval_page(request, student_id, action):
    student = get_object_or_404(Student.objects.prefetch_related('education_history', 'work_experience'), id=student_id)
    page_title = 'Approve Student Application' if action == 'approve' else 'Decline Student Application'
    button_text = 'Confirm Approval' if action == 'approve' else 'Confirm Decline'
    button_class = 'btn-success' if action == 'approve' else 'btn-danger'
    
    # Determine back link based on user role
    user_role = getattr(request.user, 'role', '')
    if user_role in ['staff', 'manager', 'admin']:
        back_url = 'dashboard:student_list'
    else:
        back_url = 'dashboard:recruitment_client_dashboard'
        
    return render(request, 'dashboards/approval_page.html', {
        'student': student,
        'action': action,
        'page_title': page_title,
        'button_text': button_text,
        'button_class': button_class,
        'back_url': back_url
    })

@login_required
def approve_student(request, student_id):
    return update_student_status(request, student_id, 'approved')

@login_required
def decline_student(request, student_id):
    return update_student_status(request, student_id, 'declined')

# -----------------------
# Candidate Counts (Dashboard)
# -----------------------
@login_required
def all_candidates(request):
    students = Student.objects.all()
    context = {
        "students": students,
        "total_count": students.count(),
        "pending_count": students.filter(status='pending').count(),
        "approved_count": students.filter(status='approved').count(),
        "declined_count": students.filter(status='declined').count(),
    }
    return render(request, "dashboards/student_list.html", context)

# -----------------------
# Simple Pages
# -----------------------
@login_required
def biodata(request):
    return render(request, 'dashboards/biodata.html')

# -----------------------
# Debug / Test Form
# -----------------------
def test_form_submission(request):
    """Debug view to test form submission"""
    if request.method == 'POST':
        agent = Agent.objects.first()
        response_text = ["="*50, "TEST FORM SUBMISSION", "="*50]
        response_text.append(f"POST data: {dict(request.POST)}")
        response_text.append(f"FILES: {dict(request.FILES)}")
        if agent:
            form = StudentForm(request.POST, request.FILES, agent=agent)
            if form.is_valid():
                student = save_student_form(form, request)
                response_text.append(f"✓ Student saved: {student.student_id}" if student else "✗ Error saving")
            else:
                response_text.append(f"✗ Form is INVALID\nErrors: {form.errors}")
        else:
            response_text.append("✗ No agent found!")
        response_text.append("="*50)
        return HttpResponse("<br>".join(response_text))

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


from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

@login_required
def update_student_status(request, student_id, status=None):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        # If status is provided as parameter, use it; otherwise get from POST
        if status:
            action = status
        else:
            action = request.POST.get('action')

        review_notes = request.POST.get('review_notes', '')

        if action in ['approve', 'approved', 'decline', 'declined']:
            # Normalize to the correct status value
            student.status = 'approved' if action in ['approve', 'approved'] else 'declined'
            student.approved_by = request.user.get_full_name() or request.user.username
            student.reviewed_at = timezone.now()
            student.review_notes = review_notes
            student.save()

            messages.success(request, f'Student {student.full_name} has been {student.status}.')

            # Redirect logic
            if student.status == 'approved':
                return redirect('dashboard:approval_success', student_id=student.id)
            elif student.status == 'declined':
                # For staff/managers, go back to student list with declined tab
                user_role = getattr(request.user, 'role', '')
                if user_role in ['staff', 'manager', 'admin']:
                    return redirect(f"{reverse('dashboard:student_list')}?tab=declined")
                else:
                    return redirect('dashboard:recruitment_client_dashboard')
        else:
            messages.error(request, 'Invalid action.')

    # Fallback redirect if not POST or invalid action
    user_role = getattr(request.user, 'role', '')
    if user_role in ['staff', 'manager', 'admin']:
         return redirect('dashboard:student_list')
    else:
        return redirect('dashboard:recruitment_client_dashboard')

@login_required
def approval_success(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'dashboards/approval_success.html', {'student': student})

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
            return redirect('no_permission')
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


import base64
import os
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from weasyprint import HTML

@login_required
def generate_student_pdf(request, student_id):
    try:
        student = get_object_or_404(
            Student.objects.select_related('agent').prefetch_related(
                'education_history', 'work_experience'
            ),
            id=student_id
        )

        # Photo Processing
        photo_html = '<div style="font-size:8pt; color:#666;">PHOTO</div>'
        if student.photo:
            try:
                photo_path = student.photo.path
                if os.path.exists(photo_path):
                    with open(photo_path, "rb") as f:
                        photo_data = base64.b64encode(f.read()).decode()
                    ext = os.path.splitext(photo_path)[1].lower()
                    mime_type = 'image/jpeg' if ext in ['.jpg', '.jpeg'] else 'image/png'
                    photo_html = f'<img src="data:{mime_type};base64,{photo_data}" style="width:100%; height:100%; object-fit:cover;">'
            except Exception: pass

        # Prepare Loops for Tables
        edu_defaults = ["Primary School", "Junior H. School", "Higher S. School", "College / University", "Graduate University", "Graduate University", "Other School"]
        edu_list = list(student.education_history.all())
        education_rows = ""
        for i in range(7):
            e = edu_list[i] if i < len(edu_list) else None
            education_rows += f"""
            <tr>
                <td class="lbl-sm">{e.pass_level if e else edu_defaults[i]}</td>
                <td>{e.school_name if e else ''}</td>
                <td class="center">{e.admission_year if e else ''}</td>
                <td class="center">{e.admission_month if e else ''}</td>
                <td class="center">{e.graduation_year if e else ''}</td>
                <td class="center">{e.graduation_month if e else ''}</td>
                <td class="right-text">{e.enrolled_years if e else ''} Years</td>
            </tr>"""

        work_list = list(student.work_experience.all())[:3]
        work_rows = ""
        for i in range(3):
            w = work_list[i] if i < len(work_list) else None
            work_rows += f"""
            <tr style="height:25px;">
                <td>{w.work_type if w else ''}</td>
                <td>{w.company_name if w else ''}</td>
                <td class="center">{w.join_date if w else ''} - {w.resign_date if w else ''}</td>
                <td class="right-text">{w.working_years if w else ''} Years</td>
            </tr>"""

        # Context Data
        a_code = student.agent.agent_code if student.agent else ""
        dob = student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else ''
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        @page {{ size: A4; margin: 0.5cm; }}
        body {{ font-family: 'Arial', sans-serif; font-size: 8.5pt; line-height: 1.2; color: #000; }}
        .header {{ text-align: center; margin-bottom: 5px; }}
        .header h1 {{ font-size: 15pt; margin: 0; }}
        .header p {{ font-size: 9pt; margin: 2px 0; }}
        .cc-to {{ text-align: left; font-size: 7pt; font-weight: bold; margin-top: 5px; }}
        
        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
        td, th {{ border: 1px solid #000; padding: 3px 5px; vertical-align: middle; }}
        
        .bg-beige {{ background-color: #C7BFA3; font-weight: bold; text-align: center; }}
        .center {{ text-align: center; }}
        .right-text {{ text-align: right; }}
        .lbl-sm {{ font-size: 7.5pt; }}
        
        .photo-box {{ width: 110px; height: 135px; text-align: center; padding: 0; }}
        .main-title {{ font-size: 11pt; padding: 5px; border: 2px solid #000; border-bottom: none; }}
        
        .sig-text {{ font-size: 7.5pt; text-align: justify; padding: 10px; }}
        .sign-box-border {{ border: 2px solid #000; width: 100%; height: 50px; display: table; }}
        .sign-label {{ display: table-cell; width: 50px; background: #C7BFA3; border-right: 2px solid #000; vertical-align: middle; font-weight: bold; text-align: center; }}
    </style>
</head>
<body>

    <div class="header">
        <h1>AQUA EDUCATION AND TRAINING ACADEMY</h1>
        <p>Lazimpat-02, Kathmandu, Nepal</p>
        <div class="cc-to">CC TO: ZENSHO HOLDINGS / SUKIYA JAPAN / AEON GROUP / TOKYU GROUP / TOKYUSYUKAI JAPAN</div>
    </div>

    <div class="main-title bg-beige">ADMISSION FORM FOR SSW AND WORKING</div>

    <table>
        <tr>
            <td width="15%" class="bg-white">Student ID NO</td>
            <td width="20%">{student.student_id or ''}</td>
            <td width="10%" class="center bg-white">A-CODE</td>
            <td width="15%">{a_code}</td>
            <td width="10%" class="center bg-white">Gender</td>
            <td width="10%">{student.get_gender_display() if student.gender else ''}</td>
            <td rowspan="4" class="photo-box">{photo_html}</td>
        </tr>
        <tr>
            <td class="bg-white">Full Name</td>
            <td colspan="3">{student.full_name or ''}</td>
            <td class="center bg-white">DOB</td>
            <td>{dob}</td>
        </tr>
        <tr>
            <td rowspan="2" class="bg-white">Full Address</td>
            <td class="lbl-sm">Permanent: {student.permanent_address or ''}</td>
            <td colspan="2" class="center bg-white">Age</td>
            <td colspan="2">{student.age or ''}</td>
        </tr>
        <tr>
            <td class="lbl-sm">Present: {student.present_address or ''}</td>
            <td colspan="2" class="center bg-white">Marital Status</td>
            <td colspan="2">{student.get_marital_status_display() if student.marital_status else ''}</td>
        </tr>
    </table>

    <table style="border-top: none;">
        <tr>
            <td width="15%">Passport No.</td>
            <td width="20%">{student.passport_no or ''}</td>
            <td width="15%" class="center">Date of Issue</td>
            <td width="15%">{student.passport_issue_date or ''}</td>
            <td width="15%" class="center">Date of Expired</td>
            <td>{student.passport_expiry_date or ''}</td>
        </tr>
    </table>

    <table style="border-top: none;">
        <tr class="bg-white center" style="font-size: 7pt;">
            <td rowspan="2" width="15%">Personal Info</td>
            <td>Height</td><td>Weight</td><td colspan="2">Eye Lens (R/L)</td><td>Blood</td><td>Visa Record</td><td colspan="2">Visa Result</td>
        </tr>
        <tr class="center">
            <td>{student.height or ''}</td><td>{student.weight or ''}</td>
            <td>{getattr(student, 'eye_lens_right', '')}</td><td>{getattr(student, 'eye_lens_left', '')}</td>
            <td>{student.blood_group or ''}</td><td>{student.get_visa_apply_record_display() if student.visa_apply_record else ''}</td><td colspan="2">{student.visa_details or ''}</td>
        </tr>
    </table>

    <table style="border-top: none;">
        <tr>
            <td width="15%">Email ID</td><td width="45%">{student.email or ''}</td>
            <td width="15%" class="center">Phone No.</td><td>{student.phone or ''}</td>
        </tr>
        <tr>
            <td>Family Records</td><td colspan="3">{student.family_records or ''}</td>
        </tr>
        <tr>
            <td>Spouse Name</td><td>{student.spouse_name or ''}</td>
            <td class="center">Contact No.</td><td>{student.spouse_contact or ''}</td>
        </tr>
    </table>

    <div class="bg-beige" style="border: 1px solid #000; border-top:none; padding: 3px;">EDUCATIONAL HISTORY</div>
    <table>
        <tr class="bg-white center">
            <th width="20%">Pass Level</th><th width="35%">Name of School</th><th colspan="4">Admission & Graduation</th><th width="15%">Enrolled</th>
        </tr>
        <tr class="bg-white center" style="font-size: 7pt;">
            <td colspan="2"></td><td>Year</td><td>Month</td><td>Year</td><td>Month</td><td></td>
        </tr>
        {education_rows}
    </table>

    <div class="bg-beige" style="border: 1px solid #000; border-top:none; padding: 3px;">WORKING EXPERIENCE</div>
    <table>
        <tr class="bg-white center">
            <th>Type of Work</th><th>Name of Working Company</th><th>Date of Join & Resign</th><th>Working Years</th>
        </tr>
        {work_rows}
    </table>

    <table style="border-top: none;">
        <tr>
            <td class="bg-beige" width="50%">LANGUAGE & SKILLS PASSED CERTIFICATE</td>
            <td class="bg-beige">LANGUAGE & SKILLS TRAINING STATUS</td>
        </tr>
        <tr>
            <td style="padding:0;">
                <table style="border:none;">
                    <tr class="center lbl-sm"><td>Pass Yr/Mo</td><td>Exam Name</td></tr>
                    <tr style="height:20px;"><td>{getattr(student, 'certificate_pass_year', '')}</td><td>{getattr(student, 'certificate_name', '')}</td></tr>
                </table>
            </td>
            <td style="padding:0;">
                <table style="border:none;">
                    <tr class="center lbl-sm"><td>Join Yr/Mo</td><td>Organization</td></tr>
                    <tr style="height:20px;"><td>{getattr(student, 'language_join_year', '')}</td><td>{getattr(student, 'organization', '')}</td></tr>
                </table>
            </td>
        </tr>
    </table>

    <table style="border-top: none;">
        <tr>
            <td width="50%"><b>Hobbies, Special skills, etc.</b></td>
            <td><b>Motivation, Self-promotion</b></td>
        </tr>
        <tr style="height: 60px; vertical-align: top;">
            <td>{student.hobbies or ''}</td>
            <td>{student.motivation or ''}</td>
        </tr>
    </table>

    <table style="border: none; margin-top: 5px;">
        <tr>
            <td style="border: none;" width="70%">
                <div class="sig-text">
                    I hereby agree to study the Japanese language at the Aqua Education And Training Academy while strictly complying with all rules and regulations. After going to Japan, I promise to follow all Japanese rules and the immigration law. In the event that I fail to comply with company rules and law of Japan, I agree to accept all penalties in accordance with Japanese rules and Immigration Law.
                </div>
            </td>
            <td style="border: none;">
                <div style="margin-bottom: 5px;">Date: ________________</div>
                <div class="sign-box-border">
                    <div class="sign-label">SIGN</div>
                    <div></div>
                </div>
            </td>
        </tr>
    </table>

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
    return render(request, 'dashboards/approval_page.html', {
        'student': student,
        'action': action,
        'page_title': page_title,
        'button_text': button_text,
        'button_class': button_class
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
    return render(request, "your_template.html", context)

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
            student.reviewed_by = request.user
            student.reviewed_at = timezone.now()
            student.review_notes = review_notes
            student.save()

            messages.success(request, f'Student {student.full_name} has been {student.status}.')

            # Redirect to success page for approval, dashboard for decline
            if student.status == 'approved':
                return redirect('dashboard:approval_success', student_id=student.id)
        else:
            messages.error(request, 'Invalid action.')

    return redirect('dashboard:recruitment_client_dashboard')

@login_required
def approval_success(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'dashboards/approval_success.html', {'student': student})

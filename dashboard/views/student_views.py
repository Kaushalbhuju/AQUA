from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.utils import timezone
from datetime import date
from django.template.loader import get_template
from xhtml2pdf import pisa

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
    student = get_object_or_404(
        Student.objects.prefetch_related('education_history', 'work_experience', 'documents'),
        id=student_id
    )
    template_path = 'dashboards/student_pdf_template.html'
    context = {'student': student}
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="student_{student.student_id}.pdf"'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
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



#Use Django ORM Counts in Your Template
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
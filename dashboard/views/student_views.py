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
        form = StudentForm(request.POST, request.FILES, agent=agent)
        if form.is_valid():
            try:
                student = form.save()
                
                # Handle TB status from radio buttons
                tb_status = request.POST.get('tb_status')
                if tb_status:
                    student.tb_status = tb_status
                    student.save()

                messages.success(request, f'Student {student.full_name} registered successfully with ID: {student.student_id}!')
                return redirect('dashboard:registration_success', student_id=student.id)
            except Exception as e:
                messages.error(request, f'Error saving student: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentForm(agent=agent)
    
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
        form = StudentForm(request.POST, request.FILES, agent=agent)
        if form.is_valid():
            try:
                student = form.save()
                
                # Handle TB status from radio buttons
                tb_status = request.POST.get('tb_status')
                if tb_status:
                    student.tb_status = tb_status
                    student.save()

                messages.success(request, f'Student {student.full_name} registered successfully with ID: {student.student_id}!')
                return redirect('dashboard:agent_dashboard')
            except Exception as e:
                messages.error(request, f'Error saving student: {str(e)}')
        else:
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

# -----------------------
# Simple Pages
# -----------------------
@login_required
def biodata(request):
    return render(request, 'dashboards/biodata.html')
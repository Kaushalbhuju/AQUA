# dashboard_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.urls import reverse
from dashboard.models import Student
from dashboard.decorators import check_role




@login_required(login_url='login')
@check_role('operation_head')
def operation_head_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'Operation Head', 
        'role_description': 'Manage overall operations and staff'
    }
    return render(request, 'dashboards/operation_head_dashboard.html', context)

@login_required(login_url='login')
@check_role('manager')
def manager_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'Manager', 
        'role_description': 'Manage team and projects'
    }
    return render(request, 'dashboards/manager_dashboard.html', context)

@login_required(login_url='login')
@check_role('staff')
def staff_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'Staff', 
        'role_description': 'View assigned tasks and updates'
    }
    return render(request, 'dashboards/staff_dashboard.html', context)

@login_required(login_url='login')
@check_role('college')
def college_student_dashboard(request):
    context = {
        'user': request.user, 
        'role_name': 'College Student', 
        'role_description': 'View job opportunities and apply for positions'
    }
    return render(request, 'dashboards/college_student_dashboard.html', context)

@login_required(login_url='login')
@check_role('client', 'manager', 'staff')
def recruitment_client_dashboard(request):
    # Get counts for each pipeline stage
    candidate_info_count = Student.objects.filter(stage='candidate_info').count()
    select_candidate_count = Student.objects.filter(stage='select_candidate').count()
    interview_pattern_count = Student.objects.filter(stage='interview_pattern').count()
    pass_interview_count = Student.objects.filter(stage='pass_interview').count()
    ceo_approval_count = Student.objects.filter(stage='ceo_approval').count()
    visa_arrival_count = Student.objects.filter(stage='visa_arrival').count()
    
    # Get students for each stage
    candidate_info_students = Student.objects.filter(stage='candidate_info')
    select_candidate_students = Student.objects.filter(stage='select_candidate')
    interview_pattern_students = Student.objects.filter(stage='interview_pattern')
    pass_interview_students = Student.objects.filter(stage='pass_interview')
    ceo_approval_students = Student.objects.filter(stage='ceo_approval')
    visa_arrival_students = Student.objects.filter(stage='visa_arrival')
    
    # Get active tab from URL parameter
    active_tab = request.GET.get('tab', 'candidate-info')
    
    context = {
        # Pipeline counts
        'candidate_info_count': candidate_info_count,
        'select_candidate_count': select_candidate_count,
        'interview_pattern_count': interview_pattern_count,
        'pass_interview_count': pass_interview_count,
        'ceo_approval_count': ceo_approval_count,
        'visa_arrival_count': visa_arrival_count,
        
        # Student querysets for each stage
        'candidate_info_students': candidate_info_students,
        'select_candidate_students': select_candidate_students,
        'interview_pattern_students': interview_pattern_students,
        'pass_interview_students': pass_interview_students,
        'ceo_approval_students': ceo_approval_students,
        'visa_arrival_students': visa_arrival_students,
        
        # Active tab
        'active_tab': active_tab,
        
        # User info
        'user': request.user,
        'role_name': 'Recruitment Manager',
        'role_description': 'Manage candidate recruitment pipeline',
    }
    
    return render(request, 'dashboards/recruitment_client_dashboard.html', context)



# dashboard_views.py - Complete fixed move_to_next_stage function
@login_required
def move_to_next_stage(request, student_id, next_stage):
    """Move student to next stage in pipeline"""
    
    try:
        student = get_object_or_404(Student, id=student_id)
    except Student.DoesNotExist:
        messages.error(request, f'❌ Student with ID {student_id} not found')
        return redirect('/dashboard/recruitment_client/?tab=candidate-info')
    
    # Define the pipeline sequence
    pipeline_sequence = [
        'candidate_info',
        'select_candidate', 
        'interview_pattern',
        'pass_interview',
        'ceo_approval',
        'visa_arrival',
        'completed'
    ]
    
    # Create mapping for URL-friendly names to actual stage names
    stage_mapping = {
        'candidate-info': 'candidate_info',
        'select-candidate': 'select_candidate',
        'interview-pattern': 'interview_pattern',
        'pass-interview': 'pass_interview',
        'ceo-approval': 'ceo_approval',
        'visa-arrival': 'visa_arrival',
        'completed': 'completed'
    }
    
    if next_stage in stage_mapping:
        normalized_next_stage = stage_mapping[next_stage]
    else:
        normalized_next_stage = next_stage.replace('-', '_')
    
    if student.stage not in pipeline_sequence:
        # Auto-fix invalid current stage
        student.stage = 'candidate_info'
        student.save()
        messages.warning(request, f'⚠️  Fixed invalid stage for {student.full_name}')
    
    if normalized_next_stage not in pipeline_sequence:
        valid_stages_display = [stage.replace('_', ' ').title() for stage in pipeline_sequence]
        messages.error(request, f'❌ Invalid target stage: {next_stage}. Valid stages are: {", ".join(valid_stages_display)}')
        return redirect(f'/dashboard/recruitment_client/?tab={student.stage}')
    
    try:
        current_index = pipeline_sequence.index(student.stage)
        next_index = pipeline_sequence.index(normalized_next_stage)
        
        if next_index > current_index:
            old_stage = student.stage
            student.stage = normalized_next_stage
            student.save()
            
            messages.success(request, f'✅ Successfully moved {student.full_name} to {normalized_next_stage.replace("_", " ").title()}')
        elif next_index == current_index:
            messages.warning(request, f'ℹ️  {student.full_name} is already in {normalized_next_stage.replace("_", " ").title()} stage')
        else:
            messages.error(request, f'❌ Cannot move backwards from {student.stage.replace("_", " ").title()} to {normalized_next_stage.replace("_", " ").title()}')
            
    except Exception as e:
        messages.error(request, f'❌ Unexpected error: {str(e)}')
    
    # Redirect back to the dashboard
    redirect_url = f'/dashboard/recruitment_client/?tab={student.stage}'
    print(f"🔀 Redirecting to: {redirect_url}")
    return redirect(redirect_url)
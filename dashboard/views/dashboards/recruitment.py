"""
Recruitment pipeline dashboard views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

from dashboard.models import Student
from ..decorators_fixed import check_role


# Pipeline sequence constant
PIPELINE_SEQUENCE = [
    'candidate_info',
    'select_candidate',
    'interview_pattern',
    'pass_interview',
    'ceo_approval',
    'visa_arrival',
    'completed'
]

STAGE_MAPPING = {
    'candidate-info': 'candidate_info',
    'select-candidate': 'select_candidate',
    'interview-pattern': 'interview_pattern',
    'pass-interview': 'pass_interview',
    'ceo-approval': 'ceo_approval',
    'visa-arrival': 'visa_arrival',
    'completed': 'completed'
}


@login_required(login_url='/')
@check_role('client', 'manager', 'staff')
def recruitment_client_dashboard(request):
    # Single query: aggregate all stage counts at once
    from django.db.models import Count, Case, When, IntegerField
    stage_counts = Student.objects.values('stage').annotate(
        count=Count('id')
    )
    counts = {item['stage']: item['count'] for item in stage_counts}

    # Only fetch students for the active tab
    active_tab = request.GET.get('tab', 'candidate-info')
    current_stage = STAGE_MAPPING.get(active_tab, 'candidate_info')
    active_students = Student.objects.filter(stage=current_stage).select_related('agent')

    context = {
        'candidate_info_count': counts.get('candidate_info', 0),
        'select_candidate_count': counts.get('select_candidate', 0),
        'interview_pattern_count': counts.get('interview_pattern', 0),
        'pass_interview_count': counts.get('pass_interview', 0),
        'ceo_approval_count': counts.get('ceo_approval', 0),
        'visa_arrival_count': counts.get('visa_arrival', 0),
        'candidate_info_students': active_students if active_tab == 'candidate-info' else Student.objects.none(),
        'select_candidate_students': active_students if active_tab == 'select-candidate' else Student.objects.none(),
        'interview_pattern_students': active_students if active_tab == 'interview-pattern' else Student.objects.none(),
        'pass_interview_students': active_students if active_tab == 'pass-interview' else Student.objects.none(),
        'ceo_approval_students': active_students if active_tab == 'ceo-approval' else Student.objects.none(),
        'visa_arrival_students': active_students if active_tab == 'visa-arrival' else Student.objects.none(),
        'active_tab': active_tab,
        'user': request.user,
        'role_name': 'Recruitment Manager',
        'role_description': 'Manage candidate recruitment pipeline',
    }
    return render(request, 'dashboards/recruitment_client_dashboard.html', context)


@login_required
def move_to_next_stage(request, student_id, next_stage):
    """Move student to next stage in pipeline"""
    try:
        student = get_object_or_404(Student, id=student_id)
    except Student.DoesNotExist:
        messages.error(request, f'Student with ID {student_id} not found')
        return redirect('dashboard:recruitment_client_dashboard')

    if next_stage in STAGE_MAPPING:
        normalized_next_stage = STAGE_MAPPING[next_stage]
    else:
        normalized_next_stage = next_stage.replace('-', '_')

    if student.stage not in PIPELINE_SEQUENCE:
        student.stage = 'candidate_info'
        student.save()
        messages.warning(request, f'Fixed invalid stage for {student.full_name}')

    if normalized_next_stage not in PIPELINE_SEQUENCE:
        valid_stages_display = [s.replace('_', ' ').title() for s in PIPELINE_SEQUENCE]
        messages.error(request, f'Invalid target stage: {next_stage}. Valid stages: {", ".join(valid_stages_display)}')
        return redirect(reverse('dashboard:recruitment_client_dashboard') + f'?tab={student.stage}')

    current_index = PIPELINE_SEQUENCE.index(student.stage)
    next_index = PIPELINE_SEQUENCE.index(normalized_next_stage)

    if next_index > current_index:
        student.stage = normalized_next_stage
        student.save()
        messages.success(request, f'Moved {student.full_name} to {normalized_next_stage.replace("_", " ").title()}')
    elif next_index == current_index:
        messages.warning(request, f'{student.full_name} is already in {normalized_next_stage.replace("_", " ").title()} stage')
    else:
        messages.error(request, f'Cannot move backwards from {student.stage.replace("_", " ").title()}')

    return redirect(reverse('dashboard:recruitment_client_dashboard') + f'?tab={student.stage}')
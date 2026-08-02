"""
Student approval/decline views
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required

from dashboard.models import Student

from .utils import check_role


def _approval_page(request, student_id, action):
    student = get_object_or_404(Student.objects.prefetch_related('education_history', 'work_experience'), id=student_id)
    page_title = 'Approve Student Application' if action == 'approve' else 'Decline Student Application'
    button_text = 'Confirm Approval' if action == 'approve' else 'Confirm Decline'
    button_class = 'btn-success' if action == 'approve' else 'btn-danger'

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
def approve_student_page(request, student_id):
    return _approval_page(request, student_id, 'approve')


@login_required
def decline_student_page(request, student_id):
    return _approval_page(request, student_id, 'decline')


@login_required
def approve_student(request, student_id):
    return update_student_status(request, student_id, 'approved')


@login_required
def decline_student(request, student_id):
    return update_student_status(request, student_id, 'declined')


@login_required
def update_student_status(request, student_id, status=None):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        if status:
            action = status
        else:
            action = request.POST.get('action')

        review_notes = request.POST.get('review_notes', '')

        if action in ['approve', 'approved', 'decline', 'declined']:
            student.status = 'approved' if action in ['approve', 'approved'] else 'declined'
            student.approved_by = request.user.get_full_name() or request.user.username
            student.reviewed_at = timezone.now()
            student.review_notes = review_notes
            student.save()

            messages.success(request, f'Student {student.full_name} has been {student.status}.')

            if student.status == 'approved':
                return redirect('dashboard:approval_success', student_id=student.id)
            elif student.status == 'declined':
                user_role = getattr(request.user, 'role', '')
                if user_role in ['staff', 'manager', 'admin']:
                    return redirect(f"{reverse('dashboard:student_list')}?tab=declined")
                else:
                    return redirect('dashboard:recruitment_client_dashboard')
        else:
            messages.error(request, 'Invalid action.')

    user_role = getattr(request.user, 'role', '')
    if user_role in ['staff', 'manager', 'admin']:
        return redirect('dashboard:student_list')
    else:
        return redirect('dashboard:recruitment_client_dashboard')


@login_required
def approval_success(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'dashboards/approval_success.html', {'student': student})
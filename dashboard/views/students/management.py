"""
Student management views (list, detail, etc.)
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import models

from dashboard.models import Student, EducationalHistory, WorkExperience, StudentDocument, Agent

from .utils import check_role


@login_required
def registration_success(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    return render(request, 'dashboards/registration_success.html', {'student': student})


@login_required
def student_list(request):
    students = Student.objects.select_related('agent').all().order_by('-created_at')

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
        from django.contrib import messages
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


@login_required
def all_candidates(request):
    students = Student.objects.select_related('agent').all()
    context = {
        "students": students,
        "total_count": students.count(),
        "pending_count": students.filter(status='pending').count(),
        "approved_count": students.filter(status='approved').count(),
        "declined_count": students.filter(status='declined').count(),
    }
    return render(request, "dashboards/student_list.html", context)


@login_required
def biodata(request):
    return render(request, 'dashboards/biodata.html')
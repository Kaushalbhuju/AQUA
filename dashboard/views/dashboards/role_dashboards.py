"""
Role-specific dashboard views
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from dashboard.models import Student
from staff.models import StaffTask
from ..decorators_fixed import check_role


@login_required(login_url='/')
@check_role('operation_head')
def operation_head_dashboard(request):
    context = {
        'user': request.user,
        'role_name': 'Operation Head',
        'role_description': 'Manage overall operations and staff'
    }
    return render(request, 'dashboards/operation_head_dashboard.html', context)


@login_required(login_url='/')
@check_role('manager')
def manager_dashboard(request):
    context = {
        'user': request.user,
        'role_name': 'Manager',
        'role_description': 'Manage team and projects'
    }
    return render(request, 'dashboards/manager_dashboard.html', context)


@login_required(login_url='/')
@check_role('staff')
def staff_dashboard(request):
    tasks = StaffTask.objects.filter(assigned_to=request.user)
    pending_count = tasks.exclude(status='completed').count()
    context = {
        'user': request.user,
        'role_name': 'Staff',
        'role_description': 'View assigned tasks and updates',
        'tasks': tasks,
        'pending_count': pending_count,
    }
    return render(request, 'dashboards/staff_dashboard.html', context)


@login_required(login_url='/')
@check_role('college')
def college_student_dashboard(request):
    context = {
        'user': request.user,
        'role_name': 'College Student',
        'role_description': 'View job opportunities and apply for positions'
    }
    return render(request, 'dashboards/college_student_dashboard.html', context)


@login_required(login_url='/')
@check_role('teacher')
def teacher_dashboard(request):
    context = {
        'user': request.user,
        'role_name': 'Teacher',
        'role_description': 'Manage student attendance and records'
    }
    return render(request, 'dashboards/teacher_dashboard.html', context)
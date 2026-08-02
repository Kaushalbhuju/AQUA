"""
Student registration views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from dashboard.models import Student, Agent
from dashboard.forms import StudentForm

from .utils import check_role, save_student_form


@login_required(login_url='login')
@check_role('staff', 'manager')
def student_registration(request):
    agent = getattr(request.user, 'agent', None)
    if not agent and request.GET.get('agent_code'):
        agent = Agent.objects.filter(agent_code=request.GET.get('agent_code')).first()
        if not agent:
            messages.error(request, 'Invalid agent code')
            return redirect('home')

    if not agent and request.user.role in ['staff', 'manager']:
        agent = Agent.objects.first()

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
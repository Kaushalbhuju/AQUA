from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from candidate_portal.forms import AgentAuthenticationForm
from candidate_portal.models import Agent
from dashboard.models import Student

def agent_dashboard(request):
    """Agent dashboard showing only their candidates"""
    # Check if agent is logged in
    if 'agent_id' not in request.session:
        return redirect('dashboard:agent_login')
    
    try:
        agent_id = request.session['agent_id']
        agent = Agent.objects.get(id=agent_id)
        
        # Get ONLY this agent's students
        students = Student.objects.filter(agent=agent).select_related('candidate')
        
        # ADD THIS: Get contract
        from candidate_portal.models import Contract
        contract = Contract.objects.filter(agent=agent).order_by('-start_date').first()
        
        context = {
            'agent': agent,
            'agent_code': request.session.get('agent_code', ''),
            'agent_name': request.session.get('agent_name', ''),
            'agent_pin': request.session.get('agent_pin', ''),
            'students': students,
            'total_students': students.count(),
            'remaining_slots': agent.max_candidates - agent.current_candidate_count,
            'page_title': f'Agent Dashboard - {agent.agent_code}',
            'contract': contract,  # ADD THIS
            'candidates': agent.candidates.filter(is_active=True),  # ADD THIS for template compatibility
        }
        
        return render(request, 'candidate_portal/agent_dashboard.html', context)
        
    except Agent.DoesNotExist:
        messages.error(request, 'Agent not found.')
        return redirect('dashboard:agent_login')
def agent_student_detail(request, student_id):
    """Agent view for individual student details"""
    if 'agent_id' not in request.session:
        return redirect('dashboard:agent_login')
    
    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
        student = Student.objects.get(id=student_id, agent=agent)
        
        return render(request, 'candidate_portal/agent_student_detail.html', {
            'student': student,
            'agent': agent,
            'agent_code': request.session.get('agent_code', ''),
            'agent_pin': request.session.get('agent_pin', ''),
            'page_title': f'Student Details - {student.student_id}'
        })
        
    except (Agent.DoesNotExist, Student.DoesNotExist):
        messages.error(request, 'Student not found or access denied.')
        return redirect('dashboard:agent_dashboard')

def agent_student_registration(request):
    """Direct student registration by agent"""
    if 'agent_id' not in request.session:
        return redirect('dashboard:agent_login')
    
    try:
        agent = Agent.objects.get(id=request.session['agent_id'])
        
        if request.method == 'POST':
            from dashboard.forms import StudentForm
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
            from dashboard.forms import StudentForm
            form = StudentForm(agent=agent)
        
        return render(request, 'dashboards/StudentRegistrationForm.html', {
            'form': form,
            'agent': agent,
            'agent_code': request.session.get('agent_code', ''),
            'agent_pin': request.session.get('agent_pin', ''),
        })
        
    except Agent.DoesNotExist:
        messages.error(request, 'Agent not found.')
        return redirect('dashboard:agent_login')
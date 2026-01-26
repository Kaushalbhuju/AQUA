from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from .forms import AgentAuthenticationForm
from .models import Agent, Candidate, Contract
from dashboard.models import Student


class AgentLoginView(View):
    """Agent login view"""
    
    @method_decorator(csrf_protect)
    def get(self, request):
        # Clear any existing session
        self._clear_agent_session(request)
        form = AgentAuthenticationForm()
        return render(request, 'candidate_portal/agent_login.html', {'form': form})
    
    @method_decorator(csrf_protect)
    def post(self, request):
        form = AgentAuthenticationForm(request.POST)
        
        if form.is_valid():
            agent = form.cleaned_data['agent']
            
            # Store agent info in session
            request.session['agent_id'] = str(agent.id)
            request.session['agent_code'] = agent.agent_code
            request.session['agent_name'] = agent.name
            request.session['remaining_slots'] = agent.max_candidates - agent.current_candidate_count
            
            # Update agent last used timestamp
            agent.save(update_fields=['last_used'])
            
            messages.success(
                request, 
                f'Welcome, {agent.name}! '
                f'You have {request.session["remaining_slots"]} registration slots remaining.'
            )
            return redirect('candidate_portal:dashboard')
        
        return render(request, 'candidate_portal/agent_login.html', {
            'form': form,
            'error_message': 'Invalid agent code or PIN.'
        })
    
    def _clear_agent_session(self, request):
        """Clear agent-related session data"""
        session_keys = ['agent_id', 'agent_code', 'agent_name', 'remaining_slots']
        for key in session_keys:
            if key in request.session:
                del request.session[key]


class AgentDashboardView(View):
    """Agent dashboard with all information"""
    
    def get(self, request):
        # Verify agent session
        agent = self._get_agent_from_session(request)
        if not agent:
            messages.error(request, 'Please login first')
            return redirect('candidate_portal:agent_login')
        
        # Get agent's candidates
        candidates = Candidate.objects.filter(agent=agent, is_active=True)
        
        # Get contract (most recent)
        contract = Contract.objects.filter(agent=agent).order_by('-start_date').first()
        
        # Get students for this agent
        students = Student.objects.filter(agent=agent)
        
        context = {
            'agent': agent,
            'candidates': candidates,
            'students': students,
            'contract': contract,
            'remaining_slots': agent.max_candidates - agent.current_candidate_count,
            'total_students': students.count(),
            'total_candidates': candidates.count(),
            'page_title': f'Agent Dashboard - {agent.agent_code}',
        }
        
        return render(request, 'candidate_portal/agent_dashboard.html', context)
    
    def _get_agent_from_session(self, request):
        """Get agent from session or return None"""
        try:
            agent_id = request.session.get('agent_id')
            if agent_id:
                return Agent.objects.get(id=agent_id, is_active=True)
        except (Agent.DoesNotExist, ValueError):
            pass
        return None


class PortalStudentRegistrationView(View):
    """Student registration by agent"""
    
    def get(self, request):
        agent = self._get_agent_from_session(request)
        if not agent:
            return redirect('candidate_portal:agent_login')
        
        if not agent.can_register_candidate():
            messages.error(request, 'Maximum candidate limit reached.')
            return redirect('candidate_portal:agent_logout')
        
        from dashboard.forms import StudentRegistrationForm
        form = StudentRegistrationForm(agent=agent)
        
        context = {
            'form': form,
            'agent': agent,
            'remaining_slots': agent.max_candidates - agent.current_candidate_count,
        }
        
        return render(request, 'dashboards/StudentRegistrationForm.html', context)
    
    @method_decorator(transaction.atomic)
    def post(self, request):
        agent = self._get_agent_from_session(request)
        if not agent:
            return redirect('candidate_portal:agent_login')
        
        if not agent.can_register_candidate():
            messages.error(request, 'Maximum candidate limit reached.')
            return redirect('candidate_portal:agent_logout')
        
        from dashboard.forms import StudentRegistrationForm
        form = StudentRegistrationForm(request.POST, request.FILES, agent=agent)
        
        if form.is_valid():
            try:
                # Create candidate
                candidate = Candidate.objects.create(
                    first_name=form.cleaned_data.get('full_name', '').split()[0],
                    last_name=' '.join(form.cleaned_data.get('full_name', '').split()[1:]),
                    email=form.cleaned_data.get('email'),
                    phone=form.cleaned_data.get('phone', ''),
                    agent=agent
                )
                
                # Create student
                student = form.save(commit=False)
                student.candidate = candidate
                student.agent = agent
                student.student_id = candidate.student_id
                
                # Calculate age
                from datetime import date
                if student.date_of_birth:
                    today = date.today()
                    student.age = today.year - student.date_of_birth.year - (
                        (today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day)
                    )
                
                student.save()
                form.save_related_data(student)
                
                messages.success(request, f'Registration completed! Student ID: {student.student_id}')
                return redirect('candidate_portal:registration_success')
                
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
                return render(request, 'dashboards/StudentRegistrationForm.html', {
                    'form': form,
                    'agent': agent,
                    'remaining_slots': agent.max_candidates - agent.current_candidate_count
                })
        else:
            messages.error(request, 'Please correct the errors below.')
            return render(request, 'dashboards/StudentRegistrationForm.html', {
                'form': form,
                'agent': agent,
                'remaining_slots': agent.max_candidates - agent.current_candidate_count
            })
    
    def _get_agent_from_session(self, request):
        """Get agent from session or return None"""
        try:
            agent_id = request.session.get('agent_id')
            if agent_id:
                return Agent.objects.get(id=agent_id, is_active=True)
        except (Agent.DoesNotExist, ValueError):
            pass
        return None


def registration_success(request):
    """Registration success page"""
    agent = None
    try:
        agent_id = request.session.get('agent_id')
        if agent_id:
            agent = Agent.objects.get(id=agent_id)
    except (Agent.DoesNotExist, ValueError):
        pass
    
    context = {
        'agent': agent,
        'remaining_slots': agent.max_candidates - agent.current_candidate_count if agent else 0
    }
    
    return render(request, 'candidate_portal/registration_success.html', context)


def agent_logout(request):
    """Logout agent"""
    session_keys = ['agent_id', 'agent_code', 'agent_name', 'remaining_slots']
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    
    messages.info(request, 'Logged out successfully')
    return redirect('candidate_portal:agent_login')
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from .forms import AgentAuthenticationForm
from .models import Agent, Candidate
from dashboard.models import Student

# class AgentLoginView(View):
#     """Enhanced agent login with multi-candidate support"""
    
#     @method_decorator(csrf_protect)
#     def get(self, request):
#         # Clear any existing session
#         self._clear_agent_session(request)
        
#         form = AgentAuthenticationForm()
#         return render(request, 'candidate_portal/agent_login.html', {'form': form})
    
#     @method_decorator(csrf_protect)
#     def post(self, request):
#         form = AgentAuthenticationForm(request.POST)
        
#         if form.is_valid():
#             agent = form.cleaned_data['agent']
            
#             # Store agent info in session
#             request.session['agent_id'] = str(agent.id)
#             request.session['agent_code'] = agent.agent_code
#             request.session['agent_name'] = agent.name
#             request.session['remaining_slots'] = agent.max_candidates - agent.current_candidate_count
            
#             # Update agent last used timestamp
#             agent.save(update_fields=['last_used'])
            
#             messages.success(
#                 request, 
#                 f'Welcome, {agent.name}! '
#                 f'You have {request.session["remaining_slots"]} registration slots remaining.'
#             )
#             # Redirect to the CORRECT URL without agent_code parameter
#             return redirect('dashboard:portal_student_registration')
        
#         return render(request, 'candidate_portal/agent_login.html', {
#             'form': form,
#             'error_message': 'Please correct the errors below.'
#         })
#     def _clear_agent_session(self, request):
#         """Clear agent-related session data"""
#         session_keys = ['agent_id', 'agent_code', 'agent_name', 'remaining_slots']
#         for key in session_keys:
#             if key in request.session:
#                 del request.session[key]

class PortalStudentRegistrationView(View):
    """Enhanced registration view with multi-candidate support"""
    
    def get(self, request):
        # Verify agent session
        agent = self._get_agent_from_session(request)
        if not agent:
            return redirect('candidate_portal:agent_login')
        
        # Check if agent can register more candidates
        if not agent.can_register_candidate():
            messages.error(
                request, 
                f'Maximum candidate limit reached ({agent.max_candidates}). '
                f'Please contact administrator.'
            )
            return redirect('candidate_portal:agent_logout')
        
        from dashboard.forms import StudentRegistrationForm
        
        form = StudentRegistrationForm(agent=agent)
        
        context = {
            'form': form,
            'agent': agent,
            'remaining_slots': agent.max_candidates - agent.current_candidate_count,
            'page_title': f'Student Registration - {agent.agent_code}'
        }
        
        return render(request, 'dashboards/StudentRegistrationForm.html', context)
    
    @method_decorator(transaction.atomic)
    def post(self, request):
        # Verify agent session
        agent = self._get_agent_from_session(request)
        if not agent:
            return redirect('candidate_portal:agent_login')
        
        # Check if agent can register more candidates
        if not agent.can_register_candidate():
            messages.error(
                request, 
                f'Maximum candidate limit reached. Please contact administrator.'
            )
            return redirect('candidate_portal:agent_logout')
        
        from dashboard.forms import StudentRegistrationForm
        
        form = StudentRegistrationForm(request.POST, request.FILES, agent=agent)
        
        if form.is_valid():
            try:
                # Create candidate record first
                candidate = Candidate.objects.create(
                    first_name=form.cleaned_data.get('full_name', '').split()[0],
                    last_name=' '.join(form.cleaned_data.get('full_name', '').split()[1:]),
                    email=form.cleaned_data.get('email'),
                    phone=form.cleaned_data.get('phone', ''),
                    agent=agent
                )
                
                # Save student with the generated candidate
                student = form.save(commit=False)
                student.candidate = candidate
                student.agent = agent
                student.student_id = candidate.student_id  # Use auto-generated student ID
                
                # Auto-calculate age
                from datetime import date
                if student.date_of_birth:
                    today = date.today()
                    student.age = today.year - student.date_of_birth.year - (
                        (today.month, today.day) < (student.date_of_birth.month, student.date_of_birth.day)
                    )
                
                student.save()
                form.save_related_data(student)
                
                messages.success(
                    request, 
                    f'Registration completed successfully! '
                    f'Student ID: <strong>{student.student_id}</strong>'
                )
                
                # Redirect back to portal for next registration
                return redirect('candidate_portal:registration_success')
                
            except Exception as e:
                messages.error(
                    request, 
                    f'Registration failed: {str(e)}. Please try again.'
                )
                return redirect('dashboard:portal_student_registration')
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
    """Registration success page with option for next registration"""
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
    """Logout agent and clear session"""
    session_keys = ['agent_id', 'agent_code', 'agent_name', 'remaining_slots']
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    
    messages.info(request, 'You have been successfully logged out.')
    return redirect('candidate_portal:agent_login')

# Legacy views for backward compatibility
class CandidateLoginView(View):
    """Legacy candidate login view for backward compatibility"""
    
    @method_decorator(csrf_protect)
    def get(self, request):
        messages.info(request, 'Please use the new agent login system.')
        return redirect('candidate_portal:agent_login')

class AgentCandidatePageView(View):
    """Legacy agent candidate page for backward compatibility"""
    
    def get(self, request, agent_code):
        messages.info(request, 'Please use the new registration system.')
        return redirect('candidate_portal:agent_login')

def candidate_logout(request):
    """Legacy candidate logout for backward compatibility"""
    messages.info(request, 'Please use the new agent logout system.')
    return redirect('candidate_portal:agent_logout')
# Agents dashboards
class AgentDashboardView(View):
    """Agent dashboard showing candidates and registration options"""
    
    def get(self, request):
        # Verify agent session
        agent = self._get_agent_from_session(request)
        if not agent:
            return redirect('candidate_portal:agent_login')
        
        # Get agent's candidates
        candidates = Candidate.objects.filter(agent=agent, is_active=True)
        
        context = {
            'agent': agent,
            'candidates': candidates,
            'remaining_slots': agent.max_candidates - agent.current_candidate_count,
            'page_title': f'Agent Dashboard - {agent.agent_code}'
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
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from candidate_portal.forms import AgentAuthenticationForm
from candidate_portal.models import Agent, Candidate
from dashboard.forms import StudentRegistrationForm
from dashboard.models import Student

class PortalStudentRegistrationView(View):
    """Candidate registration portal - candidates use agent credentials"""
    
    def get(self, request):
        # Check if we're already logged in as agent (for candidate registration)
        agent = self._get_agent_from_session(request)
        
        if agent:
            # Show registration form directly
            form = StudentRegistrationForm(agent=agent)
            return render(request, 'dashboards/StudentRegistrationForm.html', {
                'form': form,
                'agent': agent,
                'remaining_slots': agent.max_candidates - agent.current_candidate_count,
                'page_title': f'Student Registration - {agent.agent_code}',
                'is_portal_registration': True
            })
        else:
            # Show agent login form for candidates
            return render(request, 'candidate_portal/candidate_login.html', {
                'page_title': 'Student Registration Portal'
            })
    
    def post(self, request):
        # Check if this is a login attempt or registration submission
        # Registration form has full_name, login form only has agent_code
        if 'agent_code' in request.POST and 'full_name' not in request.POST:
            # Handle agent login for candidate (promo code only)
            return self._handle_agent_login(request)
        else:
            # Handle student registration form
            return self._handle_student_registration(request)
    
    def _handle_agent_login(self, request):
        """Authenticate agent for candidate registration using promo code only"""
        agent_code = request.POST.get('agent_code', '').strip().upper()
        
        if agent_code:
            try:
                # Validate agent credentials using promo code only
                agent = Agent.objects.get(
                    agent_code=agent_code,
                    is_active=True
                )
                
                # Check if agent has available slots
                if not agent.can_register_candidate():
                    return render(request, 'candidate_portal/candidate_login.html', {
                        'error_message': f'Promo code {agent.agent_code} has reached maximum registration limit ({agent.max_candidates}).',
                        'page_title': 'Student Registration Portal'
                    })
                
                # Store in session with PORTAL prefix to avoid conflicts
                request.session['portal_agent_id'] = agent.id
                request.session['portal_agent_code'] = agent.agent_code
                request.session['portal_agent_name'] = agent.name
                
                # Show registration form
                form = StudentRegistrationForm(agent=agent)
                return render(request, 'dashboards/StudentRegistrationForm.html', {
                    'form': form,
                    'agent': agent,
                    'remaining_slots': agent.max_candidates - agent.current_candidate_count,
                    'page_title': f'Student Registration - {agent.agent_code}',
                    'is_portal_registration': True
                })
                
            except Agent.DoesNotExist:
                return render(request, 'candidate_portal/candidate_login.html', {
                    'error_message': 'Invalid promo code. Please try again.',
                    'page_title': 'Student Registration Portal'
                })
        else:
            return render(request, 'candidate_portal/candidate_login.html', {
                'error_message': 'Please enter a promo code.',
                'page_title': 'Student Registration Portal'
            })
    
    def _handle_student_registration(self, request):
        """Process student registration form"""
        agent = self._get_agent_from_session(request)
        if not agent:
            messages.error(request, 'Please login with agent credentials first.')
            return redirect('dashboard:portal_student_registration')
        
        form = StudentRegistrationForm(request.POST, request.FILES, agent=agent)
        
        if form.is_valid():
            try:
                # Save student directly (candidate will be created automatically)
                student = form.save()
                
                messages.success(
                    request, 
                    f'Registration completed successfully! Student ID: <strong>{student.student_id}</strong>'
                )
                
                # Store student ID in session for PDF generation
                request.session['portal_last_student_id'] = student.id
                request.session.modified = True
                
                # Keep session for potential next registration
                return redirect('dashboard:portal_registration_success')
                
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
        
        return render(request, 'dashboards/StudentRegistrationForm.html', {
            'form': form,
            'agent': agent,
            'remaining_slots': agent.max_candidates - agent.current_candidate_count,
            'page_title': f'Student Registration - {agent.agent_code}',
            'is_portal_registration': True
        })
    
    def _get_agent_from_session(self, request):
        """Get agent from session using PORTAL prefix"""
        try:
            agent_id = request.session.get('portal_agent_id')
            if agent_id:
                return Agent.objects.get(id=agent_id, is_active=True)
        except (Agent.DoesNotExist, ValueError):
            pass
        return None

def portal_registration_success(request):
    """Registration success page"""
    agent = None
    student = None
    try:
        agent_id = request.session.get('portal_agent_id')
        if agent_id:
            agent = Agent.objects.get(id=agent_id)
    except Agent.DoesNotExist:
        pass
    
    # Get the last registered student for PDF generation
    try:
        student_id = request.session.get('portal_last_student_id')
        if student_id:
            student = Student.objects.get(id=student_id)
    except Student.DoesNotExist:
        pass
    
    context = {
        'agent': agent,
        'student': student,
        'remaining_slots': agent.max_candidates - agent.current_candidate_count if agent else 0,
        'page_title': 'Registration Successful'
    }
    
    return render(request, 'candidate_portal/registration_success.html', context)

def portal_logout(request):
    """Logout candidate from portal and return to promo code entry"""
    # Clear portal-related session data
    portal_keys = ['portal_agent_id', 'portal_agent_code', 'portal_agent_name']
    for key in portal_keys:
        if key in request.session:
            del request.session[key]
            
    messages.info(request, 'You have been logged out from the portal.')
    return redirect('dashboard:portal_student_registration')
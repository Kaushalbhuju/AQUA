# candidate_portal/forms.py
from django import forms
from .models import Agent

class AgentAuthenticationForm(forms.Form):
    agent_code = forms.CharField(max_length=20)
    pin_code = forms.CharField(max_length=10, widget=forms.PasswordInput)
    email = forms.EmailField(required=True)  # FIXED: pin_code not pincode
    
    def clean(self):
        cleaned_data = super().clean()
        agent_code = cleaned_data.get('agent_code')
        pin_code = cleaned_data.get('pin_code')
        email = cleaned_data.get('email')

        
        if agent_code and pin_code and email:
            try:
                agent = Agent.objects.get(
                    agent_code=agent_code.upper().strip(),
                    pin_code=pin_code.strip(),
                    email=email.lower().strip(),   # FIXED: pin_code not pincode
                    is_active=True
                )
                cleaned_data['agent'] = agent
            except Agent.DoesNotExist:
                raise forms.ValidationError("Invalid agent code or PIN code or email.")
        
        return cleaned_data
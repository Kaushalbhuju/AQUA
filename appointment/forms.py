from django import forms
from django.core.exceptions import ValidationError
from .models import Appointment, AppointmentSlot
from django.utils import timezone

class AppointmentForm(forms.ModelForm):
    """Main appointment booking form"""
    class Meta:
        model = Appointment
        fields = [
            'name', 'email', 'phone', 'address',
            'company_name', 'position', 'appointment_aim',
            'message', 'appointment_slot'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'message': forms.Textarea(attrs={'rows': 4}),
            'appointment_slot': forms.HiddenInput(),  # Will be set via JavaScript
        }
    
    def clean_appointment_slot(self):
        slot = self.cleaned_data.get('appointment_slot')
        if slot:
            if slot.start_time < timezone.now():
                raise ValidationError("Cannot book past time slots.")
            if slot.is_full:
                raise ValidationError("This time slot is fully booked.")
        return slot

class DateFilterForm(forms.Form):
    """Form for filtering available slots by date"""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'datepicker'}),
        initial=timezone.now().date()
    )
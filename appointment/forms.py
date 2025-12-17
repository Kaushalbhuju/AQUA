# appointment/forms.py
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
            'appointment_slot': forms.HiddenInput(),
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

class AppointmentSlotForm(forms.ModelForm):
    """Form for creating/editing appointment slots"""
    class Meta:
        model = AppointmentSlot
        fields = ['start_time', 'end_time', 'max_capacity', 'is_available']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if start_time and end_time:
            if start_time >= end_time:
                raise ValidationError("End time must be after start time.")
            
            if start_time < timezone.now():
                raise ValidationError("Cannot create slots in the past.")
        
        return cleaned_data
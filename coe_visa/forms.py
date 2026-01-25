from django import forms
from .models import VisaTracking

class VisaTrackingForm(forms.ModelForm):
    class Meta:
        model = VisaTracking
        fields = '__all__'
        exclude = ['student', 'created_at', 'updated_at']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'application_number': forms.TextInput(attrs={'class': 'form-control'}),
            'applied_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'approved_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'interview_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'visa_document': forms.FileInput(attrs={'class': 'form-control'}),
        }
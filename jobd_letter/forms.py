from django import forms
from .models import JobDemandLetter

class JobDemandLetterForm(forms.ModelForm):
    class Meta:
        model = JobDemandLetter
        fields = ['title', 'description', 'pdf_file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'pdf_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
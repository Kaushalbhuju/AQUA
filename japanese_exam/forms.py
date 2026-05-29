from django import forms
from .models import ExamResult

class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ['status', 'score']
        widgets = {
            'status': forms.RadioSelect(choices=ExamResult.STATUS_CHOICES),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter score'}),
        }

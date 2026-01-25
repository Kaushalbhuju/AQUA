from django import forms
from .models import Agreement

class AgreementForm(forms.ModelForm):
    class Meta:
        model = Agreement
        fields = ['title', 'document']

# other_documents/forms.py
from django import forms
from .models import FinancialDocument, DocumentComment
from datetime import datetime

class FinancialDocumentForm(forms.ModelForm):
    class Meta:
        model = FinancialDocument
        fields = ['title', 'description', 'document_type', 'file', 'fiscal_year', 'is_confidential', 'client_name', 'project_code']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'fiscal_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_confidential': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'project_code': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_fiscal_year(self):
        year = self.cleaned_data.get('fiscal_year')
        current_year = datetime.now().year
        if year and (year < 2000 or year > current_year + 1):
            raise forms.ValidationError(f'Fiscal year must be between 2000 and {current_year + 1}')
        return year

class DocumentCommentForm(forms.ModelForm):
    class Meta:
        model = DocumentComment
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
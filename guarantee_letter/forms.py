# guarantee_letter/forms.py - UPDATED
from django import forms
from django.core.exceptions import ValidationError
import os
import re
from .models import Client, JobGuaranteeLetter, JobGuaranteeLetterTemplate

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'email', 'phone', 'passport_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_passport_number(self):
        passport = self.cleaned_data.get('passport_number')
        if passport:
            if not re.match(r'^[A-Z0-9]{6,12}$', passport):
                raise ValidationError('Invalid passport number format. Use 6-12 alphanumeric characters (uppercase).')
        return passport

class UploadLetterForm(forms.ModelForm):
    """Form for uploading existing PDF letters"""
    class Meta:
        model = JobGuaranteeLetter
        fields = [
            'client', 'candidate_name', 'candidate_email', 'candidate_phone',
            'passport_number', 'job_title', 'company_name', 'department',
            'letter_type', 'issue_date', 'start_date', 'expiry_date',
            'salary_amount', 'salary_currency', 'pdf_file', 'remarks', 'notes'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'candidate_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'candidate_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'candidate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AB123456'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Software Engineer'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ABC Company Ltd.'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., IT Department'}),
            'letter_type': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50000'}),
            'salary_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., USD'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes...'}),
        }
    
    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get('pdf_file')
        if pdf_file:
            ext = os.path.splitext(pdf_file.name)[1].lower()
            if ext != '.pdf':
                raise ValidationError('Only PDF files are allowed.')
            if pdf_file.size > 10 * 1024 * 1024:
                raise ValidationError('File size must be under 10MB.')
        return pdf_file
    
    def clean(self):
        cleaned_data = super().clean()
        expiry_date = cleaned_data.get('expiry_date')
        issue_date = cleaned_data.get('issue_date')
        
        if expiry_date and issue_date:
            if expiry_date <= issue_date:
                raise ValidationError('Expiry date must be after issue date.')
        return cleaned_data

class CreateLetterForm(forms.ModelForm):
    """Form for creating new letters from templates"""
    template = forms.ModelChoiceField(
        queryset=JobGuaranteeLetterTemplate.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'template-select'}),
        empty_label="Select a template",
        required=True
    )
    
    class Meta:
        model = JobGuaranteeLetter
        fields = [
            'client', 'candidate_name', 'candidate_email', 'candidate_phone',
            'passport_number', 'job_title', 'company_name', 'department',
            'letter_type', 'issue_date', 'start_date', 'expiry_date',
            'salary_amount', 'salary_currency', 'remarks', 'notes'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'candidate_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'candidate_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@example.com'}),
            'candidate_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'}),
            'passport_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AB123456'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Software Engineer'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ABC Company Ltd.'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., IT Department'}),
            'letter_type': forms.Select(attrs={'class': 'form-select'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary_amount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 50000'}),
            'salary_currency': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., USD'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Internal notes...'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        expiry_date = cleaned_data.get('expiry_date')
        issue_date = cleaned_data.get('issue_date')
        
        if expiry_date and issue_date:
            if expiry_date <= issue_date:
                raise ValidationError('Expiry date must be after issue date.')
        return cleaned_data

class TemplateForm(forms.ModelForm):
    """Form for creating/editing templates"""
    class Meta:
        model = JobGuaranteeLetterTemplate
        fields = ['name', 'description', 'content', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 15}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
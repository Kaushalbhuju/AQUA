from django import forms
from .models import Company, CompanyYearlyData
from django.core.exceptions import ValidationError

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = '__all__'
        widgets = {
            'company_id': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name_english': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name_japanese': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-control'}),
            'fax_no': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'head_office_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'corporate_office_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'representative_name': forms.TextInput(attrs={'class': 'form-control'}),
            'representative_mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'company_type': forms.TextInput(attrs={'class': 'form-control'}),
            'agreement_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'agreement_type': forms.Select(attrs={'class': 'form-control'}),
            'agreement_doc': forms.FileInput(attrs={'class': 'form-control'}),
            'interview_pass_doc': forms.FileInput(attrs={'class': 'form-control'}),
            'visa_apply_doc': forms.FileInput(attrs={'class': 'form-control'}),
            'ceo_visa_doc': forms.FileInput(attrs={'class': 'form-control'}),
            'other_doc': forms.FileInput(attrs={'class': 'form-control'}),
            'pdf_doc_1': forms.FileInput(attrs={'class': 'form-control'}),
            'pdf_doc_2': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If updating, make ALL fields not required
        if self.instance and self.instance.pk:
            for field_name in self.fields:
                self.fields[field_name].required = False

    def clean_company_id(self):
        company_id = self.cleaned_data.get('company_id')
        # Only validate company_id if it's being changed
        if company_id and self.instance.pk and company_id != self.instance.company_id:
            if Company.objects.filter(company_id=company_id).exists():
                raise ValidationError("Company ID already exists.")
        return company_id

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # For updates, only save fields that were actually provided in the form
        if self.instance.pk:
            for field in self.fields:
                field_value = self.cleaned_data.get(field)
                if field_value not in [None, '']:  # Only update if value was provided
                    setattr(instance, field, field_value)
        
        if commit:
            instance.save()
        
        return instance

class CompanyYearlyDataForm(forms.ModelForm):
    class Meta:
        model = CompanyYearlyData
        fields = ['year', 'yearly_student_no', 'interview_attend_no', 'interview_pass_no', 'visa_application_no', 'ceo_success_no']
        widgets = {
            'year': forms.NumberInput(attrs={
                'class': 'form-control year-input', 
                'min': 2024,
                'max': 2035,
                'placeholder': 'Year'
            }),
            'yearly_student_no': forms.NumberInput(attrs={
                'class': 'form-control number-input', 
                'min': 0,
                'placeholder': '0'
            }),
            'interview_attend_no': forms.NumberInput(attrs={
                'class': 'form-control number-input', 
                'min': 0,
                'placeholder': '0'
            }),
            'interview_pass_no': forms.NumberInput(attrs={
                'class': 'form-control number-input', 
                'min': 0,
                'placeholder': '0'
            }),
            'visa_application_no': forms.NumberInput(attrs={
                'class': 'form-control number-input', 
                'min': 0,
                'placeholder': '0'
            }),
            'ceo_success_no': forms.NumberInput(attrs={
                'class': 'form-control number-input', 
                'min': 0,
                'placeholder': '0'
            }),
        }

# Formset for yearly data
CompanyYearlyDataFormSet = forms.inlineformset_factory(
    Company,
    CompanyYearlyData,
    form=CompanyYearlyDataForm,
    extra=5,
    can_delete=True,
    max_num=10,
)
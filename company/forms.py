from django import forms
from .models import College, CollegeYearlyData

class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = '__all__'
        widgets = {
            'college_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter College ID'}),
            'college_name_english': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter College Name in English'}),
            'college_name_japanese': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter College Name in Japanese'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Phone Number'}),
            'fax_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Fax Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter Email ID'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter Website URL'}),
            'head_office_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Head Office Address'}),
            'corporate_office_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter Corporate Office Address'}),
            'representative_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Representative Name'}),
            'representative_mobile': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Representative Mobile'}),
            'college_type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Type of College'}),
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
        labels = {
            'college_id': 'College ID',
            'college_name_english': 'College Name (In English)',
            'college_name_japanese': 'College Name (In Japanese)',
            'phone_no': 'Phone No.',
            'fax_no': 'Fax No.',
            'email': 'College Email ID',
            'website': 'Home Page',
            'head_office_address': 'Head Office Address',
            'corporate_office_address': 'Corporate Office Address',
            'representative_name': 'Representative Name',
            'representative_mobile': 'Representative Mobile',
            'college_type': 'Type of College',
            'agreement_date': 'Agreement Date',
            'expire_date': 'Expire Date',
            'agreement_type': 'Agreement Type',
        }

class CollegeYearlyDataForm(forms.ModelForm):
    class Meta:
        model = CollegeYearlyData
        fields = ['year', 'yearly_student_no', 'interview_attend_no', 'interview_pass_no', 'visa_application_no', 'ceo_success_no']
        widgets = {
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': 2024}),
            'yearly_student_no': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'interview_attend_no': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'interview_pass_no': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'visa_application_no': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'ceo_success_no': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

# Formset for yearly data
CollegeYearlyDataFormSet = forms.inlineformset_factory(
    College,
    CollegeYearlyData,
    form=CollegeYearlyDataForm,
    extra=10,  # 10 years from 2024-2033
    can_delete=True,
    max_num=10
)
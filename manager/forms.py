from django import forms
from django.forms import inlineformset_factory
from .models import (
    StaffRegistration, EducationalHistory, WorkingExperience,
    CertificateOfSkills, SkillsTrainingStatus, DrivingLicense, BankInformation
)

class StaffRegistrationForm(forms.ModelForm):
    class Meta:
        model = StaffRegistration
        fields = '__all__'
        exclude = ['created_at', 'updated_at']
        widgets = {
            'staff_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Auto-generated if left blank'}),
            'gender': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'marital_status': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'permanent_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'required': 'required'}),
            'present_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'required': 'required'}),
            'candidate_photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'id_passport_no': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'date_of_issue': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': 'required'}),
            'issue_from': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': 'required'}),
            'eye_lense_right': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'eye_lense_left': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'blood_group': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'phone_no': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '10', 'placeholder': '10 digits only', 'required': 'required'}),
            'email_id': forms.EmailInput(attrs={'class': 'form-control', 'required': 'required'}),
            'spouse_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_no': forms.TextInput(attrs={'class': 'form-control'}),
            'hobbies': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': 'required'}),
            'motivation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'required': 'required'}),
            'staff_bio_data_pdf': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf', 'required': 'required'}),
            'staff_id_doc_pdf': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf', 'required': 'required'}),
            'staff_login_report_pdf': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
            'staff_login_id_pdf': forms.FileInput(attrs={'class': 'form-control', 'accept': 'application/pdf'}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            from datetime import date
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 18:
                raise forms.ValidationError("Staff must be at least 18 years old.")
            if dob > today:
                raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean_date_of_issue(self):
        doi = self.cleaned_data.get('date_of_issue')
        if doi:
            from datetime import date
            if doi > date.today():
                raise forms.ValidationError("Date of issue cannot be in the future.")
        return doi

    def clean_email_id(self):
        email = self.cleaned_data.get('email_id')
        if email:
            qs = StaffRegistration.objects.filter(email_id=email)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("This email is already registered.")
        return email
class BankInformationForm(forms.ModelForm):
    class Meta:
        model = BankInformation
        fields = [
            "bank_name",
            "branch_name",
            "account_no",
            "account_holder_name",
        ]
        widgets = {
            "bank_name": forms.TextInput(attrs={"class": "form-control"}),
            "branch_name": forms.TextInput(attrs={"class": "form-control"}),
            "account_no": forms.TextInput(attrs={"class": "form-control"}),
            "account_holder_name": forms.TextInput(attrs={"class": "form-control"}),
        }
# forms.py (same file)


from django.forms import inlineformset_factory
from .models import StaffRegistration, BankInformation

BankFormSet = inlineformset_factory(
    StaffRegistration,
    BankInformation,
    fields=["bank_name", "branch_name", "account_no", "account_holder_name"],
    extra=1,
    can_delete=False
)


class EducationalHistoryForm(forms.ModelForm):
    class Meta:
        model = EducationalHistory
        fields = '__all__'
        exclude = ['staff']
        widgets = {
            'pass_level': forms.Select(attrs={'class': 'form-control form-control-sm'}),
            'name_of_school': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'admission_year': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Year'}),
            'admission_month': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Month'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Year'}),
            'graduation_month': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Month'}),
            'enrolled_years': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Years'}),
            
        }


class WorkingExperienceForm(forms.ModelForm):
    class Meta:
        model = WorkingExperience
        fields = '__all__'
        exclude = ['staff']
        widgets = {
            'type_of_work': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'name_of_company': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'join_year': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Year'}),
            'join_month': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Month'}),
            'resign_year': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Year'}),
            'resign_month': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Month'}),
            'working_years': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Years'}),
        }


class CertificateOfSkillsForm(forms.ModelForm):
    class Meta:
        model = CertificateOfSkills
        fields = '__all__'
        exclude = ['staff']
        widgets = {
            'pass_year': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Year'}),
            'pass_month': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Month'}),
            'name_of_certificate': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'join_year': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Year'}),
            'join_month': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Month'}),
            'organization': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


class SkillsTrainingStatusForm(forms.ModelForm):
    class Meta:
        model = SkillsTrainingStatus
        fields = '__all__'
        exclude = ['staff']
        widgets = {
            'pass_year': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Year'}),
            'pass_month': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Month'}),
            'name_of_training': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
            'join_year': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Year'}),
            'join_month': forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'placeholder': 'Month'}),
            'organization': forms.TextInput(attrs={'class': 'form-control form-control-sm'}),
        }


class DrivingLicenseForm(forms.ModelForm):
    class Meta:
        model = DrivingLicense
        fields = '__all__'
        exclude = ['staff']
        widgets = {
            'pass_year': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}),
            'pass_month': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Month'}),
            'discretion_of_license': forms.TextInput(attrs={'class': 'form-control'}),
        }


# Create formsets
EducationalHistoryFormSet = inlineformset_factory(
    StaffRegistration, EducationalHistory, form=EducationalHistoryForm,
    extra=7, can_delete=True
)

WorkingExperienceFormSet = inlineformset_factory(
    StaffRegistration, WorkingExperience, form=WorkingExperienceForm,
    extra=3, can_delete=True
)

CertificateFormSet = inlineformset_factory(
    StaffRegistration, CertificateOfSkills, form=CertificateOfSkillsForm,
    extra=2, can_delete=True
)

TrainingFormSet = inlineformset_factory(
    StaffRegistration, SkillsTrainingStatus, form=SkillsTrainingStatusForm,
    extra=2, can_delete=True
)

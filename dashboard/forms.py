from django import forms 
from django.contrib.auth.forms import AuthenticationForm
from datetime import date
import re
import os
import os

class AgentLoginForm(AuthenticationForm):
    agent_code = forms.CharField(max_length=20, required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Agent Code'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'PIN'})



class StudentForm(forms.ModelForm):
    """Main student registration form"""
    
    # Auto-filled fields (readonly)
    agent_code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'style': 'background-color: #f8f9fa;'
        })
    )
    
    student_id_preview = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'style': 'background-color: #f8f9fa;'
        })
    )
      # Add Eye Lens fields
    eye_lens_right = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., -2.00'
        })
    )
    
    eye_lens_left = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., -1.50'
        })
    )
    # TB Status field
    tb_status = forms.ChoiceField(
        choices=[('positive', 'Positive'), ('negative', 'Negative')],
        required=True,
        widget=forms.RadioSelect(),
        initial='negative'
    )
    
    # Stage field - ADD THIS
    stage = forms.CharField(
    initial='candidate_info',
    widget=forms.HiddenInput()
)

    experience = forms.IntegerField(
    initial=0,
    widget=forms.HiddenInput()
)
    
    
    # Educational history fields
    school_primary_school = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Name'}))
    admission_year_primary_school = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    admission_month_primary_school = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    graduation_year_primary_school = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    graduation_month_primary_school = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    enrolled_years_primary_school = forms.CharField(required=True, initial='5', widget=forms.TextInput(attrs={'class': 'form-control readonly', 'readonly': 'readonly', 'placeholder': 'Years (e.g. 5.0)'}))
    
    school_junior_h_school = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Name'}))
    admission_year_junior_h_school = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    admission_month_junior_h_school = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    graduation_year_junior_h_school = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    graduation_month_junior_h_school = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    enrolled_years_junior_h_school = forms.CharField(required=True, initial='5', widget=forms.TextInput(attrs={'class': 'form-control readonly', 'readonly': 'readonly', 'placeholder': 'Years (e.g. 5.0)'}))
    
    school_higher_s_school = forms.CharField(max_length=200, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Name'}))
    admission_year_higher_s_school = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    admission_month_higher_s_school = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    graduation_year_higher_s_school = forms.IntegerField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    graduation_month_higher_s_school = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=True, widget=forms.Select(attrs={'class': 'form-control'}))
    enrolled_years_higher_s_school = forms.CharField(required=True, initial='2', widget=forms.TextInput(attrs={'class': 'form-control readonly', 'readonly': 'readonly', 'placeholder': 'Years (e.g. 2.0)'}))
    
    school_college_university = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Name'}))
    admission_year_college_university = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    admission_month_college_university = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    graduation_year_college_university = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    graduation_month_college_university = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    enrolled_years_college_university = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Years (e.g. 4.0)'}))
    
    school_graduate_university = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Name'}))
    admission_year_graduate_university = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    admission_month_graduate_university = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    graduation_year_graduate_university = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    graduation_month_graduate_university = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    enrolled_years_graduate_university = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Years (e.g. 2.0)'}))
    
    school_other_school = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'School Name'}))
    admission_year_other_school = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    admission_month_other_school = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    graduation_year_other_school = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Year'}))
    graduation_month_other_school = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 13)], required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    enrolled_years_other_school = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Years (e.g. 1.0)'}))
    
    # Work experience fields
    work_type_1 = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Work Type'}))
    company_name_1 = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}))
    join_date_1 = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Join Date'}))
    resign_date_1 = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resign Date'}))
    working_years_1 = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Years (e.g. 2.6)'}))
    
    work_type_2 = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Work Type'}))
    company_name_2 = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company Name'}))
    join_date_2 = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Join Date'}))
    resign_date_2 = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Resign Date'}))
    working_years_2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Years (e.g. 1.3)'}))
    
    # Document fields
    bio_data_file = forms.FileField(label="Passport", required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    id_info_file = forms.FileField(label="Citizenship/Driving", required=True, widget=forms.FileInput(attrs={'class': 'form-control'}))
    educational_doc_file = forms.FileField(label="Graduation/Transcript", required=True, widget=forms.FileInput(attrs={'class': 'form-control'}))
    report_file = forms.FileField(label="Medical Report", required=True, widget=forms.FileInput(attrs={'class': 'form-control'}))
    other_file = forms.FileField(label="Other PDF", required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    
    def _clean_file_field(self, field_name, label, max_mb=5):
        file = self.cleaned_data.get(field_name)
        if file:
            valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(f'Unsupported file extension for {label}. Please upload PDF, Word, or image files.')
            
            if file.size > max_mb * 1024 * 1024:
                raise forms.ValidationError(f'{label} size must be less than {max_mb}MB.')
        return file

    def clean_bio_data_file(self): return self._clean_file_field('bio_data_file', 'Passport')
    def clean_id_info_file(self): return self._clean_file_field('id_info_file', 'Citizenship/Driving')
    def clean_educational_doc_file(self): return self._clean_file_field('educational_doc_file', 'Graduation/Transcript')
    def clean_report_file(self): return self._clean_file_field('report_file', 'Medical Report')
    def clean_other_file(self): return self._clean_file_field('other_file', 'Other PDF')
    
    class Meta:
        # Import here to avoid circular imports
        from dashboard.models import Student
        model = Student
        # Remove stage and experience from exclude since we're defining them explicitly
        exclude = ['status', 'reviewed_at', 'review_notes', 'candidate', 'agent', 'student_id']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'required': 'required'}),
            'passport_issue_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'passport_expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'permanent_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control', 'required': 'required'}),
            'present_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'family_records': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'visa_details': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'hobbies': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'required': 'required'}),
            'motivation': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'required': 'required'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'required': 'required'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'height': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g., 5'8\"", 'required': 'required'}),
            'weight': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 65 kg', 'required': 'required'}),
            'spouse_name': forms.TextInput(attrs={'class': 'form-control'}),
            'spouse_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'certificate_pass_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Year & Month'}),
            'certificate_name': forms.TextInput(attrs={'class': 'form-control'}),
            'language_join_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Year & Month'}),
            'organization': forms.TextInput(attrs={'class': 'form-control'}),
            'driving_license': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'license_pass_year': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Year & Month'}),
            'license_type_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': ''}),
            'license_pass_year_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Year & Month'}),
            'gender': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'marital_status': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'blood_group': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'visa_apply_record': forms.Select(attrs={'class': 'form-control', 'required': 'required'}),
            'photo': forms.FileInput(attrs={'class': 'form-control', 'required': 'required'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly', 'required': 'required'}),
            'eye_lens_right': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Right eye measurement', 'required': 'required'}),
            'eye_lens_left': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Left eye measurement', 'required': 'required'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.agent = kwargs.pop('agent', None)
        self.candidate = kwargs.pop('candidate', None)
        super().__init__(*args, **kwargs)
        
        # Set auto-filled values
        if self.agent:
            self.fields['agent_code'].initial = self.agent.agent_code
            # Generate preview of student ID
            from dashboard.models import Student
            student_count = Student.objects.filter(agent=self.agent).count() + 1
            preview_id = f"{self.agent.agent_code}-{student_count:04d}"
            self.fields['student_id_preview'].initial = preview_id
        
        # Make required fields
        required_fields = [
            'full_name', 'date_of_birth', 'permanent_address', 
            'marital_status', 'email', 'phone', 'gender',
            'hobbies', 'motivation', 'height', 'weight',
            'eye_lens_right', 'eye_lens_left', 'blood_group'
        ]
        
        for field_name in required_fields:
            self.fields[field_name].required = True
        
        # Set age field as readonly
        self.fields['age'].widget.attrs['readonly'] = True
        
        # Customize tb_status widget for inline display
        self.fields['tb_status'].widget.attrs.update({'class': 'form-check-input'})
        
        # Set initial values for stage and experience
        self.fields['stage'].required = False
        self.fields['experience'].required = False
      
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Passport dates validation
        issue_date = cleaned_data.get('passport_issue_date')
        expiry_date = cleaned_data.get('passport_expiry_date')
        if issue_date and expiry_date and expiry_date <= issue_date:
            self.add_error('passport_expiry_date', 'Passport expiry date must be after the issue date.')

        # Visa Details conditional validation
        visa_apply_record = cleaned_data.get('visa_apply_record')
        visa_details = cleaned_data.get('visa_details')
        if visa_apply_record == 'yes' and not visa_details:
            self.add_error('visa_details', 'Visa details are mandatory if you have a past visa application record.')

        # Spouse Details conditional validation
        marital_status = cleaned_data.get('marital_status')
        spouse_name = cleaned_data.get('spouse_name')
        spouse_contact = cleaned_data.get('spouse_contact')
        if marital_status == 'married':
            if not spouse_name:
                self.add_error('spouse_name', 'Spouse name is mandatory if you are married.')
            if not spouse_contact:
                self.add_error('spouse_contact', 'Spouse contact is mandatory if you are married.')

        # Ensure default enrolled years are permanent for mandatory schools
        cleaned_data['enrolled_years_primary_school'] = '5'
        cleaned_data['enrolled_years_junior_h_school'] = '5'
        cleaned_data['enrolled_years_higher_s_school'] = '2'

        return cleaned_data

    def clean_email(self):
        """Ensure email uniqueness within the same agent"""
        email = self.cleaned_data.get('email')
        if email and self.agent:
            from dashboard.models import Student
            existing_students = Student.objects.filter(
                agent=self.agent,
                email=email
            )
            if self.instance.pk:
                existing_students = existing_students.exclude(pk=self.instance.pk)
            
            if existing_students.exists():
                raise forms.ValidationError(
                    'A student with this email already exists for this agent.'
                )
        return email
    
    def save(self, commit=True):
        """Save student with auto-generated student ID and agent linkage"""
        from dashboard.models import Student, EducationalHistory, WorkExperience, StudentDocument
        
        student = super().save(commit=False)
        
        # Link with agent
        if self.agent:
            student.agent = self.agent
            # Generate student ID
            student.student_id = self.fields['student_id_preview'].initial
        
        # Save TB status from form field
        tb_status = self.cleaned_data.get('tb_status')
        if tb_status:
            student.tb_status = tb_status
        student.stage = 'candidate_info'  # Default stage for new students
        student.experience = 0  # Default experience
    
        
        if commit:
            student.save()
            self.save_related_data(student)
        
        return student
    
    def save_related_data(self, student):
        """Save educational history, work experience, and documents"""
        from dashboard.models import EducationalHistory, WorkExperience, StudentDocument
        
        # Save Educational History
        education_levels = [
            ('primary_school', 'Primary School'),
            ('junior_h_school', 'Junior H. School'),
            ('higher_s_school', 'Higher S. School'),
            ('college_university', 'College / University'),
            ('graduate_university', 'Graduate University'),
            ('other_school', 'Other School'),
        ]
        
        for level_key, level_name in education_levels:
            school_name = self.cleaned_data.get(f'school_{level_key}')
            if school_name:
                EducationalHistory.objects.update_or_create(
                    student=student,
                    pass_level=level_name,
                    defaults={
                        'school_name': school_name,
                        'admission_year': self.cleaned_data.get(f'admission_year_{level_key}'),
                        'admission_month': self.cleaned_data.get(f'admission_month_{level_key}'),
                        'graduation_year': self.cleaned_data.get(f'graduation_year_{level_key}'),
                        'graduation_month': self.cleaned_data.get(f'graduation_month_{level_key}'),
                        'enrolled_years': self.cleaned_data.get(f'enrolled_years_{level_key}'),
                    }
                )
        
        # Save Work Experience
        for i in range(1, 3):
            company_name = self.cleaned_data.get(f'company_name_{i}')
            if company_name:
                WorkExperience.objects.update_or_create(
                    student=student,
                    company_name=company_name,
                    defaults={
                        'work_type': self.cleaned_data.get(f'work_type_{i}'),
                        'join_date': self.cleaned_data.get(f'join_date_{i}'),
                        'resign_date': self.cleaned_data.get(f'resign_date_{i}'),
                        'working_years': self.cleaned_data.get(f'working_years_{i}'),
                    }
                )
        
        # Save Documents
        document_mapping = {
            'bio_data_file': 'bio_data',
            'id_info_file': 'id_info',
            'educational_doc_file': 'educational_doc',
            'report_file': 'report',
            'other_file': 'other',
        }
        
        for field_name, doc_type in document_mapping.items():
            document_file = self.cleaned_data.get(field_name)
            if document_file:
                StudentDocument.objects.create(
                    student=student,
                    document_type=doc_type,
                    document_file=document_file
                )

class StudentRegistrationForm(StudentForm):
    """Enhanced student registration form with agent validation"""
    
    # This class inherits from StudentForm and adds agent-specific functionality
    # We keep it separate for clarity and future extensions
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Additional initialization for registration form if needed
        if self.agent and not self.instance.pk:
            # Pre-fill some fields if needed
            pass
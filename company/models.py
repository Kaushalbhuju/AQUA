from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class College(models.Model):
    AGREEMENT_TYPES = [
        ('student', 'Student'),
        ('other', 'Other'),
    ]
    
    
    # Basic Information
    college_id = models.CharField(max_length=50, unique=True, verbose_name="College ID")
    college_name_english = models.CharField(max_length=255, verbose_name="College Name (English)")
    college_name_japanese = models.CharField(max_length=255, blank=True, verbose_name="College Name (Japanese)")
    
    # Contact Information
    phone_no = models.CharField(max_length=20, blank=True, verbose_name="Phone No.")
    fax_no = models.CharField(max_length=20, blank=True, verbose_name="Fax No.")
    email = models.EmailField(verbose_name="College Email ID")
    website = models.URLField(blank=True, verbose_name="Home Page")
    
    # Address
    head_office_address = models.TextField(verbose_name="Head Office Address")
    corporate_office_address = models.TextField(blank=True, verbose_name="Corporate Office Address")
    
    # Representative Information
    representative_name = models.CharField(max_length=255, verbose_name="Representative Name")
    representative_mobile = models.CharField(max_length=20, verbose_name="Representative Mobile")
    
    # College Type and Agreement
    college_type = models.CharField(max_length=255, verbose_name="Type of College")
    agreement_date = models.DateField(verbose_name="Agreement Date")
    expire_date = models.DateField(verbose_name="Expire Date")
    agreement_type = models.CharField(max_length=10, choices=AGREEMENT_TYPES, verbose_name="Agreement Type")
    
    # Document URLs
    agreement_doc = models.FileField(upload_to='college_docs/agreements/', blank=True, null=True, verbose_name="Agreement Document")
    interview_pass_doc = models.FileField(upload_to='college_docs/interview_pass/', blank=True, null=True, verbose_name="Interview Pass Document")
    visa_apply_doc = models.FileField(upload_to='college_docs/visa_apply/', blank=True, null=True, verbose_name="Visa Apply Document")
    ceo_visa_doc = models.FileField(upload_to='college_docs/ceo_visa/', blank=True, null=True, verbose_name="CEO Visa Document")
    other_doc = models.FileField(upload_to='college_docs/other/', blank=True, null=True, verbose_name="Other Document")
    pdf_doc_1 = models.FileField(upload_to='college_docs/pdf/', blank=True, null=True, verbose_name="PDF Document 1")
    pdf_doc_2 = models.FileField(upload_to='college_docs/pdf/', blank=True, null=True, verbose_name="PDF Document 2")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.college_id} - {self.college_name_english}"
    
    class Meta:
        verbose_name = "College"
        verbose_name_plural = "Colleges"

class CollegeYearlyData(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='yearly_data')
    year = models.IntegerField(
        validators=[MinValueValidator(2024)],
        verbose_name="Year"
    )
    yearly_student_no = models.PositiveIntegerField(default=0, verbose_name="Yearly Student No.")
    interview_attend_no = models.PositiveIntegerField(default=0, verbose_name="Interview Attend No.")
    interview_pass_no = models.PositiveIntegerField(default=0, verbose_name="Interview Pass No.")
    visa_application_no = models.PositiveIntegerField(default=0, verbose_name="Visa Application No.")
    ceo_success_no = models.PositiveIntegerField(default=0, verbose_name="CEO Success No.")
    
    class Meta:
        verbose_name = "College Yearly Data"
        verbose_name_plural = "College Yearly Data"
        unique_together = ['college', 'year']
    
    def __str__(self):
        return f"{self.college.college_id} - {self.year}"
    
    from django.utils import timezone
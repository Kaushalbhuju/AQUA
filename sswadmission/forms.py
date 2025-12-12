# sswadmission/forms.py - COMPLETE VERSION
from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
from .models import Student, FeePayment, FeeInstallment
from django.db.models import Q

class DateInput(forms.DateInput):
    input_type = 'date'
    
    def __init__(self, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs'].update({'class': 'form-control datepicker'})
        super().__init__(**kwargs)

class StudentSearchForm(forms.Form):
    """Advanced student search form"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, ID, email or phone...',
            'autocomplete': 'off'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Student.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    course = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Course name...'
        })
    )
    
    payment_status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Payments'),
            ('fully_paid', 'Fully Paid'),
            ('not_paid', 'Not Paid'),
            ('partially_paid', 'Partially Paid')
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    date_from = forms.DateField(
        required=False,
        widget=DateInput(attrs={'placeholder': 'From date'})
    )
    
    date_to = forms.DateField(
        required=False,
        widget=DateInput(attrs={'placeholder': 'To date'})
    )

class StudentForm(forms.ModelForm):
    """Enhanced student registration form"""
    class Meta:
        model = Student
        fields = [
            'full_name', 'email', 'phone', 'date_of_birth', 'gender',
            'address', 'city', 'state', 'country', 'pincode',
            'course', 'batch', 'qualification', 'previous_institution',
            'total_fee', 'discount', 'remarks',
            'emergency_contact', 'emergency_contact_name', 'blood_group'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name as per ID',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '10-digit Mobile Number',
                'pattern': '[0-9]{10}',
                'title': 'Please enter a valid 10-digit mobile number',
                'required': True
            }),
            'date_of_birth': DateInput(),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Complete Address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City'
            }),
            'state': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'State'
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Country',
                'value': 'India'
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'PIN Code',
                'pattern': '[0-9]{6}'
            }),
            'course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Course Name',
                'required': True
            }),
            'batch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Batch (e.g., 2024-25)'
            }),
            'qualification': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Highest Qualification'
            }),
            'previous_institution': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Previous Institution'
            }),
            'total_fee': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Total Course Fee',
                'required': True
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Discount if any'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any special remarks...'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency Contact Number'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency Contact Name'
            }),
            'blood_group': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Blood Group (Optional)'
            }),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check if email exists (excluding current instance during update)
        query = Student.objects.filter(email=email)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError("A student with this email already exists.")
        return email
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if len(phone) != 10 or not phone.isdigit():
            raise forms.ValidationError("Please enter a valid 10-digit mobile number.")
        
        # Check if phone exists (excluding current instance during update)
        query = Student.objects.filter(phone=phone)
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError("A student with this phone number already exists.")
        return phone
    
    def clean_discount(self):
        total_fee = self.cleaned_data.get('total_fee', 0)
        discount = self.cleaned_data.get('discount', 0)
        
        if discount > total_fee:
            raise forms.ValidationError("Discount cannot be greater than total fee.")
        
        return discount

class FeePaymentForm(forms.ModelForm):
    """Enhanced fee payment form"""
    class Meta:
        model = FeePayment
        fields = [
            'student', 'amount', 'payment_method', 'payment_date',
            'transaction_id', 'bank_name', 'cheque_number',
            'cheque_date', 'utr_number', 'upi_id',
            'description', 'notes'
        ]
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'required': True,
                'placeholder': 'Amount'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'payment_date': DateInput(attrs={'value': timezone.now().date()}),
            'transaction_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Transaction/Reference ID'
            }),
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank Name'
            }),
            'cheque_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cheque Number'
            }),
            'cheque_date': DateInput(),
            'utr_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UTR/Reference Number'
            }),
            'upi_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UPI ID'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Payment description...'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any notes...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        
        if student:
            self.fields['student'].initial = student
            self.fields['student'].widget = forms.HiddenInput()
            
            # Set max amount based on student's due amount
            max_amount = student.due_amount + Decimal('10000')  # Allow some advance
            self.fields['amount'].validators.append(
                MaxValueValidator(max_amount, f'Maximum allowed amount is ₹{max_amount}')
            )
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise forms.ValidationError("Payment amount must be greater than zero.")
        
        # Check if amount exceeds due amount significantly
        student = self.cleaned_data.get('student')
        if student:
            if amount > student.due_amount + Decimal('10000'):
                raise forms.ValidationError(
                    f"Payment amount exceeds due amount by more than ₹10,000. "
                    f"Maximum allowed: ₹{student.due_amount + Decimal('10000')}"
                )
        
        return amount

class FeeInstallmentForm(forms.ModelForm):
    """Fee installment creation form"""
    class Meta:
        model = FeeInstallment
        fields = ['student', 'installment_number', 'amount', 'due_date', 'notes']
        widgets = {
            'student': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'installment_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'required': True
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'required': True
            }),
            'due_date': DateInput(),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Installment notes...'
            }),
        }

class QuickPaymentForm(forms.Form):
    """Quick payment form for dashboard"""
    student_id = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Student ID',
            'autocomplete': 'off'
        })
    )
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0.01',
            'placeholder': 'Amount'
        })
    )
    payment_method = forms.ChoiceField(
        choices=FeePayment.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Payment description'
        })
    )
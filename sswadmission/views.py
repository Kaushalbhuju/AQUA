# sswadmission/views.py - COMPLETE VERSION
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q, F
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal
from .models import Student, FeePayment, FeeInstallment
from .forms import StudentForm, FeePaymentForm, StudentSearchForm, QuickPaymentForm
from django.core.paginator import Paginator
from django.template.loader import get_template
import json
from django.db import transaction

# ========== DASHBOARD VIEWS ==========

@login_required
def professional_dashboard(request):
    """Professional Admission & Fee Payment Dashboard"""
    # Date filters
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Student Statistics
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status__in=['enrolled', 'approved']).count()
    pending_applications = Student.objects.filter(status='pending').count()
    new_today = Student.objects.filter(created_at__date=today).count()
    new_this_week = Student.objects.filter(created_at__date__gte=week_ago).count()
    
    # Financial Statistics
    financial_stats = Student.objects.aggregate(
        total_fee_expected=Sum('total_fee'),
        total_discount=Sum('discount'),
        total_paid=Sum('paid_amount'),
        total_due=Sum('due_amount')
    )
    
    # Today's Payments
    todays_payments = FeePayment.objects.filter(
        payment_date__date=today,
        status='completed'
    ).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    # Recent Admissions
    recent_admissions = Student.objects.select_related('created_by').order_by('-created_at')[:10]
    
    # Recent Payments
    recent_payments = FeePayment.objects.select_related('student', 'created_by').filter(
        status='completed'
    ).order_by('-payment_date')[:10]
    
    # Fee Due Alerts
    fee_due_alerts = Student.objects.filter(
        status__in=['enrolled', 'approved'],
        due_amount__gt=0
    ).order_by('-due_amount')[:10]
    
    # Payment Methods Summary
    payment_methods_summary = FeePayment.objects.filter(
        status='completed',
        payment_date__date__gte=month_ago
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Quick Payment Form
    quick_payment_form = QuickPaymentForm()
    
    context = {
        'total_students': total_students,
        'active_students': active_students,
        'pending_applications': pending_applications,
        'new_today': new_today,
        'new_this_week': new_this_week,
        'financial_stats': {
            'total_fee_expected': financial_stats['total_fee_expected'] or Decimal('0'),
            'total_discount': financial_stats['total_discount'] or Decimal('0'),
            'total_paid': financial_stats['total_paid'] or Decimal('0'),
            'total_due': financial_stats['total_due'] or Decimal('0'),
            'effective_fee': (financial_stats['total_fee_expected'] or Decimal('0')) - (financial_stats['total_discount'] or Decimal('0')),
            'collection_rate': ((financial_stats['total_paid'] or Decimal('0')) / ((financial_stats['total_fee_expected'] or Decimal('1')) - (financial_stats['total_discount'] or Decimal('0'))) * 100) if (financial_stats['total_fee_expected'] or Decimal('0')) > (financial_stats['total_discount'] or Decimal('0')) else 0,
        },
        'todays_payments': {
            'total': todays_payments['total'] or Decimal('0'),
            'count': todays_payments['count'] or 0,
        },
        'recent_admissions': recent_admissions,
        'recent_payments': recent_payments,
        'fee_due_alerts': fee_due_alerts,
        'payment_methods_summary': payment_methods_summary,
        'quick_payment_form': quick_payment_form,
        'current_date': today,
    }
    
    return render(request, 'sswadmission/dashboard.html', context)

@login_required
def process_quick_payment(request):
    """Process quick payment from dashboard"""
    if request.method == 'POST':
        form = QuickPaymentForm(request.POST)
        if form.is_valid():
            try:
                student_id = form.cleaned_data['student_id']
                amount = form.cleaned_data['amount']
                payment_method = form.cleaned_data['payment_method']
                description = form.cleaned_data['description']
                
                # Find student
                student = get_object_or_404(Student, student_id=student_id)
                
                # Create payment
                payment = FeePayment.objects.create(
                    student=student,
                    amount=amount,
                    payment_method=payment_method,
                    description=description or f"Quick payment via dashboard",
                    status='completed',
                    created_by=request.user
                )
                
                messages.success(request, f'Payment of ₹{amount} recorded for {student.full_name}!')
                return redirect('sswdashboard:professional_dashboard')
                
            except Student.DoesNotExist:
                messages.error(request, f'Student with ID {student_id} not found!')
            except Exception as e:
                messages.error(request, f'Error processing payment: {str(e)}')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    
    return redirect('sswdashboard:professional_dashboard')

# ========== STUDENT MANAGEMENT VIEWS ==========

@login_required
def student_registration(request):
    """Student registration form"""
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    student = form.save(commit=False)
                    student.created_by = request.user
                    student.save()
                    
                    messages.success(request, f'Student {student.full_name} registered successfully! Student ID: {student.student_id}')
                    return redirect('sswdashboard:student_detail', student_id=student.id)
            except Exception as e:
                messages.error(request, f'Error saving student: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StudentForm()
    
    return render(request, 'sswadmission/student_registration.html', {'form': form})

@login_required
def student_list(request):
    """List all students with search and filters"""
    students = Student.objects.all().order_by('-created_at')
    form = StudentSearchForm(request.GET)
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        course = form.cleaned_data.get('course')
        payment_status = form.cleaned_data.get('payment_status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        # Apply filters
        if search:
            students = students.filter(
                Q(full_name__icontains=search) |
                Q(student_id__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(course__icontains=search)
            )
        
        if status:
            students = students.filter(status=status)
        
        if course:
            students = students.filter(course__icontains=course)
        
        if payment_status:
            if payment_status == 'fully_paid':
                students = students.filter(due_amount=0, total_fee__gt=0)
            elif payment_status == 'not_paid':
                students = students.filter(paid_amount=0, total_fee__gt=0)
            elif payment_status == 'partially_paid':
                students = students.filter(due_amount__gt=0, paid_amount__gt=0)
        
        if date_from:
            students = students.filter(created_at__date__gte=date_from)
        
        if date_to:
            students = students.filter(created_at__date__lte=date_to)
    
    # Statistics
    stats = {
        'total': students.count(),
        'pending': students.filter(status='pending').count(),
        'approved': students.filter(status='approved').count(),
        'enrolled': students.filter(status='enrolled').count(),
        'fully_paid': students.filter(due_amount=0, total_fee__gt=0).count(),
        'total_fee': students.aggregate(total=Sum('total_fee'))['total'] or Decimal('0'),
        'total_paid': students.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0'),
    }
    
    # Pagination
    paginator = Paginator(students, 25)
    page = request.GET.get('page')
    students_page = paginator.get_page(page)
    
    context = {
        'students': students_page,
        'form': form,
        'stats': stats,
        'total_count': Student.objects.count(),
    }
    
    return render(request, 'sswadmission/student_list.html', context)

@login_required
def student_detail(request, student_id):
    """View student details"""
    student = get_object_or_404(Student, id=student_id)
    payments = student.fee_payments.all().order_by('-payment_date')
    installments = student.installments.all().order_by('installment_number')
    
    # Payment statistics
    payment_stats = payments.aggregate(
        total_paid=Sum('amount', filter=Q(status='completed')),
        pending_payments=Count('id', filter=Q(status='pending')),
        total_payments=Count('id')
    )
    
    context = {
        'student': student,
        'payments': payments,
        'installments': installments,
        'payment_stats': payment_stats,
        'payment_form': FeePaymentForm(initial={'student': student}),
    }
    
    return render(request, 'sswadmission/student_detail.html', context)

@login_required
def update_student(request, student_id):
    """Update student information"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            try:
                student = form.save()
                messages.success(request, f'Student {student.full_name} updated successfully!')
                return redirect('sswdashboard:student_detail', student_id=student.id)
            except Exception as e:
                messages.error(request, f'Error updating student: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'sswadmission/student_update.html', {'form': form, 'student': student})

@login_required
def change_student_status(request, student_id):
    """Change student status"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Student.STATUS_CHOICES):
            old_status = student.status
            student.status = new_status
            student.remarks = f"{student.remarks}\nStatus changed from {old_status} to {new_status}: {notes}" if notes else f"Status changed from {old_status} to {new_status}"
            student.save()
            
            messages.success(request, f'Student status changed from {old_status} to {new_status}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('sswdashboard:student_detail', student_id=student_id)

# ========== PAYMENT MANAGEMENT VIEWS ==========

@login_required
def add_payment(request, student_id=None):
    """Add payment for a student"""
    if student_id:
        student = get_object_or_404(Student, id=student_id)
        initial = {'student': student}
        half_due = student.due_amount / 2
    else:
        student = None
        initial = {}
        half_due = 0
    
    if request.method == 'POST':
        form = FeePaymentForm(request.POST, student=student)
        if form.is_valid():
            try:
                with transaction.atomic():
                    payment = form.save(commit=False)
                    payment.created_by = request.user
                    
                    # Auto-verify if user has permission
                    if request.user.has_perm('sswadmission.change_feepayment'):
                        payment.status = 'completed'
                        payment.verified_by = request.user
                        payment.verified_at = timezone.now()
                    
                    payment.save()
                    
                    messages.success(request, f'Payment of ₹{payment.amount} recorded successfully! Payment ID: {payment.payment_id}')
                    
                    if student_id:
                        return redirect('sswdashboard:student_detail', student_id=student_id)
                    else:
                        return redirect('sswdashboard:payment_list')
            except Exception as e:
                messages.error(request, f'Error recording payment: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = FeePaymentForm(student=student, initial=initial)
    
    context = {
        'form': form,
        'student': student,
         'half_due': half_due,
    }
    
    return render(request, 'sswadmission/payment_add.html', context)

@login_required
def payment_list(request):
    """List all payments"""
    payments = FeePayment.objects.select_related('student', 'created_by', 'verified_by').all().order_by('-payment_date')
    
    # Filters
    status = request.GET.get('status', '')
    payment_method = request.GET.get('method', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    if status:
        payments = payments.filter(status=status)
    
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    
    if date_from:
        payments = payments.filter(payment_date__date__gte=date_from)
    
    if date_to:
        payments = payments.filter(payment_date__date__lte=date_to)
    
    if search:
        payments = payments.filter(
            Q(payment_id__icontains=search) |
            Q(receipt_number__icontains=search) |
            Q(student__student_id__icontains=search) |
            Q(student__full_name__icontains=search) |
            Q(transaction_id__icontains=search)
        )
    
    # Statistics
    stats = payments.aggregate(
        total_amount=Sum('amount'),
        total_count=Count('id'),
        completed_amount=Sum('amount', filter=Q(status='completed')),
        pending_count=Count('id', filter=Q(status='pending'))
    )
    
    # Check user permissions
    can_verify = request.user.has_perm('sswadmission.change_feepayment')
    
    # Pagination
    paginator = Paginator(payments, 50)
    page = request.GET.get('page')
    payments_page = paginator.get_page(page)
    
    context = {
        'payments': payments_page,
        'stats': stats,
        'status_choices': FeePayment.PAYMENT_STATUS_CHOICES,
        'method_choices': FeePayment.PAYMENT_METHOD_CHOICES,
        'can_verify': can_verify,  # Add this
    }
    
    return render(request, 'sswadmission/payment_list.html', context)

# In your views.py, update the payment_detail function:
@login_required
def payment_detail(request, payment_id):
    """View payment details"""
    payment = get_object_or_404(FeePayment, id=payment_id)
    
    # Check user permissions
    can_verify = request.user.has_perm('sswadmission.change_feepayment')
    
    context = {
        'payment': payment,
        'can_verify': can_verify,  # This is CRITICAL
    }
    
    return render(request, 'sswadmission/payment_detail.html', context)

@login_required
def verify_payment(request, payment_id):
    """Verify a pending payment"""
    payment = get_object_or_404(FeePayment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        if action == 'approve':
            payment.status = 'completed'
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.notes = f"{payment.notes}\nVerified: {notes}" if notes else f"Verified by {request.user.username}"
            payment.save()
            
            messages.success(request, f'Payment {payment.payment_id} verified successfully!')
            
        elif action == 'reject':
            payment.status = 'failed'
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.notes = f"{payment.notes}\nRejected: {notes}" if notes else f"Rejected by {request.user.username}"
            payment.save()
            
            messages.warning(request, f'Payment {payment.payment_id} has been rejected.')
    
    return redirect('sswdashboard:payment_verification_queue')

@login_required
def payment_verification_queue(request):
    """Payment verification queue"""
    pending_payments = FeePayment.objects.filter(
        status='pending'
    ).select_related('student', 'created_by').order_by('payment_date')
    
    # Statistics
    today = timezone.now().date()
    stats = {
        'total_pending': pending_payments.count(),
        'today_pending': pending_payments.filter(created_at__date=today).count(),
        'verified_today': FeePayment.objects.filter(
            status='completed',
            verified_at__date=today
        ).count(),
    }
    
    # Pagination
    paginator = Paginator(pending_payments, 20)
    page = request.GET.get('page')
    payments_page = paginator.get_page(page)
    
    context = {
        'payments': payments_page,
        'stats': stats,
    }
    
    return render(request, 'sswadmission/payment_verification_queue.html', context)

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from weasyprint import HTML
from django.conf import settings
from django.utils.html import escape
from .models import FeePayment


@login_required
def generate_receipt(request, payment_id):
    """Generate payment receipt with two copies"""
    payment = get_object_or_404(FeePayment, id=payment_id)
    
    # Calculate amounts
    vat_amount = float(payment.amount) * 0.13
    total_amount = float(payment.amount) + vat_amount
    
    # Receipt HTML template
    receipt_html = f"""
    <div class="receipt">
        <div class="header">
            <img src="/static/images/logo.png" alt="Logo" class="logo">
            <div class="company-info">
                <div class="reg-numbers">
                    <span>GOV REG: 376328/82/83</span>
                    <span>VAT: 622456452</span>
                </div>
                <h1>AQUA EDUCATION AND TRAINING ACADEMY PVT LTD</h1>
                <p class="address">Lazimpat, Kathmandu Metropolitan City-02, Kathmandu, Nepal</p>
                <p class="contact">Web: www.aquagroupnp.com | Email: ssw.edu.academy@gmail.com</p>
                <div class="receipt-no">Receipt: <strong>{payment.receipt_number}</strong></div>
            </div>
        </div>
        
        <div class="title">CASH RECEIPT</div>
        
        <table class="details">
            <tr><td>Received From</td><td colspan="2">{payment.student.full_name}</td><td rowspan="2" class="memo">MEMO</td></tr>
            <tr><td>Received Contents</td><td colspan="2">{payment.student.course}</td></tr>
            <tr><td colspan="3">Received Amount</td><td>Rs. {payment.amount:,.2f}</td></tr>
            <tr><td colspan="3">Payment Method</td><td>{payment.get_payment_method_display()}</td></tr>
            <tr class="total"><td colspan="3"><strong>TOTAL RECEIVED AMOUNT</strong></td><td><strong>Rs.  {payment.amount:,.2f}</strong></td></tr>
        </table>
        
        <div class="footer">
            <div class="received-by">
                <p><strong>Received By</strong></p>
                <p>Account Department</p>
                <p>Aqua Education And Training Academy Pvt. Ltd</p>
                <p>Tel: +977-01-000000</p>
            </div>
            <div class="signatures">
                <div class="sign-box">
                    <div class="sign-line"></div>
                    <p>Received Date</p>
                    <p>{payment.payment_date.strftime('%d-%m-%Y')}</p>
                </div>
                <div class="sign-box">
                    <div class="sign-line"></div>
                    <p>Received Sign & Stamp</p>
                </div>
            </div>
        </div>
    </div>
    """
    
    # Full page with two copies
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Receipt - {payment.receipt_number}</title>
    <style>
        @page {{ size: A4; margin: 5mm; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; padding: 2mm; }}
        @media print {{
            body {{ padding: 0; }}
            .print-btn {{ display: none; }}
            .receipt-wrapper {{ height: 297mm; }}
            .receipt {{ page-break-inside: avoid; }}
            .cut-line {{ page-break-after: avoid; }}
        }}
        .print-btn {{
            position: fixed; top: 10px; right: 10px; padding: 8px 16px;
            background: #667eea; color: white; border: none; border-radius: 4px;
            cursor: pointer; z-index: 1000;
        }}
        .receipt-wrapper {{ max-width: 210mm; margin: 0 auto; }}
        .receipt {{
            border: 2px solid #000; padding: 4mm; margin: 2mm 0;
            position: relative;
        }}
        .receipt::before {{
            content: ''; position: absolute; top: 0; left: 0; right: 0;
            height: 3px; background: linear-gradient(90deg, #667eea, #764ba2);
        }}
        .cut-line {{
            text-align: center; padding: 3px 0; margin: 2mm 0;
            border-top: 2px dashed #ccc; border-bottom: 2px dashed #ccc;
            font-size: 9px; color: #666;
        }}
        .header {{ display: flex; gap: 8px; margin-bottom: 5px;
                  padding-bottom: 5px; border-bottom: 1px solid #ccc; }}
        .logo {{ width: 70px; height: 55px; border: 1px solid #ccc; padding: 2px; }}
        .company-info {{ flex: 1; }}
        .reg-numbers {{ display: flex; justify-content: space-between;
                       font-size: 9px; font-weight: bold; color: #d00;
                       margin-bottom: 3px; }}
        h1 {{ color: #1e40af; font-size: 16px; margin: 3px 0; }}
        .address {{ font-size: 11px; font-weight: bold; margin: 2px 0; }}
        .contact {{ font-size: 9px; color: #666; margin: 2px 0; }}
        .receipt-no {{ font-size: 10px; margin-top: 3px; }}
        .title {{
            background: #667eea; color: white; text-align: center;
            padding: 8px; font-size: 18px; font-weight: bold;
            margin: 8px 0; border-radius: 4px;
        }}
        .details {{
            width: 100%; border-collapse: collapse; margin: 10px 0;
            border: 1px solid #000; font-size: 11px;
        }}
        .details td {{ border: 1px solid #000; padding: 6px 8px; }}
        .details td:first-child {{ background: #f7fafc; font-weight: bold; }}
        .memo {{ background: #fef3c7; text-align: center; font-weight: bold;
                color: #92400e; border: 2px solid #f59e0b !important; }}
        .total td {{ background: #dbeafe !important; font-weight: bold; }}
        .footer {{
            display: flex; justify-content: space-between;
            margin-top: 15px; padding-top: 10px; border-top: 1px solid #ccc;
            font-size: 10px;
        }}
        .signatures {{ display: flex; gap: 20px; }}
        .sign-box {{ text-align: center; }}
        .sign-line {{ width: 140px; height: 40px; border-bottom: 1px solid #000;
                     margin-bottom: 4px; }}
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">🖨️ Print</button>
    <div class="receipt-wrapper">
        {receipt_html}
        <div class="cut-line">✂️ Office Copy Above - Customer Copy Below ✂️</div>
        {receipt_html}
    </div>
</body>
</html>
"""
    
    return HttpResponse(html)
# ========== INSTALLMENT MANAGEMENT ==========

@login_required
def create_installments(request, student_id):
    """Create installment plan for student"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            num_installments = int(request.POST.get('num_installments', 1))
            start_date = request.POST.get('start_date', timezone.now().date())
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
            # Clear existing installments
            student.installments.all().delete()
            
            # Calculate installment amount
            effective_fee = student.total_fee - student.discount
            if effective_fee > 0:
                installment_amount = effective_fee / num_installments
                
                # Create installments
                for i in range(1, num_installments + 1):
                    due_date = start_date + timedelta(days=30 * (i - 1))
                    FeeInstallment.objects.create(
                        student=student,
                        installment_number=i,
                        amount=installment_amount,
                        due_date=due_date,
                        status='pending',
                        notes=f"Installment {i} of {num_installments}"
                    )
                
                messages.success(request, f'{num_installments} installments created successfully!')
            else:
                messages.error(request, 'No fee amount to create installments')
                
        except Exception as e:
            messages.error(request, f'Error creating installments: {str(e)}')
    
    return redirect('sswdashboard:student_detail', student_id=student_id)

@login_required
def mark_installment_paid(request, installment_id):
    """Mark installment as paid"""
    installment = get_object_or_404(FeeInstallment, id=installment_id)
    
    if request.method == 'POST':
        try:
            installment.status = 'paid'
            installment.paid_date = timezone.now().date()
            installment.save()
            
            messages.success(request, f'Installment {installment.installment_number} marked as paid!')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return redirect('sswdashboard:student_detail', student_id=installment.student.id)

# ========== REPORTS & ANALYTICS ==========

@login_required
def financial_reports(request):
    """Financial reports"""
    # Date filters
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    
    # Parse dates
    try:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
    except:
        date_from_obj = timezone.now().date() - timedelta(days=30)
        date_to_obj = timezone.now().date()
    
    # Get payments
    payments = FeePayment.objects.filter(
        status='completed',
        payment_date__date__range=[date_from_obj, date_to_obj]
    )
    
    # Group by date
    daily_summary = payments.extra({'date': "date(payment_date)"}).values('date').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('date')
    
    # Calculate additional fields for daily summary
    daily_summary_list = []
    total_collected = Decimal('0')
    
    for day in daily_summary:
        total = day['total'] or Decimal('0')
        count = day['count'] or 0
        avg_amount = total / count if count > 0 else Decimal('0')
        
        daily_summary_list.append({
            'date': day['date'],
            'total': total,
            'count': count,
            'avg_amount': avg_amount,
        })
        total_collected += total
    
    # Group by payment method
    method_summary = payments.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Calculate percentages for method summary
    method_summary_list = []
    for method in method_summary:
        total = method['total'] or Decimal('0')
        count = method['count'] or 0
        avg_amount = total / count if count > 0 else Decimal('0')
        percentage = (total / total_collected * 100) if total_collected > 0 else 0
        
        method_summary_list.append({
            'payment_method': method['payment_method'],
            'total': total,
            'count': count,
            'avg_amount': avg_amount,
            'percentage': percentage,
        })
    
    # Group by student status
    student_payments = Student.objects.filter(
        fee_payments__payment_date__date__range=[date_from_obj, date_to_obj],
        fee_payments__status='completed'
    ).values('status').annotate(
        total_paid=Sum('fee_payments__amount'),
        student_count=Count('id', distinct=True)
    ).order_by('status')
    
    # Calculate averages for student payments
    student_payments_list = []
    for sp in student_payments:
        total_paid = sp['total_paid'] or Decimal('0')
        student_count = sp['student_count'] or 0
        avg_per_student = total_paid / student_count if student_count > 0 else Decimal('0')
        
        student_payments_list.append({
            'status': sp['status'],
            'total_paid': total_paid,
            'student_count': student_count,
            'avg_per_student': avg_per_student,
        })
    
    # Summary statistics
    summary = {
        'total_collected': total_collected,
        'total_transactions': payments.count(),
        'avg_payment': payments.aggregate(avg=Avg('amount'))['avg'] or Decimal('0'),
        'unique_students': payments.values('student').distinct().count(),
    }
    
    # Calculate day average for comparison
    day_avg = total_collected / len(daily_summary_list) if daily_summary_list else Decimal('0')
    
    context = {
        'date_from': date_from_obj,
        'date_to': date_to_obj,
        'daily_summary': daily_summary_list,
        'method_summary': method_summary_list,
        'student_payments': student_payments_list,
        'summary': summary,
        'day_avg': day_avg,
        'days_count': (date_to_obj - date_from_obj).days + 1,
        'total_collected': total_collected,
        'total_transactions': payments.count(),
        'avg_payment': summary['avg_payment'],
    }
    
    return render(request, 'sswadmission/financial_reports.html', context)

@login_required
def admission_statistics(request):
    """Admission statistics report"""
    # Date range
    period = request.GET.get('period', 'month')
    today = timezone.now().date()
    
    if period == 'today':
        start_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'month':
        start_date = today - timedelta(days=30)
    elif period == 'quarter':
        start_date = today - timedelta(days=90)
    elif period == 'year':
        start_date = today - timedelta(days=365)
    else:
        start_date = today - timedelta(days=30)
    
    # Student statistics
    total_students = Student.objects.count()
    students_period = Student.objects.filter(created_at__date__gte=start_date)
    
    # Status distribution
    status_distribution = Student.objects.values('status').annotate(
        count=Count('id'),
        percentage=Count('id') * 100.0 / total_students if total_students > 0 else 0
    ).order_by('-count')
    
    # Course distribution
    course_distribution = Student.objects.values('course').annotate(
        count=Count('id')
    ).order_by('-count')[:10]  # Top 10 courses
    
    # Monthly trend (last 6 months)
    monthly_trend = []
    for i in range(5, -1, -1):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        month_count = Student.objects.filter(
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).count()
        
        month_payments = FeePayment.objects.filter(
            payment_date__date__gte=month_start,
            payment_date__date__lte=month_end,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        monthly_trend.append({
            'month': month_start.strftime('%b %Y'),
            'admissions': month_count,
            'revenue': month_payments,
        })
    
    # Payment status distribution
    payment_status_stats = {
        'fully_paid': Student.objects.filter(due_amount=0, total_fee__gt=0).count(),
        'partially_paid': Student.objects.filter(due_amount__gt=0, paid_amount__gt=0).count(),
        'not_paid': Student.objects.filter(paid_amount=0, total_fee__gt=0).count(),
        'no_fee': Student.objects.filter(total_fee=0).count(),
    }
    
    context = {
        'period': period,
        'start_date': start_date,
        'today': today,
        'total_students': total_students,
        'students_period': students_period.count(),
        'status_distribution': status_distribution,
        'course_distribution': course_distribution,
        'monthly_trend': monthly_trend,
        'payment_status_stats': payment_status_stats,
    }
    
    return render(request, 'sswadmission/admission_statistics.html', context)

# ========== AJAX VIEWS ==========

@login_required
def ajax_dashboard_metrics(request):
    """AJAX endpoint for dashboard metrics"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        metrics = {
            'total_students': Student.objects.count(),
            'active_students': Student.objects.filter(status__in=['enrolled', 'approved']).count(),
            'today_admissions': Student.objects.filter(created_at__date=today).count(),
            'today_collection': FeePayment.objects.filter(
                payment_date__date=today,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0,
            'pending_payments': FeePayment.objects.filter(status='pending').count(),
            'weekly_admissions': Student.objects.filter(created_at__date__gte=week_ago).count(),
            'weekly_collection': FeePayment.objects.filter(
                payment_date__date__gte=week_ago,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or 0,
        }
        
        return JsonResponse(metrics)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def ajax_payment_chart_data(request):
    """AJAX endpoint for payment chart data"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        days = int(request.GET.get('days', 30))
        date_from = timezone.now() - timedelta(days=days)
        
        data = FeePayment.objects.filter(
            payment_date__gte=date_from,
            status='completed'
        ).extra({'date': "date(payment_date)"}).values('date').annotate(
            amount=Sum('amount'),
            count=Count('id')
        ).order_by('date')
        
        chart_data = {
            'labels': [item['date'].strftime('%Y-%m-%d') for item in data],
            'amounts': [float(item['amount']) for item in data],
            'counts': [item['count'] for item in data],
        }
        
        return JsonResponse(chart_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def ajax_student_stats(request):
    """AJAX endpoint for student statistics"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        stats = {
            'status_distribution': list(Student.objects.values('status').annotate(
                count=Count('id')
            ).order_by('status')),
            'course_distribution': list(Student.objects.values('course').annotate(
                count=Count('id')
            ).filter(course__isnull=False).exclude(course='').order_by('-count')[:5]),
            'payment_status': {
                'fully_paid': Student.objects.filter(due_amount=0, total_fee__gt=0).count(),
                'partially_paid': Student.objects.filter(due_amount__gt=0, paid_amount__gt=0).count(),
                'not_paid': Student.objects.filter(paid_amount=0, total_fee__gt=0).count(),
            }
        }
        
        return JsonResponse(stats)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

# ========== UTILITY FUNCTIONS ==========

def get_student_fee_summary(student):
    """Get student fee summary"""
    effective_fee = student.total_fee - student.discount
    
    return {
        'total_fee': student.total_fee,
        'discount': student.discount,
        'effective_fee': effective_fee,
        'paid_amount': student.paid_amount,
        'due_amount': student.due_amount,
        'percentage_paid': (student.paid_amount / effective_fee * 100) if effective_fee > 0 else 0,
        'status': student.get_payment_status_display(),
    }

def get_monthly_revenue(year=None, month=None):
    """Get monthly revenue data"""
    if not year:
        year = timezone.now().year
    
    monthly_data = []
    for m in range(1, 13):
        month_start = date(year, m, 1)
        if m == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, m + 1, 1) - timedelta(days=1)
        
        revenue = FeePayment.objects.filter(
            payment_date__date__range=[month_start, month_end],
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'revenue': revenue,
        })
    
    return monthly_data
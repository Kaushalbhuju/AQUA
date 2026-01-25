

# coe_visa/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from dashboard.models import Student  # Import Student from dashboard
from .models import COETracking, VisaTracking 

from .forms import VisaTrackingForm # Import your models from coe_visa
from django.utils import timezone

@login_required
def seoandvisa_dashboard(request):
    """Simple dashboard showing approved students with COE/Visa status"""
    
    # Get all approved students
    approved_students = Student.objects.filter(status='approved').order_by('-created_at')
    
    # Get statistics
    total_students = approved_students.count()
    
    coe_stats = {
        'total': COETracking.objects.count(),
        'processing': COETracking.objects.filter(status='processing').count(),
        'approved': COETracking.objects.filter(status='approved').count(),
        'issued': COETracking.objects.filter(status='issued').count(),
    }
    
    visa_stats = {
        'total': VisaTracking.objects.count(),
        'applied': VisaTracking.objects.filter(status='applied').count(),
        'processing': VisaTracking.objects.filter(status='processing').count(),
        'approved': VisaTracking.objects.filter(status='approved').count(),
    }
    
    context = {
        'students': approved_students,
        'total_students': total_students,
        'coe_stats': coe_stats,
        'visa_stats': visa_stats,
    }
    
    return render(request, 'seoandvisa_dashboard.html', context)

@login_required
def update_coe_status(request, student_id):
    """Update COE status for a student"""
    student = get_object_or_404(Student, id=student_id, status='approved')
    
    # Get or create COE tracking record
    coe_tracking, created = COETracking.objects.get_or_create(student=student)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        coe_number = request.POST.get('coe_number')
        applied_date = request.POST.get('applied_date')
        issued_date = request.POST.get('issued_date')
        notes = request.POST.get('notes')
        
        if new_status:
            coe_tracking.status = new_status
        
        if coe_number:
            coe_tracking.coe_number = coe_number
        
        if applied_date:
            coe_tracking.applied_date = applied_date
        
        if issued_date:
            coe_tracking.issued_date = issued_date
        
        if notes:
            coe_tracking.notes = notes
        
        coe_tracking.save()
        messages.success(request, f'COE status updated for {student.full_name}')
        return redirect('coe_visa:seoandvisa_dashboard')
    
    return render(request, 'update_coe_status.html', {
        'student': student,
        'coe_tracking': coe_tracking,
    })



def update_visa_status(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    # Get or create VisaTracking
    visa_tracking, created = VisaTracking.objects.get_or_create(student=student)
    
    if request.method == 'POST':
        form = VisaTrackingForm(request.POST, request.FILES, instance=visa_tracking)
        
        if form.is_valid():
            form.save()
            messages.success(request, f'Visa status updated successfully for {student.full_name}!')
            
            # FIX 1: Use the correct URL name with namespace
            return redirect('coe_visa:update_visa_status', student_id=student.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    
    else:
        form = VisaTrackingForm(instance=visa_tracking)
    
    return render(request, 'update_visa_status.html', {
        'student': student,
        'visa_tracking': visa_tracking,
        'form': form,
    })
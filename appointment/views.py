# appointment/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, TemplateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from django.db.models import Count, Q, Sum, F
from django.db import models
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import json
import csv

from .models import Appointment, AppointmentSlot
from .forms import AppointmentForm, DateFilterForm, AppointmentSlotForm

# ================ UTILITY FUNCTIONS ================

def is_admin(user):
    """Check if user is admin/staff"""
    return user.is_authenticated and user.is_staff

# ================ PUBLIC VIEWS ================

class AppointmentCreateView(CreateView):
    """View for creating new appointments"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/book_appointment.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slot_id = self.request.GET.get('slot_id')
        if slot_id:
            try:
                slot = AppointmentSlot.objects.get(id=slot_id)
                context['selected_slot'] = slot
                # Calculate slot duration
                duration = (slot.end_time - slot.start_time).total_seconds() / 60
                context['slot_duration'] = int(duration)
            except AppointmentSlot.DoesNotExist:
                pass
        return context
    
    def form_valid(self, form):
        # Set the appointment slot from GET parameter or form data
        slot_id = self.request.GET.get('slot_id') or form.cleaned_data.get('appointment_slot')
        if slot_id:
            form.instance.appointment_slot_id = slot_id
        
        # Save the form to get the appointment object
        self.object = form.save()
        
        # Update slot booked count if slot exists
        if self.object.appointment_slot:
            slot = self.object.appointment_slot
            slot.booked_count = min(slot.booked_count + 1, slot.max_capacity)
            slot.save()
        
        # Store the appointment ID in session for confirmation page
        self.request.session['last_appointment_id'] = self.object.id
        
        # Don't use messages here as we redirect to confirmation page
        return redirect(reverse('appointment_confirmation'))

class AppointmentSlotListView(ListView):
    """View for displaying available appointment slots"""
    model = AppointmentSlot
    template_name = 'appointments/available_slots.html'
    context_object_name = 'slots'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = AppointmentSlot.objects.filter(
            is_available=True,
            start_time__gte=timezone.now()
        ).order_by('start_time')
        
        # Filter by date if provided
        date_filter = self.request.GET.get('date')
        if date_filter:
            queryset = queryset.filter(start_time__date=date_filter)
        
        # Filter by availability
        available_only = self.request.GET.get('available_only')
        if available_only == 'true':
            queryset = queryset.filter(booked_count__lt=F('max_capacity'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_filter_form'] = DateFilterForm(self.request.GET or None)
        context['selected_date'] = self.request.GET.get('date', '')
        
        # Add today's date for default
        context['today'] = timezone.now().date()
        
        return context

def get_available_slots_api(request):
    """API endpoint for fetching available slots (for AJAX)"""
    date = request.GET.get('date')
    slots = AppointmentSlot.objects.filter(
        is_available=True,
        start_time__gte=timezone.now()
    )
    
    if date:
        slots = slots.filter(start_time__date=date)
    
    slots_data = [
        {
            'id': slot.id,
            'date': slot.formatted_date,
            'time': slot.formatted_time,
            'end_time': slot.end_time.strftime('%H:%M'),
            'is_full': slot.is_full,
            'available_spots': slot.max_capacity - slot.booked_count,
            'max_capacity': slot.max_capacity,
            'booked_count': slot.booked_count,
        }
        for slot in slots.order_by('start_time')
    ]
    
    return JsonResponse({'slots': slots_data})

class AppointmentConfirmationView(TemplateView):
    """View for displaying appointment confirmation"""
    template_name = 'appointments/confirmation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        appointment = None
        
        # 1. Try to get from URL parameter (confirmation code)
        confirmation_code = self.request.GET.get('code')
        if confirmation_code:
            try:
                appointment = Appointment.objects.get(confirmation_code=confirmation_code)
            except Appointment.DoesNotExist:
                pass
        
        # 2. If not in URL, check session (from form submission)
        if not appointment:
            appointment_id = self.request.session.get('last_appointment_id')
            if appointment_id:
                try:
                    appointment = Appointment.objects.get(id=appointment_id)
                    # Clear session after use
                    if 'last_appointment_id' in self.request.session:
                        del self.request.session['last_appointment_id']
                except Appointment.DoesNotExist:
                    pass
        
        # 3. Add appointment to context if found
        if appointment:
            context['appointment'] = appointment
            
            # Calculate slot duration
            if appointment.appointment_slot:
                duration = (appointment.appointment_slot.end_time - 
                           appointment.appointment_slot.start_time).total_seconds() / 60
                context['slot_duration'] = int(duration)
        
        return context

def appointment_detail_public(request, confirmation_code):
    """Public view for appointment details using confirmation code"""
    appointment = get_object_or_404(Appointment, confirmation_code=confirmation_code)
    
    context = {
        'appointment': appointment,
    }
    
    if appointment.appointment_slot:
        duration = (appointment.appointment_slot.end_time - 
                   appointment.appointment_slot.start_time).total_seconds() / 60
        context['slot_duration'] = int(duration)
    
    return render(request, 'appointments/appointment_detail_public.html', context)

# ================ ADMIN VIEWS ================

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require admin access"""
    def test_func(self):
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        messages.error(self.request, "You need to be an admin to access this page.")
        return redirect('available_slots')

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """
    Main dashboard view for admin
    Shows stats, recent appointments, calendar, and analytics
    """
    # Get date filters
    today = timezone.now().date()
    selected_date = request.GET.get('date', today.strftime('%Y-%m-%d'))
    
    # Parse selected date
    try:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except:
        selected_date = today
    
    # ================ STATISTICS ================
    # Appointment stats
    total_appointments = Appointment.objects.count()
    confirmed_appointments = Appointment.objects.filter(is_confirmed=True).count()
    pending_appointments = Appointment.objects.filter(is_confirmed=False).count()
    appointments_today = Appointment.objects.filter(date=today).count()
    
    # Slot stats
    available_slots = AppointmentSlot.objects.filter(
        is_available=True, 
        start_time__gte=timezone.now()
    ).count()
    
    booked_slots = AppointmentSlot.objects.filter(booked_count__gt=0).count()
    
    # ================ APPOINTMENT DATA ================
    # Recent appointments (last 20)
    recent_appointments = Appointment.objects.select_related('appointment_slot').order_by('-created_at')[:20]
    
    # Today's appointments
    todays_appointments = Appointment.objects.filter(date=today).order_by('time')
    
    # Upcoming appointments (next 7 days)
    next_week = today + timedelta(days=7)
    upcoming_appointments = Appointment.objects.filter(
        date__range=[today, next_week]
    ).order_by('date', 'time')[:10]
    
    # ================ ANALYTICS DATA ================
    # Appointment distribution by purpose
    purpose_distribution = Appointment.objects.values('appointment_aim').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Top companies by appointment count
    top_companies = Appointment.objects.values('company_name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Appointments by date for calendar
    start_date = today.replace(day=1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    appointments_by_date = {}
    appointments_in_range = Appointment.objects.filter(
        date__range=[start_date, end_date]
    ).values('date').annotate(count=Count('id'))
    
    for item in appointments_in_range:
        date_str = item['date'].strftime('%Y-%m-%d')
        appointments_by_date[date_str] = item['count']
    
    # Daily appointment trends (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    daily_trends = Appointment.objects.filter(
        date__range=[thirty_days_ago, today]
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Convert daily trends to lists for chart
    trend_dates = [item['date'].strftime('%Y-%m-%d') for item in daily_trends]
    trend_counts = [item['count'] for item in daily_trends]
    
    # ================ CALCULATIONS ================
    # Calculate percentages
    if total_appointments > 0:
        confirmed_percentage = round((confirmed_appointments / total_appointments * 100), 1)
        pending_percentage = round((pending_appointments / total_appointments * 100), 1)
    else:
        confirmed_percentage = pending_percentage = 0
    
    # Average appointments per day (handle empty database)
    try:
        # Check if there are any appointments
        earliest_appointment = Appointment.objects.earliest('created_at')
        days_count = (today - earliest_appointment.created_at.date()).days + 1
        avg_daily_appointments = round(total_appointments / max(days_count, 1), 1)
    except Appointment.DoesNotExist:
        # No appointments yet
        avg_daily_appointments = 0
    except Exception as e:
        # Handle any other errors
        avg_daily_appointments = 0
    
    # ================ CONTEXT ================
    context = {
        'today': today,
        'selected_date': selected_date,
        
        # Stats
        'stats': {
            'total_appointments': total_appointments,
            'confirmed_appointments': confirmed_appointments,
            'pending_appointments': pending_appointments,
            'appointments_today': appointments_today,
            'available_slots': available_slots,
            'booked_slots': booked_slots,
            'confirmed_percentage': confirmed_percentage,
            'pending_percentage': pending_percentage,
            'avg_daily_appointments': avg_daily_appointments,
        },
        
        # Appointments
        'recent_appointments': recent_appointments,
        'todays_appointments': todays_appointments,
        'upcoming_appointments': upcoming_appointments,
        
        # Analytics
        'purpose_distribution': purpose_distribution,
        'top_companies': top_companies,
        
        # Chart data - handle empty data
        'purpose_labels': json.dumps([item['appointment_aim'] for item in purpose_distribution]),
        'purpose_data': json.dumps([item['count'] for item in purpose_distribution]),
        'trend_dates': json.dumps(trend_dates),
        'trend_counts': json.dumps(trend_counts),
        
        # Calendar data
        'appointments_by_date': json.dumps(appointments_by_date),
        
        # For template tags
        'appointments_by_date_dict': appointments_by_date,
        'daily_trends': list(daily_trends),
        
        # Flag for empty database
        'has_appointments': total_appointments > 0,
        'has_slots': available_slots > 0,
    }
    
    return render(request, 'appointments/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def appointment_list(request):
    """
    Full list of appointments with filtering and pagination
    """
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status')
    search = request.GET.get('search', '')
    purpose = request.GET.get('purpose')
    
    # Start with all appointments
    appointments = Appointment.objects.all().order_by('-date', '-time')
    
    # Apply filters
    if date_from:
        appointments = appointments.filter(date__gte=date_from)
    if date_to:
        appointments = appointments.filter(date__lte=date_to)
    if status == 'confirmed':
        appointments = appointments.filter(is_confirmed=True)
    elif status == 'pending':
        appointments = appointments.filter(is_confirmed=False)
    if purpose:
        appointments = appointments.filter(appointment_aim=purpose)
    
    # Apply search
    if search:
        appointments = appointments.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(company_name__icontains=search) |
            Q(confirmation_code__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(appointments, 25)  # 25 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get purposes for filter dropdown
    purposes = Appointment.APPOINTMENT_AIMS
    
    context = {
        'page_obj': page_obj,
        'appointments': page_obj.object_list,
        'search': search,
        'date_from': date_from or '',
        'date_to': date_to or '',
        'status': status or '',
        'purpose': purpose or '',
        'purposes': purposes,
        'total_count': appointments.count(),
    }
    
    return render(request, 'appointments/appointment_list.html', context)

@login_required
def appointment_detail_admin(request, pk):
    """Admin view for appointment details using database ID"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Get related appointments (same company)
    related_appointments = Appointment.objects.filter(
        company_name=appointment.company_name
    ).exclude(pk=pk).order_by('-date')[:5]
    
    context = {
        'appointment': appointment,
        'related_appointments': related_appointments,
    }
    
    return render(request, 'appointments/appointment_detail_admin.html', context)

@login_required
@user_passes_test(is_admin)
def appointment_detail_api(request, appointment_id):
    """API endpoint to get appointment details"""
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    data = {
        'id': appointment.id,
        'name': appointment.name,
        'email': appointment.email,
        'phone': appointment.phone,
        'address': appointment.address,
        'company_name': appointment.company_name,
        'position': appointment.position,
        'appointment_aim': appointment.get_appointment_aim_display(),
        'date': appointment.date.strftime('%Y-%m-%d'),
        'time': appointment.time.strftime('%H:%M'),
        'is_confirmed': appointment.is_confirmed,
        'message': appointment.message,
        'confirmation_code': appointment.confirmation_code,
        'created_at': appointment.created_at.strftime('%Y-%m-%d %H:%M'),
    }
    
    return JsonResponse(data)

@login_required
@user_passes_test(is_admin)
@require_POST
def confirm_appointment(request, appointment_id):
    """Confirm an appointment and redirect back to dashboard"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        if appointment.is_confirmed:
            messages.warning(request, f"Appointment #{appointment_id} is already confirmed!")
        else:
            appointment.is_confirmed = True
            appointment.save()
            messages.success(request, f"Appointment #{appointment_id} confirmed successfully!")
            
    except Appointment.DoesNotExist:
        messages.error(request, f"Appointment #{appointment_id} not found!")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    # Redirect back to dashboard
    return redirect('dashboard')

@login_required
@user_passes_test(is_admin)
@require_POST
def cancel_appointment(request, appointment_id):
    """Cancel an appointment and redirect back to dashboard"""
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        confirmation_code = appointment.confirmation_code
        
        # Update slot if needed
        if appointment.appointment_slot:
            appointment.appointment_slot.booked_count = max(
                0, appointment.appointment_slot.booked_count - 1
            )
            appointment.appointment_slot.save()
        
        # Delete appointment
        appointment.delete()
        messages.success(request, f"Appointment #{appointment_id} ({confirmation_code}) cancelled!")
        
    except Appointment.DoesNotExist:
        messages.error(request, f"Appointment #{appointment_id} not found!")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    # Redirect back to dashboard
    return redirect('dashboard')

# ================ SLOT MANAGEMENT VIEWS ================

@login_required
@user_passes_test(is_admin)
def slot_management(request):
    """Simple slot management view"""
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    available_only = request.GET.get('available_only')
    
    # Get slots
    slots = AppointmentSlot.objects.all().order_by('start_time')
    
    # Apply filters
    if date_from:
        slots = slots.filter(start_time__date__gte=date_from)
    if date_to:
        slots = slots.filter(start_time__date__lte=date_to)
    if available_only == '1':
        slots = slots.filter(is_available=True)
    elif available_only == '0':
        slots = slots.filter(is_available=False)
    
    # Simple grouping by date
    from collections import defaultdict
    slots_by_date = defaultdict(list)
    for slot in slots:
        date_str = slot.start_time.strftime('%Y-%m-%d')
        slots_by_date[date_str].append(slot)
    
    # Convert to regular dict for template
    slots_by_date = dict(slots_by_date)
    
    # Prepare JSON for calendar
    import json
    slots_by_date_json = {}
    for date_str, slot_list in slots_by_date.items():
        slots_by_date_json[date_str] = len(slot_list)
    
    context = {
        'slots_by_date': slots_by_date,
        'slots_by_date_json': json.dumps(slots_by_date_json),
        'date_from': date_from or '',
        'date_to': date_to or '',
        'available_only': available_only or '',
        'total_slots': slots.count(),
        'available_slots': slots.filter(is_available=True).count(),
        'booked_slots': slots.filter(booked_count__gt=0).count(),
        'current_month': timezone.now(),
    }
    
    return render(request, 'appointments/slot_management.html', context)

@login_required
@user_passes_test(is_admin)
def create_slot(request):
    """Create a new appointment slot"""
    if request.method == 'POST':
        form = AppointmentSlotForm(request.POST)
        if form.is_valid():
            slot = form.save()
            messages.success(request, f'Slot created for {slot.start_time.strftime("%Y-%m-%d %H:%M")}')
            return redirect('slot_management')
    else:
        form = AppointmentSlotForm()
    
    context = {
        'form': form,
        'title': 'Create New Slot',
    }
    
    return render(request, 'appointments/slot_form.html', context)

@login_required
@user_passes_test(is_admin)
def edit_slot(request, pk):
    """Edit an existing appointment slot"""
    slot = get_object_or_404(AppointmentSlot, pk=pk)
    
    if request.method == 'POST':
        form = AppointmentSlotForm(request.POST, instance=slot)
        if form.is_valid():
            slot = form.save()
            messages.success(request, f'Slot updated for {slot.start_time.strftime("%Y-%m-%d %H:%M")}')
            return redirect('slot_management')
    else:
        form = AppointmentSlotForm(instance=slot)
    
    context = {
        'form': form,
        'title': 'Edit Slot',
        'slot': slot,
    }
    
    return render(request, 'appointments/slot_form.html', context)

@login_required
@user_passes_test(is_admin)
def delete_slot(request, pk):
    """Delete an appointment slot"""
    slot = get_object_or_404(AppointmentSlot, pk=pk)
    
    if request.method == 'POST':
        slot_time = slot.start_time.strftime("%Y-%m-%d %H:%M")
        slot.delete()
        messages.success(request, f'Slot {slot_time} deleted')
        return redirect('slot_management')
    
    context = {
        'slot': slot,
    }
    
    return render(request, 'appointments/slot_confirm_delete.html', context)

@login_required
@user_passes_test(is_admin)
def toggle_slot_availability(request, pk):
    """Toggle slot availability"""
    slot = get_object_or_404(AppointmentSlot, pk=pk)
    slot.is_available = not slot.is_available
    slot.save()
    
    status = "available" if slot.is_available else "unavailable"
    messages.success(request, f'Slot marked as {status}')
    
    return redirect('slot_management')

# ================ EXPORT VIEWS ================

@login_required
@user_passes_test(is_admin)
def export_appointments(request):
    """Export appointments to CSV"""
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    status = request.GET.get('status')
    purpose = request.GET.get('purpose')
    
    # Filter appointments
    appointments = Appointment.objects.all()
    
    if date_from:
        appointments = appointments.filter(date__gte=date_from)
    if date_to:
        appointments = appointments.filter(date__lte=date_to)
    if status == 'confirmed':
        appointments = appointments.filter(is_confirmed=True)
    elif status == 'pending':
        appointments = appointments.filter(is_confirmed=False)
    if purpose:
        appointments = appointments.filter(appointment_aim=purpose)
    
    # Selected IDs
    selected_ids = request.GET.get('ids', '').split(',')
    if selected_ids and selected_ids[0]:
        appointments = appointments.filter(id__in=selected_ids)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="appointments_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    
    # Write UTF-8 BOM for Excel compatibility
    response.write('\ufeff'.encode('utf8'))
    
    # Write header
    writer.writerow([
        'Confirmation Code', 'Name', 'Email', 'Phone', 'Company', 'Position',
        'Purpose', 'Date', 'Time', 'Status', 'Created At', 'Address', 'Message'
    ])
    
    # Write data
    for appointment in appointments:
        writer.writerow([
            appointment.confirmation_code,
            appointment.name,
            appointment.email,
            appointment.phone,
            appointment.company_name,
            appointment.position,
            appointment.get_appointment_aim_display(),
            appointment.date.strftime('%Y-%m-%d'),
            appointment.time.strftime('%H:%M'),
            'Confirmed' if appointment.is_confirmed else 'Pending',
            appointment.created_at.strftime('%Y-%m-%d %H:%M'),
            appointment.address.replace('\n', ' ') if appointment.address else '',
            appointment.message.replace('\n', ' ') if appointment.message else '',
        ])
    
    return response

@login_required
@user_passes_test(is_admin)
def export_slots(request):
    """Export appointment slots to CSV"""
    slots = AppointmentSlot.objects.all().order_by('start_time')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="slots_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    response.write('\ufeff'.encode('utf8'))
    
    # Write header
    writer.writerow([
        'Start Time', 'End Time', 'Available', 'Max Capacity', 
        'Booked Count', 'Available Spots', 'Is Full'
    ])
    
    # Write data
    for slot in slots:
        writer.writerow([
            slot.start_time.strftime('%Y-%m-%d %H:%M'),
            slot.end_time.strftime('%Y-%m-%d %H:%M'),
            'Yes' if slot.is_available else 'No',
            slot.max_capacity,
            slot.booked_count,
            slot.max_capacity - slot.booked_count,
            'Yes' if slot.is_full else 'No',
        ])
    
    return response

# ================ REPORT VIEWS ================

@login_required
@user_passes_test(is_admin)
def appointment_report(request):
    """Generate appointment analytics report"""
    # Date range
    today = timezone.now().date()
    last_month = today - timedelta(days=30)
    
    # Get data
    appointments = Appointment.objects.filter(created_at__date__gte=last_month)
    
    # Daily appointments
    daily_appointments = appointments.values('date').annotate(
        count=Count('id'),
        confirmed=Count('id', filter=Q(is_confirmed=True)),
        pending=Count('id', filter=Q(is_confirmed=False))
    ).order_by('date')
    
    # By purpose
    by_purpose = appointments.values('appointment_aim').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # By company
    by_company = appointments.values('company_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Time distribution
    time_distribution = []
    for hour in range(9, 18):  # 9 AM to 5 PM
        hour_appointments = appointments.filter(time__hour=hour).count()
        time_distribution.append({
            'hour': f'{hour}:00',
            'count': hour_appointments
        })
    
    context = {
        'today': today,
        'last_month': last_month,
        'daily_appointments': daily_appointments,
        'by_purpose': by_purpose,
        'by_company': by_company,
        'time_distribution': time_distribution,
        'total_appointments': appointments.count(),
        'confirmed_appointments': appointments.filter(is_confirmed=True).count(),
        'pending_appointments': appointments.filter(is_confirmed=False).count(),
    }
    
    return render(request, 'appointments/appointment_report.html', context)

# ================ FORM HANDLING VIEWS ================

@login_required
@user_passes_test(is_admin)
@require_POST
def confirm_appointment_form(request):
    """Handle appointment confirmation via POST form"""
    appointment_id = request.POST.get('appointment_id')
    
    if not appointment_id:
        messages.error(request, "No appointment ID provided!")
        return redirect('dashboard')
    
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        
        if appointment.is_confirmed:
            messages.warning(request, f"Appointment #{appointment_id} is already confirmed!")
        else:
            appointment.is_confirmed = True
            appointment.save()
            messages.success(request, f"Appointment #{appointment_id} confirmed successfully!")
            
    except Appointment.DoesNotExist:
        messages.error(request, f"Appointment #{appointment_id} not found!")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('dashboard')

@login_required
@user_passes_test(is_admin)
@require_POST
def cancel_appointment_form(request):
    """Handle appointment cancellation via POST form"""
    appointment_id = request.POST.get('appointment_id')
    
    if not appointment_id:
        messages.error(request, "No appointment ID provided!")
        return redirect('dashboard')
    
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        confirmation_code = appointment.confirmation_code
        
        # Update slot if needed
        if appointment.appointment_slot:
            appointment.appointment_slot.booked_count = max(
                0, appointment.appointment_slot.booked_count - 1
            )
            appointment.appointment_slot.save()
        
        appointment.delete()
        messages.success(request, f"Appointment #{appointment_id} ({confirmation_code}) cancelled!")
        
    except Appointment.DoesNotExist:
        messages.error(request, f"Appointment #{appointment_id} not found!")
    except Exception as e:
        messages.error(request, f"Error: {str(e)}")
    
    return redirect('dashboard')

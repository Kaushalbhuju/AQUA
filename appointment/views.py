from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import CreateView, ListView, TemplateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.contrib import messages
from .models import Appointment, AppointmentSlot
from .forms import AppointmentForm, DateFilterForm
import json

class AppointmentCreateView(CreateView):
    """View for creating new appointments"""
    model = Appointment
    form_class = AppointmentForm
    template_name = 'appointments/book_appointment.html'
    success_url = reverse_lazy('appointment_confirmation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        slot_id = self.request.GET.get('slot_id')
        if slot_id:
            try:
                slot = AppointmentSlot.objects.get(id=slot_id)
                context['selected_slot'] = slot
            except AppointmentSlot.DoesNotExist:
                pass
        return context
    
    def form_valid(self, form):
        # Set the appointment slot from GET parameter or form data
        slot_id = self.request.GET.get('slot_id') or form.cleaned_data.get('appointment_slot')
        if slot_id:
            form.instance.appointment_slot_id = slot_id
        
        response = super().form_valid(form)
        messages.success(self.request, f"Appointment booked successfully! Your confirmation code is: {form.instance.confirmation_code}")
        return response

class AppointmentSlotListView(ListView):
    """View for displaying available appointment slots"""
    model = AppointmentSlot
    template_name = 'appointments/available_slots.html'
    context_object_name = 'slots'
    
    def get_queryset(self):
        queryset = AppointmentSlot.objects.filter(
            is_available=True,
            start_time__gte=timezone.now()
        ).order_by('start_time')
        
        # Filter by date if provided
        date_filter = self.request.GET.get('date')
        if date_filter:
            queryset = queryset.filter(start_time__date=date_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['date_filter_form'] = DateFilterForm(self.request.GET or None)
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
            'available_spots': slot.max_capacity - slot.booked_count
        }
        for slot in slots.order_by('start_time')
    ]
    
    return JsonResponse({'slots': slots_data})

class AppointmentConfirmationView(TemplateView):
    """View for displaying appointment confirmation"""
    template_name = 'appointments/confirmation.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        confirmation_code = self.request.GET.get('code')
        if confirmation_code:
            try:
                appointment = Appointment.objects.get(confirmation_code=confirmation_code)
                context['appointment'] = appointment
            except Appointment.DoesNotExist:
                pass
        return context
    
def test(request):
    return render(request, 'appointments/base.html')

# appointment/views.py
from django.shortcuts import render
from django.http import HttpResponse

def test_view(request):
    """Simple test view to check if CSS is loading"""
    context = {
        'title': 'CSS Test Page',
        'message': 'If you see colors and styles, CSS is working!'
    }
    return render(request, 'appointment/test.html', context)

def home_view(request):
    """Home page"""
    return render(request, 'appointment/home.html')
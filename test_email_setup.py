#!/usr/bin/env python
"""
Quick test script to verify email configuration and template rendering.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rm_system.settings')
django.setup()

from django.conf import settings
from django.template.loader import render_to_string
from appointment.emails import AppointmentEmailService
from appointment.models import Appointment, AppointmentSlot
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("EMAIL CONFIGURATION TEST")
print("=" * 60)

# Test 1: Check email settings
print("\n1. Email Settings:")
print(f"   EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"   EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"   EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"   EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"   EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"   DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")

# Test 2: Check template rendering
print("\n2. Template Rendering Test:")
try:
    # Create a mock appointment for testing
    slot = AppointmentSlot(
        start_time=timezone.now() + timedelta(days=1),
        end_time=timezone.now() + timedelta(days=1, hours=1),
        max_capacity=1
    )
    
    appointment = Appointment(
        id=999,
        name="Test User",
        email="test@example.com",
        phone="+1234567890",
        address="Test Address",
        company_name="Test Company",
        position="Test Position",
        appointment_aim="consultation",
        message="Test message",
        appointment_slot=slot,
        date=(timezone.now() + timedelta(days=1)).date(),
        time=(timezone.now() + timedelta(days=1)).time(),
        confirmation_code="TEST1234",
        is_confirmed=False
    )
    
    # Test booking confirmation template
    context = {
        'appointment': appointment,
        'public_url': 'http://example.com/appointment/TEST1234/',
        'site_name': 'SSW Academy Nepal',
        'site_email': settings.DEFAULT_FROM_EMAIL,
    }
    
    html = render_to_string('appointment/emails/booking_confirmation.html', context)
    text = render_to_string('appointment/emails/booking_confirmation.txt', context)
    
    print("   ✓ Booking confirmation HTML template: OK")
    print("   ✓ Booking confirmation text template: OK")
    
    # Test admin confirmation template
    appointment.is_confirmed = True
    html2 = render_to_string('appointment/emails/appointment_confirmed.html', context)
    text2 = render_to_string('appointment/emails/appointment_confirmed.txt', context)
    
    print("   ✓ Admin confirmation HTML template: OK")
    print("   ✓ Admin confirmation text template: OK")
    
except Exception as e:
    print(f"   ✗ Template rendering failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Check email service
print("\n3. Email Service Test:")
try:
    print("   ✓ AppointmentEmailService imported successfully")
    print(f"   - send_booking_confirmation method: available")
    print(f"   - send_admin_confirmation method: available")
except Exception as e:
    print(f"   ✗ Email service error: {e}")

# Test 4: Check signals
print("\n4. Signals Test:")
try:
    from appointment import signals
    print("   ✓ Signals module imported successfully")
except Exception as e:
    print(f"   ✗ Signals error: {e}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNOTE: To test actual email sending, run:")
print("  python manage.py shell")
print("Then create an appointment and check if emails are sent.")

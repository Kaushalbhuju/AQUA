#!/usr/bin/env python
"""
Email Diagnostic Script

This script diagnoses why emails are not being sent from the appointment app.
Run this to get detailed error information.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rm_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    print("✓ Django setup successful")
except Exception as e:
    print(f"✗ Django setup failed: {e}")
    sys.exit(1)

from django.core.mail import get_connection, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from appointment.models import Appointment
from appointment.emails import AppointmentEmailService


def test_smtp_connection():
    """Test basic SMTP connectivity"""
    print("\n" + "="*60)
    print("1. SMTP CONNECTION TEST")
    print("="*60)
    
    print(f"\nEmail Settings:")
    print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"  EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    
    try:
        connection = get_connection()
        connection.open()
        print("\n✓ SMTP connection opened successfully")
        connection.close()
        print("✓ SMTP connection closed successfully")
        return True
    except Exception as e:
        print(f"\n✗ SMTP connection failed: {e}")
        print(f"\nError type: {type(e).__name__}")
        return False


def test_template_rendering():
    """Test that email templates render correctly"""
    print("\n" + "="*60)
    print("2. TEMPLATE RENDERING TEST")
    print("="*60)
    
    # Get the most recent appointment
    try:
        appointment = Appointment.objects.latest('created_at')
        print(f"\nUsing appointment: {appointment.name} ({appointment.email})")
    except Appointment.DoesNotExist:
        print("\n✗ No appointments found in database")
        print("  Creating a test appointment...")
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a test slot
        from appointment.models import AppointmentSlot
        slot = AppointmentSlot.objects.create(
            start_time=timezone.now() + timedelta(days=1),
            end_time=timezone.now() + timedelta(days=1, hours=1),
            is_available=True,
            max_capacity=1
        )
        
        appointment = Appointment.objects.create(
            name="Test User",
            email="test@example.com",
            phone="+1234567890",
            address="Test Address",
            company_name="Test Company",
            position="Test Position",
            appointment_aim="consultation",
            message="Test message",
            appointment_slot=slot,
            date=slot.start_time.date(),
            time=slot.start_time.time(),
        )
        print(f"  Created test appointment: {appointment.name} ({appointment.email})")
    
    templates_to_test = [
        'appointment/emails/booking_confirmation.html',
        'appointment/emails/booking_confirmation.txt',
        'appointment/emails/appointment_confirmed.html',
        'appointment/emails/appointment_confirmed.txt',
    ]
    
    all_ok = True
    for template in templates_to_test:
        try:
            context = {
                'appointment': appointment,
                'public_url': 'http://example.com/test',
                'site_name': 'SSW Academy Nepal',
                'site_email': settings.DEFAULT_FROM_EMAIL,
            }
            result = render_to_string(template, context)
            print(f"  ✓ {template}: OK ({len(result)} chars)")
        except Exception as e:
            print(f"  ✗ {template}: FAILED - {e}")
            all_ok = False
    
    return all_ok, appointment


def test_email_service(appointment):
    """Test the email service directly"""
    print("\n" + "="*60)
    print("3. EMAIL SERVICE TEST")
    print("="*60)
    
    print(f"\nTesting send_booking_confirmation...")
    try:
        result = AppointmentEmailService.send_booking_confirmation(appointment)
        if result:
            print("  ✓ Booking confirmation email sent successfully")
        else:
            print("  ✗ Booking confirmation email failed (returned False)")
    except Exception as e:
        print(f"  ✗ Booking confirmation email failed: {e}")
        print(f"     Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
    
    print(f"\nTesting send_admin_confirmation...")
    try:
        result = AppointmentEmailService.send_admin_confirmation(appointment)
        if result:
            print("  ✓ Admin confirmation email sent successfully")
        else:
            print("  ✗ Admin confirmation email failed (returned False)")
    except Exception as e:
        print(f"  ✗ Admin confirmation email failed: {e}")
        print(f"     Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


def test_direct_email():
    """Test sending a direct email via Django"""
    print("\n" + "="*60)
    print("4. DIRECT EMAIL TEST")
    print("="*60)
    
    try:
        msg = EmailMessage(
            subject='Test Email from SSW Academy Nepal',
            body='This is a test email to verify SMTP configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER],  # Send to self
        )
        result = msg.send(fail_silently=False)
        print(f"\n✓ Direct email sent successfully (result: {result})")
        print(f"  Check {settings.EMAIL_HOST_USER} inbox")
    except Exception as e:
        print(f"\n✗ Direct email failed: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()


def check_gmail_requirements():
    """Check if Gmail-specific requirements are met"""
    print("\n" + "="*60)
    print("5. GMAIL REQUIREMENTS CHECK")
    print("="*60)
    
    print("\nGmail SMTP requires one of the following:")
    print("  1. 'Less secure app access' enabled in Google Account")
    print("  2. An App Password (recommended, especially with 2FA)")
    print("  3. OAuth 2.0 authentication")
    print("\nCurrent configuration uses regular password authentication.")
    print("If you have 2FA enabled, you MUST use an App Password.")
    print("\nTo create an App Password:")
    print("  1. Go to https://myaccount.google.com/apppasswords")
    print("  2. Sign in with your Google account")
    print("  3. Select 'Mail' and your device")
    print("  4. Copy the 16-character password")
    print("  5. Update EMAIL_HOST_PASSWORD in settings.py")


def main():
    print("="*60)
    print("EMAIL DIAGNOSTIC TOOL")
    print("="*60)
    
    # Test 1: SMTP Connection
    smtp_ok = test_smtp_connection()
    
    # Test 2: Template Rendering
    templates_ok, appointment = test_template_rendering()
    
    # Test 3: Email Service
    if appointment:
        test_email_service(appointment)
    
    # Test 4: Direct Email
    test_direct_email()
    
    # Test 5: Gmail Requirements
    check_gmail_requirements()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"SMTP Connection: {'✓ OK' if smtp_ok else '✗ FAILED'}")
    print(f"Templates: {'✓ OK' if templates_ok else '✗ FAILED'}")
    
    if not smtp_ok:
        print("\n⚠️  SMTP connection failed. This is the most likely cause.")
        print("   Check your Gmail settings and password.")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    main()

"""
Email notification service for the appointment app.

This module provides utilities for sending automated email notifications
to users when they book appointments and when admins confirm them.
"""

import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse


logger = logging.getLogger(__name__)


class AppointmentEmailService:
    """
    Service class for sending appointment-related email notifications.
    
    All methods are static and handle errors gracefully to ensure
    appointment operations are not disrupted by email failures.
    """
    
    @staticmethod
    def _build_public_url(appointment, request=None):
        """
        Build the public appointment detail URL.
        
        Args:
            appointment: Appointment instance
            request: Optional HttpRequest to build absolute URI
            
        Returns:
            str: Public URL for the appointment detail page
        """
        try:
            url = reverse('appointment_detail_public', kwargs={
                'confirmation_code': appointment.confirmation_code
            })
            
            if request:
                return request.build_absolute_uri(url)
            
            # Build from SITE_URL if no request available
            site_url = getattr(settings, 'SITE_URL', 'http://127.0.0.1:8000').rstrip('/')
            return f"{site_url}{url}"
        except Exception as e:
            logger.warning(f"Could not build public URL for appointment {appointment.id}: {e}")
            return None
    
    @staticmethod
    def _send_email(subject, template_prefix, appointment, request=None, extra_context=None):
        """
        Send an email using both HTML and text templates.
        
        Args:
            subject: Email subject line
            template_prefix: Base name for templates (e.g., 'booking_confirmation')
            appointment: Appointment instance
            request: Optional HttpRequest for building absolute URLs
            extra_context: Optional dict of extra template context variables
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Build template paths
            html_template = f'appointment/emails/{template_prefix}.html'
            text_template = f'appointment/emails/{template_prefix}.txt'
            
            # Build context
            context = {
                'appointment': appointment,
                'public_url': AppointmentEmailService._build_public_url(appointment, request),
                'site_name': 'SSW Academy Nepal',
                'site_email': settings.DEFAULT_FROM_EMAIL,
            }
            
            if extra_context:
                context.update(extra_context)
            
            # Render templates
            html_content = render_to_string(html_template, context)
            text_content = render_to_string(text_template, context)
            
            # Create email
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = appointment.email
            
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[to_email],
            )
            msg.attach_alternative(html_content, "text/html")
            
            # Send email
            msg.send(fail_silently=False)
            
            logger.info(
                f"Email sent successfully: {template_prefix} "
                f"to {to_email} for appointment {appointment.id}"
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send email: {template_prefix} "
                f"to {appointment.email} for appointment {appointment.id}: {e}",
                exc_info=True
            )
            return False
    
    @staticmethod
    def send_booking_confirmation(appointment, request=None):
        """
        Send booking confirmation email to the user.
        
        Called immediately after a new appointment is created.
        
        Args:
            appointment: The newly created Appointment instance
            request: Optional HttpRequest for building absolute URLs
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = (
            f"Appointment Booked Successfully! 📅 "
            f"Code: {appointment.confirmation_code}"
        )
        
        return AppointmentEmailService._send_email(
            subject=subject,
            template_prefix='booking_confirmation',
            appointment=appointment,
            request=request,
        )
    
    @staticmethod
    def send_admin_confirmation(appointment, request=None):
        """
        Send admin confirmation email to the user.
        
        Called when an admin confirms the appointment.
        
        Args:
            appointment: The confirmed Appointment instance
            request: Optional HttpRequest for building absolute URLs
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        subject = (
            f"✅ Your Appointment is Confirmed! "
            f"{appointment.date.strftime('%b %d, %Y')}"
        )
        
        return AppointmentEmailService._send_email(
            subject=subject,
            template_prefix='appointment_confirmed',
            appointment=appointment,
            request=request,
        )

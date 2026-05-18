"""
Django signals for the appointment app.

This module provides signal handlers that ensure email notifications
are sent reliably regardless of how appointments are created.
Signals act as a safety net for:
- Admin interface changes
- Bulk operations (via management commands)
- API updates
- Direct model saves
"""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Appointment
from .emails import AppointmentEmailService


logger = logging.getLogger(__name__)


# Store previous confirmation state before save
@receiver(pre_save, sender=Appointment)
def appointment_pre_save(sender, instance, **kwargs):
    """
    Capture the previous confirmation state before saving.
    
    This allows the post_save signal to detect when is_confirmed
    changes from False to True.
    """
    if instance.pk:
        try:
            old_instance = Appointment.objects.get(pk=instance.pk)
            instance._previous_is_confirmed = old_instance.is_confirmed
        except Appointment.DoesNotExist:
            instance._previous_is_confirmed = False
    else:
        instance._previous_is_confirmed = False


@receiver(post_save, sender=Appointment)
def appointment_post_save(sender, instance, created, **kwargs):
    """
    Signal handler for Appointment post_save events.
    
    This ensures emails are sent even when appointments are:
    - Created via admin interface
    - Updated via management commands
    - Modified through API endpoints
    - Bulk updated
    
    Args:
        sender: The Appointment model class
        instance: The Appointment instance that was saved
        created: True if this is a new instance, False if updated
        **kwargs: Additional signal kwargs
    """
    try:
        if created:
            # New appointment created - send booking confirmation
            # Skip if view already sent it (view sets this flag before saving)
            if not getattr(instance, '_booking_email_sent', False):
                logger.info(
                    f"Signal: Sending booking confirmation for "
                    f"appointment {instance.id} (created via non-view path)"
                )
                AppointmentEmailService.send_booking_confirmation(instance)
            else:
                logger.debug(
                    f"Signal: Skipping booking email for appointment "
                    f"{instance.id} - already sent by view"
                )
        else:
            # Appointment updated - check if it was just confirmed
            previous_is_confirmed = getattr(instance, '_previous_is_confirmed', False)
            
            if not previous_is_confirmed and instance.is_confirmed:
                # Confirmation status changed from False to True
                # Skip if view already sent it (view sets this flag before saving)
                if not getattr(instance, '_confirmation_email_sent', False):
                    logger.info(
                        f"Signal: Appointment {instance.id} confirmed, "
                        f"sending confirmation email"
                    )
                    AppointmentEmailService.send_admin_confirmation(instance)
                else:
                    logger.debug(
                        f"Signal: Skipping confirmation email for appointment "
                        f"{instance.id} - already sent by view"
                    )
            
    except Exception as e:
        logger.error(
            f"Signal handler error for appointment {instance.id}: {e}",
            exc_info=True
        )

# sswadmission/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import FeePayment, Student
from django.db import transaction

@receiver(post_save, sender=FeePayment)
def update_student_payment_on_payment_save(sender, instance, created, **kwargs):
    """Update student payment status when payment is saved"""
    if instance.student:
        instance.student.update_payment_status()

@receiver(post_delete, sender=FeePayment)
def update_student_payment_on_payment_delete(sender, instance, **kwargs):
    """Update student payment status when payment is deleted"""
    if instance.student:
        instance.student.update_payment_status()
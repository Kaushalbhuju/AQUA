# sswadmission/context_processors.py
from .models import Student, FeePayment
from django.db.models import Sum, Count
from django.utils import timezone
from decimal import Decimal

def dashboard_stats(request):
    """Add dashboard stats to all templates"""
    if request.user.is_authenticated:
        today = timezone.now().date()
        
        stats = {
            'total_students': Student.objects.count(),
            'pending_applications': Student.objects.filter(status='pending').count(),
            'todays_payments_total': FeePayment.objects.filter(
                payment_date__date=today,
                status='completed'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'pending_payments_count': FeePayment.objects.filter(status='pending').count(),
        }
        return {'dashboard_stats': stats}
    return {}
from django.core.management.base import BaseCommand
from django.utils import timezone
from appointments.models import AppointmentSlot
from datetime import timedelta, datetime

class Command(BaseCommand):
    help = 'Create appointment slots for the next 30 days'
    
    def handle(self, *args, **kwargs):
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=30)
        
        current_date = start_date
        slots_created = 0
        
        while current_date <= end_date:
            # Skip weekends
            if current_date.weekday() < 5:  # Monday-Friday
                # Create slots from 9 AM to 5 PM, every hour
                for hour in range(9, 17):
                    start_time = timezone.make_aware(
                        datetime.combine(current_date, datetime.min.time())
                    ).replace(hour=hour)
                    end_time = start_time + timedelta(hours=1)
                    
                    # Check if slot already exists
                    if not AppointmentSlot.objects.filter(start_time=start_time).exists():
                        AppointmentSlot.objects.create(
                            start_time=start_time,
                            end_time=end_time,
                            max_capacity=5
                        )
                        slots_created += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(self.style.SUCCESS(f'Created {slots_created} appointment slots'))
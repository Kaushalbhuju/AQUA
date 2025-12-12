# sswadmission/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from sswadmission.models import Student, FeePayment
from decimal import Decimal
from django.utils import timezone
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Seed initial data for testing'

    def handle(self, *args, **kwargs):
        # Create test user if not exists
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))

        # Create sample students
        courses = ['Computer Science', 'Business Administration', 'Engineering', 'Medicine', 'Arts']
        statuses = ['pending', 'approved', 'enrolled', 'graduated']
        
        for i in range(1, 51):
            student = Student.objects.create(
                full_name=f'Student {i}',
                email=f'student{i}@example.com',
                phone=f'9876543{i:03d}',
                date_of_birth=timezone.now().date() - timedelta(days=random.randint(18*365, 25*365)),
                gender=random.choice(['male', 'female']),
                course=random.choice(courses),
                batch=f'2024-{random.randint(1, 4)}',
                total_fee=Decimal(random.randint(50000, 200000)),
                discount=Decimal(random.randint(0, 20000)),
                status=random.choice(statuses),
                created_by=user
            )
            
            # Create payments for some students
            if random.choice([True, False]):
                num_payments = random.randint(1, 3)
                for j in range(num_payments):
                    FeePayment.objects.create(
                        student=student,
                        amount=Decimal(random.randint(10000, 50000)),
                        payment_method=random.choice(['cash', 'bank_transfer', 'online_payment', 'upi']),
                        description=f'Payment {j+1} for {student.course}',
                        created_by=user
                    )
        
        self.stdout.write(self.style.SUCCESS('Successfully seeded 50 sample students with payments'))
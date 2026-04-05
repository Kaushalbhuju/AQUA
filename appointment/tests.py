from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from appointment.models import Appointment, AppointmentSlot


class AppointmentActionTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff',
            password='pass12345',
            role='staff',
            is_staff=True,
        )
        self.client_user = User.objects.create_user(
            username='client',
            password='pass12345',
            role='client',
        )
        start = timezone.now() + timedelta(days=1)
        self.slot = AppointmentSlot.objects.create(
            start_time=start,
            end_time=start + timedelta(hours=1),
            max_capacity=2,
        )
        self.appointment = Appointment.objects.create(
            name='Alice Example',
            email='alice@example.com',
            phone='+12345678901',
            address='1 Test Street',
            company_name='Example Co',
            position='Manager',
            appointment_aim='consultation',
            appointment_slot=self.slot,
            confirmation_code='ABC12345',
        )

    def test_confirm_appointment_requires_post(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse('confirm_appointment', args=[self.appointment.id]))

        self.assertEqual(response.status_code, 405)
        self.appointment.refresh_from_db()
        self.assertFalse(self.appointment.is_confirmed)

    def test_confirm_appointment_allows_staff_post(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(reverse('confirm_appointment', args=[self.appointment.id]))

        self.assertEqual(response.status_code, 302)
        self.appointment.refresh_from_db()
        self.assertTrue(self.appointment.is_confirmed)

    def test_cancel_appointment_requires_admin_access(self):
        self.client.force_login(self.client_user)

        response = self.client.post(reverse('cancel_appointment', args=[self.appointment.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Appointment.objects.filter(pk=self.appointment.pk).exists())

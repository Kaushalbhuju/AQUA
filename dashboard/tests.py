from datetime import date

from django.test import TestCase

from dashboard.models import Student


class StudentPhotoHelperTests(TestCase):
    def test_photo_display_url_returns_none_for_missing_file(self):
        student = Student(
            student_id='S-0001',
            full_name='Test Student',
            gender='male',
            date_of_birth=date(2000, 1, 1),
            permanent_address='Test Address',
            age=25,
            marital_status='single',
            height='170',
            weight='60',
            eye_lens_right='Normal',
            eye_lens_left='Normal',
            blood_group='A+',
            tb_status='negative',
            email='test@example.com',
            phone='1234567890',
        )
        student.photo.name = 'student_photos/missing.jpg'

        self.assertIsNone(student.photo_display_url)

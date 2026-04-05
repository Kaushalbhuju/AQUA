from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from coe_visa.views import can_manage_coe_visa


class CoeVisaAccessTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff',
            password='pass12345',
            role='staff',
        )
        self.client_user = User.objects.create_user(
            username='client',
            password='pass12345',
            role='client',
        )

    def test_can_manage_coe_visa_is_role_based(self):
        self.assertTrue(can_manage_coe_visa(self.staff_user))
        self.assertFalse(can_manage_coe_visa(self.client_user))

    @patch('coe_visa.views.get_object_or_404')
    @patch('coe_visa.views.COETracking.objects.get_or_create')
    def test_update_coe_status_rejects_invalid_status(self, mock_get_or_create, mock_get_object_or_404):
        student = Mock(id=1, full_name='Test Student')
        mock_get_object_or_404.return_value = student
        tracking = Mock()
        mock_get_or_create.return_value = (tracking, True)

        self.client.force_login(self.staff_user)
        response = self.client.post(
            reverse('coe_visa:update_coe_status', args=[1]),
            {'status': 'invalid_status'},
        )

        self.assertEqual(response.status_code, 302)
        tracking.save.assert_not_called()

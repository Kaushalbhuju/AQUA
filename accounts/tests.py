from django.test import TestCase

from accounts.forms import RegisterForm
from accounts.models import User


class RegisterFormTests(TestCase):
    def test_register_form_uses_custom_user_model(self):
        self.assertIs(RegisterForm._meta.model, User)

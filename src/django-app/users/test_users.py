from django.test import TestCase
from .forms import CustomUserCreationForm, CustomLoginForm


class UserFormsTest(TestCase):
    def test_custom_user_creation_form_valid(self):
        form_data = {'username': 'testuser', 'email': 'test@example.com', 'password1': 'strongpass123', 'password2': 'strongpass123'}
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_custom_user_creation_form_invalid_email(self):
        form_data = {'username': 'testuser', 'email': 'invalid', 'password1': 'strongpass123', 'password2': 'strongpass123'}
        form = CustomUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_login_form_required_fields(self):
        form = CustomLoginForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('password', form.errors)


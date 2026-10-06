from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import UserProfile


User = get_user_model()


class RegistrationTests(TestCase):
    def test_registration_creates_user_profile_and_hashes_password(self):
        response = self.client.post(
            reverse('register'),
            {
                'username': 'testcustomer',
                'email': 'customer@example.com',
                'first_name': 'Test',
                'last_name': 'Customer',
                'phone': '9876543210',
                'password1': 'StrongTestPass!2026',
                'password2': 'StrongTestPass!2026',
            },
        )

        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='testcustomer')

        self.assertEqual(user.email, 'customer@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'Customer')
        self.assertTrue(user.check_password('StrongTestPass!2026'))
        self.assertNotEqual(user.password, 'StrongTestPass!2026')
        self.assertTrue(user.password.startswith('pbkdf2_'))

        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.phone, '9876543210')

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='StrongExistingPass!2026',
        )

        response = self.client.post(
            reverse('register'),
            {
                'username': 'anotheruser',
                'email': 'EXISTING@example.com',
                'first_name': 'Another',
                'last_name': 'User',
                'phone': '9876543211',
                'password1': 'StrongAnotherPass!2026',
                'password2': 'StrongAnotherPass!2026',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='anotheruser').count(), 0)
        self.assertIn('An account with this email already exists.', response.content.decode())

    def test_login_works_after_registration(self):
        self.client.post(
            reverse('register'),
            {
                'username': 'loginuser',
                'email': 'login@example.com',
                'first_name': 'Login',
                'last_name': 'User',
                'phone': '9876543212',
                'password1': 'StrongLoginPass!2026',
                'password2': 'StrongLoginPass!2026',
            },
        )

        response = self.client.post(
            reverse('login'),
            {
                'username': 'loginuser',
                'password': 'StrongLoginPass!2026',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

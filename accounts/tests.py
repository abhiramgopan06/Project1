from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core import mail
from django.test import TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import UserProfile, PendingRegistration


User = get_user_model()


class RegistrationTests(TestCase):
    registration_data = {
        'username': 'testcustomer',
        'email': 'customer@example.com',
        'first_name': 'Test',
        'last_name': 'Customer',
        'phone': '9876543210',
        'password1': 'StrongTestPass!2026',
        'password2': 'StrongTestPass!2026',
    }

    @patch('accounts.views.random.randint', return_value=123456)
    def test_registration_sends_otp_before_creating_user(self, mocked_otp):
        response = self.client.post(reverse('register'), self.registration_data)

        self.assertRedirects(response, reverse('verify_registration'))
        self.assertFalse(User.objects.filter(username='testcustomer').exists())

        pending = PendingRegistration.objects.get(username='testcustomer')
        self.assertTrue(check_password('123456', pending.otp_hash))
        self.assertTrue(pending.password_hash.startswith('pbkdf2_'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('123456', mail.outbox[0].body)

    @patch('accounts.views.random.randint', return_value=123456)
    def test_correct_otp_creates_user_and_profile(self, mocked_otp):
        self.client.post(reverse('register'), self.registration_data)

        response = self.client.post(
            reverse('verify_registration'),
            {'otp': '123456'},
        )

        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='testcustomer')
        self.assertEqual(user.email, 'customer@example.com')
        self.assertTrue(user.check_password('StrongTestPass!2026'))

        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.phone, '9876543210')
        self.assertFalse(PendingRegistration.objects.filter(username='testcustomer').exists())

    @patch('accounts.views.random.randint', return_value=123456)
    def test_wrong_otp_does_not_create_user(self, mocked_otp):
        self.client.post(reverse('register'), self.registration_data)

        response = self.client.post(
            reverse('verify_registration'),
            {'otp': '999999'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='testcustomer').exists())
        pending = PendingRegistration.objects.get(username='testcustomer')
        self.assertEqual(pending.attempts, 1)

    @patch('accounts.views.random.randint', side_effect=[123456, 654321])
    def test_resend_otp_sends_a_new_code(self, mocked_otp):
        self.client.post(reverse('register'), self.registration_data)

        pending = PendingRegistration.objects.get(username='testcustomer')
        pending.otp_created_at = pending.otp_created_at.replace(year=2020)
        pending.save(update_fields=['otp_created_at'])

        response = self.client.post(
            reverse('verify_registration'),
            {'action': 'resend'},
        )

        self.assertRedirects(response, reverse('verify_registration'))
        self.assertEqual(len(mail.outbox), 2)
        pending.refresh_from_db()
        self.assertTrue(check_password('654321', pending.otp_hash))

    def test_duplicate_email_is_rejected(self):
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='StrongExistingPass!2026',
        )

        response = self.client.post(
            reverse('register'),
            {
                **self.registration_data,
                'username': 'anotheruser',
                'email': 'EXISTING@example.com',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='anotheruser').count(), 0)
        self.assertIn('An account with this email already exists.', response.content.decode())

    @patch('accounts.views.random.randint', return_value=123456)
    def test_login_works_after_verified_registration(self, mocked_otp):
        self.client.post(reverse('register'), self.registration_data)
        self.client.post(reverse('verify_registration'), {'otp': '123456'})

        response = self.client.post(
            reverse('login'),
            {
                'username': 'testcustomer',
                'password': 'StrongTestPass!2026',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

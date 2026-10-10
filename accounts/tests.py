# accounts/tests.py
# Tests for registration with email OTP and the Google button.
# Run them with:  python manage.py test accounts

import re
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import EmailOTP, UserProfile


User = get_user_model()


REGISTER_DATA = {
    'username': 'newuser',
    'first_name': 'New',
    'last_name': 'User',
    'email': 'newuser@example.com',
    'phone': '9876543210',
    'password1': 'Str0ng!Pass#2026',
    'password2': 'Str0ng!Pass#2026',
}


def code_from_last_email():
    """Read the 6-digit code out of the last email that was 'sent'."""
    body = mail.outbox[-1].body
    return re.search(r'\b(\d{6})\b', body).group(1)


class RegistrationOtpTests(TestCase):

    def register(self, **changes):
        data = dict(REGISTER_DATA)
        data.update(changes)
        return self.client.post(reverse('register'), data)

    def test_register_sends_otp_and_keeps_user_inactive(self):
        response = self.register()
        self.assertRedirects(response, reverse('verify_otp'))

        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['newuser@example.com'])

    def test_correct_otp_activates_user_and_goes_to_login(self):
        self.register()
        response = self.client.post(reverse('verify_otp'), {'otp': code_from_last_email()})
        self.assertRedirects(response, reverse('login'))

        user = User.objects.get(username='newuser')
        self.assertTrue(user.is_active)
        self.assertFalse(EmailOTP.objects.filter(user=user).exists())

        # and now the user can really log in
        logged_in = self.client.login(username='newuser', password='Str0ng!Pass#2026')
        self.assertTrue(logged_in)

    def test_wrong_otp_shows_error_and_user_stays_inactive(self):
        self.register()
        real = code_from_last_email()
        wrong = '000000' if real != '000000' else '111111'

        response = self.client.post(reverse('verify_otp'), {'otp': wrong})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Incorrect code')
        self.assertFalse(User.objects.get(username='newuser').is_active)

    def test_too_many_wrong_attempts_blocks_even_the_right_code(self):
        self.register()
        real = code_from_last_email()
        wrong = '000000' if real != '000000' else '111111'

        for _ in range(5):
            self.client.post(reverse('verify_otp'), {'otp': wrong})

        response = self.client.post(reverse('verify_otp'), {'otp': real})
        self.assertContains(response, 'Too many wrong attempts')
        self.assertFalse(User.objects.get(username='newuser').is_active)

    def test_expired_otp_is_rejected(self):
        self.register()
        EmailOTP.objects.update(created_at=timezone.now() - timedelta(minutes=11))

        response = self.client.post(reverse('verify_otp'), {'otp': code_from_last_email()})
        self.assertContains(response, 'expired')

    def test_non_digit_code_is_rejected(self):
        self.register()
        response = self.client.post(reverse('verify_otp'), {'otp': 'abc123'})
        self.assertContains(response, 'Please enter the 6-digit code')

    def test_resend_is_blocked_during_cooldown(self):
        self.register()
        response = self.client.post(reverse('resend_otp'), follow=True)
        self.assertContains(response, 'Please wait')
        self.assertEqual(len(mail.outbox), 1)      # no second email

    def test_resend_sends_new_code_and_old_code_stops_working(self):
        self.register()
        old_code = code_from_last_email()

        # pretend 31 seconds have passed
        EmailOTP.objects.update(created_at=timezone.now() - timedelta(seconds=31))
        response = self.client.post(reverse('resend_otp'), follow=True)
        self.assertContains(response, 'new code has been sent')
        self.assertEqual(len(mail.outbox), 2)

        new_code = code_from_last_email()
        if new_code != old_code:
            response = self.client.post(reverse('verify_otp'), {'otp': old_code})
            self.assertContains(response, 'Incorrect code')

        response = self.client.post(reverse('verify_otp'), {'otp': new_code})
        self.assertRedirects(response, reverse('login'))

    def test_resend_needs_post(self):
        self.register()
        response = self.client.get(reverse('resend_otp'))
        self.assertEqual(response.status_code, 405)

    def test_verify_page_without_registering_redirects(self):
        response = self.client.get(reverse('verify_otp'))
        self.assertRedirects(response, reverse('register'))

    def test_otp_is_not_stored_as_plain_text(self):
        self.register()
        self.assertNotEqual(EmailOTP.objects.get().code_hash, code_from_last_email())

    def test_unverified_user_login_goes_to_otp_page(self):
        self.register()
        self.client.logout()
        fresh = self.client_class()
        response = fresh.post(reverse('login'), {
            'username': 'newuser', 'password': 'Str0ng!Pass#2026'})
        self.assertRedirects(response, reverse('verify_otp'))

    def test_wrong_password_still_shows_normal_error(self):
        self.register()
        fresh = self.client_class()
        response = fresh.post(reverse('login'), {
            'username': 'newuser', 'password': 'wrong-password'})
        self.assertEqual(response.status_code, 200)

    def test_registering_again_replaces_unverified_account(self):
        self.register()
        self.register()
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)
        self.assertEqual(len(mail.outbox), 2)

    def test_verified_email_cannot_be_registered_twice(self):
        self.register()
        self.client.post(reverse('verify_otp'), {'otp': code_from_last_email()})
        response = self.register(username='other')
        self.assertContains(response, 'already exists')

    def test_email_failure_still_lets_user_resend(self):
        with mock.patch('django.core.mail.EmailMultiAlternatives.send',
                        side_effect=OSError('no internet')):
            response = self.register()
        self.assertRedirects(response, reverse('verify_otp'))
        self.assertTrue(EmailOTP.objects.exists())


class GoogleButtonTests(TestCase):

    def test_login_page_has_google_button_after_create_account(self):
        response = self.client.get(reverse('login'))
        html = response.content.decode()
        self.assertIn('Continue with Google', html)
        self.assertLess(html.index('Create an account'), html.index('Continue with Google'))

    def test_google_login_without_keys_shows_friendly_message(self):
        response = self.client.get(reverse('google_login'), follow=True)
        self.assertContains(response, 'Google sign-in is not set up yet')

    @override_settings(GOOGLE_CLIENT_ID='abc', GOOGLE_CLIENT_SECRET='xyz')
    def test_google_login_redirects_to_account_chooser(self):
        response = self.client.get(reverse('google_login'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('accounts.google.com', response['Location'])
        self.assertIn('prompt=select_account', response['Location'])

    @override_settings(GOOGLE_CLIENT_ID='abc', GOOGLE_CLIENT_SECRET='xyz')
    def test_google_callback_rejects_wrong_state(self):
        self.client.get(reverse('google_login'))
        response = self.client.get(reverse('google_callback'), {'code': 'c', 'state': 'bad'}, follow=True)
        self.assertContains(response, 'Google sign-in failed')

    def fake_google(self, email='gu@example.com', verified=True):
        token = mock.Mock()
        token.json.return_value = {'access_token': 'tok'}
        info = mock.Mock()
        info.json.return_value = {
            'email': email, 'email_verified': verified,
            'given_name': 'Goo', 'family_name': 'User'}
        return mock.patch('accounts.views.requests.post', return_value=token), \
               mock.patch('accounts.views.requests.get', return_value=info)

    @override_settings(GOOGLE_CLIENT_ID='abc', GOOGLE_CLIENT_SECRET='xyz')
    def test_google_callback_creates_and_logs_in_new_user(self):
        self.client.get(reverse('google_login'))
        state = self.client.session['google_state']
        post_patch, get_patch = self.fake_google()
        with post_patch, get_patch:
            response = self.client.get(reverse('google_callback'), {'code': 'c', 'state': state})
        self.assertRedirects(response, '/', fetch_redirect_response=False)

        user = User.objects.get(email='gu@example.com')
        self.assertTrue(user.is_active)
        self.assertEqual(user.username, 'gu')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

    @override_settings(GOOGLE_CLIENT_ID='abc', GOOGLE_CLIENT_SECRET='xyz')
    def test_google_callback_logs_in_existing_user_with_same_email(self):
        existing = User.objects.create_user('old', 'gu@example.com', 'pw12345!!')
        self.client.get(reverse('google_login'))
        state = self.client.session['google_state']
        post_patch, get_patch = self.fake_google()
        with post_patch, get_patch:
            self.client.get(reverse('google_callback'), {'code': 'c', 'state': state})
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(int(self.client.session['_auth_user_id']), existing.id)

    @override_settings(GOOGLE_CLIENT_ID='abc', GOOGLE_CLIENT_SECRET='xyz')
    def test_google_unverified_email_is_refused(self):
        self.client.get(reverse('google_login'))
        state = self.client.session['google_state']
        post_patch, get_patch = self.fake_google(verified=False)
        with post_patch, get_patch:
            response = self.client.get(reverse('google_callback'), {'code': 'c', 'state': state}, follow=True)
        self.assertContains(response, 'not verified')
        self.assertFalse(User.objects.exists())


class PageTests(TestCase):

    def test_register_and_verify_pages_render(self):
        self.assertEqual(self.client.get(reverse('register')).status_code, 200)
        self.client.post(reverse('register'), REGISTER_DATA)
        self.assertEqual(self.client.get(reverse('verify_otp')).status_code, 200)


# ----------------------------------------------------
# Your original registration tests, updated for the new flow:
# registering now sends an OTP first, and the account only
# works after the OTP is verified.
# ----------------------------------------------------
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

        # Now goes to the OTP page (not straight to login).
        self.assertRedirects(response, reverse('verify_otp'))
        user = User.objects.get(username='testcustomer')
        self.assertFalse(user.is_active)

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

    def test_login_works_after_registration_and_otp(self):
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

        # Verify the email with the code that was "sent".
        self.client.post(reverse('verify_otp'), {'otp': code_from_last_email()})

        response = self.client.post(
            reverse('login'),
            {
                'username': 'loginuser',
                'password': 'StrongLoginPass!2026',
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

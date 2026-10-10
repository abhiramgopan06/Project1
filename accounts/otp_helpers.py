# accounts/otp_helpers.py
# ----------------------------------------------------
# Small helper functions for the email OTP (one-time
# password) step of registration.
#
#   make_code()        -> creates a random 6 digit code
#   send_new_otp(user) -> saves a fresh code and emails it
#   check_otp(...)     -> checks the code the user typed
# ----------------------------------------------------

import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailOTP


# Create a random 6 digit code such as "042913".
# "secrets" is safer than "random" for security codes.
def make_code():
    number = secrets.randbelow(1000000)
    return str(number).zfill(6)


# Hide most of an email address: "abhiram@gmail.com" -> "a******@gmail.com"
def mask_email(email):
    if '@' not in email:
        return email
    name, domain = email.split('@', 1)
    return name[0] + '*' * (len(name) - 1) + '@' + domain


# Has the OTP been alive for longer than the allowed time?
def is_expired(otp):
    age = timezone.now() - otp.created_at
    return age.total_seconds() > settings.OTP_EXPIRY_MINUTES * 60


# How many seconds must the user still wait before asking for another OTP?
# Returns 0 when they are allowed to resend.
def resend_wait_seconds(otp):
    age = (timezone.now() - otp.created_at).total_seconds()
    wait = settings.OTP_RESEND_SECONDS - age
    if wait <= 0:
        return 0
    return int(wait) + 1


# Save a brand new OTP for this user and email it to them.
# Returns True if the email was sent, False if sending failed.
def send_new_otp(user):
    code = make_code()

    # update_or_create keeps ONE row per user and replaces the old code.
    EmailOTP.objects.update_or_create(
        user=user,
        defaults={
            'code_hash': make_password(code),
            'created_at': timezone.now(),
            'attempts': 0,
        }
    )

    context = {
        'name': user.first_name or user.username,
        'code': code,
        'minutes': settings.OTP_EXPIRY_MINUTES,
    }
    text_body = render_to_string('accounts/email/otp_email.txt', context)
    html_body = render_to_string('accounts/email/otp_email.html', context)

    message = EmailMultiAlternatives(
        subject='Your E-Commerce Shop verification code',
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html_body, 'text/html')

    try:
        message.send()
    except Exception as error:
        # Wrong email settings, no internet, etc. We print the reason in the
        # terminal so it is easy to debug, and tell the caller it failed.
        print('Could not send OTP email:', error)
        return False

    return True


# Check the code typed by the user.
# Returns a tuple: (is_ok, error_message)
def check_otp(otp, typed_code):
    if is_expired(otp):
        return False, 'This code has expired. Please request a new one.'

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        return False, 'Too many wrong attempts. Please request a new code.'

    if not check_password(typed_code, otp.code_hash):
        otp.attempts += 1
        otp.save(update_fields=['attempts'])

        left = settings.OTP_MAX_ATTEMPTS - otp.attempts
        if left <= 0:
            return False, 'Too many wrong attempts. Please request a new code.'
        return False, f'Incorrect code. You have {left} attempt(s) left.'

    return True, ''

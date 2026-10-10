
# accounts/views.py
# ----------------------------------------------------
# Handles account pages: creating a new account (register)
# and editing your profile info (profile).
# ----------------------------------------------------

import re
import secrets
from urllib.parse import urlencode

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from orders.models import OrderItem
from .forms import RegistrationForm, LoginForm
from .forms import UserForm, UserProfileForm, AddressForm
from .models import UserProfile, Address
from .otp_helpers import (
    send_new_otp, check_otp, mask_email, resend_wait_seconds,
)


# ----------------------------------------------------
# REGISTRATION WITH EMAIL OTP
#
#   1. register()    - user fills the form. The account is created
#                      but kept INACTIVE, and an OTP is emailed.
#   2. verify_otp()  - user types the code. If it is right the
#                      account becomes active.
#   3. resend_otp()  - sends a fresh code if the first one did not
#                      arrive or expired.
#   4. The user is sent to the login page and logs in normally.
# ----------------------------------------------------

# Sign-up page: creates a new Django User (inactive) plus an empty
# UserProfile to go with it, then emails the OTP.
def register(request):
    if request.method == 'POST':

        # If someone registered earlier but never entered the OTP, their
        # half-finished account would block the same username/email.
        # Remove only those unverified leftovers so they can try again.
        typed_username = request.POST.get('username', '').strip()
        typed_email = request.POST.get('email', '').strip()
        if typed_username or typed_email:
            User.objects.filter(
                is_active=False,
                email_otp__isnull=False
            ).filter(
                Q(username__iexact=typed_username) | Q(email__iexact=typed_email)
            ).delete()

        form = RegistrationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False      # cannot log in until the OTP is verified
            user.save()

            UserProfile.objects.create(
                user=user,
                phone=form.cleaned_data['phone']
            )

            email_sent = send_new_otp(user)

            # Remember who is verifying (stored in the session, not the URL).
            request.session['otp_user_id'] = user.id

            if email_sent:
                messages.success(
                    request,
                    'Account created! We have sent a 6-digit code to your email.'
                )
            else:
                messages.error(
                    request,
                    'Account created, but we could not send the email. '
                    'Please press "Resend code".'
                )

            return redirect('verify_otp')
    else:
        form = RegistrationForm()

    return render(
        request,
        'accounts/register.html',
        {'form': form}
    )


# Find the user who is currently verifying (from the session).
# Returns (user, otp) or (None, None) if there is nothing to verify.
def get_pending_user(request):
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return None, None

    user = User.objects.filter(id=user_id, is_active=False).first()
    if user is None or not hasattr(user, 'email_otp'):
        request.session.pop('otp_user_id', None)
        return None, None

    return user, user.email_otp


# The page where the user types the OTP.
def verify_otp(request):
    user, otp = get_pending_user(request)

    if user is None:
        messages.info(request, 'Please register or login first.')
        return redirect('register')

    error = ''

    if request.method == 'POST':
        typed_code = request.POST.get('otp', '').strip()

        if not re.fullmatch(r'[0-9]{6}', typed_code):
            error = 'Please enter the 6-digit code.'
        else:
            is_ok, error = check_otp(otp, typed_code)

            if is_ok:
                user.is_active = True
                user.save(update_fields=['is_active'])
                otp.delete()                       # the code is used up
                request.session.pop('otp_user_id', None)

                messages.success(
                    request,
                    'Email verified successfully! You can now login.'
                )
                return redirect('login')

    return render(request, 'accounts/verify_otp.html', {
        'masked_email': mask_email(user.email),
        'error': error,
        'resend_wait': resend_wait_seconds(otp),
        'expiry_minutes': settings.OTP_EXPIRY_MINUTES,
        # True while real email is not set up: the code is only printed in
        # the terminal, so we tell the developer where to look.
        'email_is_test_mode': settings.EMAIL_BACKEND.endswith('console.EmailBackend') and settings.DEBUG,
    })


# "Resend code" button. Only accepts POST (a button press, not a link).
@require_POST
def resend_otp(request):
    user, otp = get_pending_user(request)

    if user is None:
        messages.info(request, 'Please register or login first.')
        return redirect('register')

    wait = resend_wait_seconds(otp)
    if wait > 0:
        messages.warning(
            request,
            f'Please wait {wait} seconds before asking for a new code.'
        )
        return redirect('verify_otp')

    if send_new_otp(user):
        messages.success(request, 'A new code has been sent to your email.')
    else:
        messages.error(
            request,
            'We could not send the email. Please try again in a moment.'
        )

    return redirect('verify_otp')


# Login page. Same as Django's login, but if the user never verified
# their email we send them to the OTP page instead of showing an error.
class CustomLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm

    def form_invalid(self, form):
        if form.unverified_user is not None:
            self.request.session['otp_user_id'] = form.unverified_user.id
            messages.info(
                self.request,
                'Please verify your email first. Enter the code we sent you, '
                'or press "Resend code".'
            )
            return redirect('verify_otp')

        return super().form_invalid(form)


# ----------------------------------------------------
# CONTINUE WITH GOOGLE
#
#   1. google_login()    - sends the user to Google's account chooser.
#   2. google_callback() - Google sends the user back here with a code.
#                          We swap the code for the user's email + name,
#                          then log them in (creating the account if new).
# ----------------------------------------------------

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'


def google_is_configured():
    return bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)


def google_redirect_uri(request):
    return request.build_absolute_uri(reverse('google_callback'))


# Step 1: open the Google "choose an account" screen.
def google_login(request):
    if not google_is_configured():
        messages.error(
            request,
            'Google sign-in is not set up yet. Add GOOGLE_CLIENT_ID and '
            'GOOGLE_CLIENT_SECRET to the .env file (see README).'
        )
        return redirect('login')

    # "state" is a random value we check later to be sure the answer
    # really came from the sign-in we started.
    state = secrets.token_urlsafe(24)
    request.session['google_state'] = state

    query = urlencode({
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': google_redirect_uri(request),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',    # always show the account chooser
    })
    return redirect(f'{GOOGLE_AUTH_URL}?{query}')


# Make a username from an email, e.g. "abhi.ram@gmail.com" -> "abhi.ram"
# and add a number if somebody already has it.
def make_unique_username(email):
    base = re.sub(r'[^A-Za-z0-9._]', '', email.split('@')[0]) or 'user'
    base = base[:140]

    username = base
    number = 1
    while User.objects.filter(username__iexact=username).exists():
        number += 1
        username = f'{base}{number}'
    return username


# Step 2: Google sends the user back here.
def google_callback(request):
    if not google_is_configured():
        return redirect('login')

    # The user pressed "Cancel" on the Google screen.
    if request.GET.get('error'):
        messages.info(request, 'Google sign-in was cancelled.')
        return redirect('login')

    saved_state = request.session.pop('google_state', None)
    if not saved_state or saved_state != request.GET.get('state'):
        messages.error(request, 'Google sign-in failed. Please try again.')
        return redirect('login')

    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Google sign-in failed. Please try again.')
        return redirect('login')

    try:
        # Swap the code for an access token.
        token_response = requests.post(GOOGLE_TOKEN_URL, data={
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': google_redirect_uri(request),
            'grant_type': 'authorization_code',
        }, timeout=10)
        access_token = token_response.json().get('access_token')

        if not access_token:
            raise ValueError('No access token received')

        # Ask Google who the user is.
        info_response = requests.get(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        info = info_response.json()
    except (requests.RequestException, ValueError):
        messages.error(request, 'Could not connect to Google. Please try again.')
        return redirect('login')

    email = (info.get('email') or '').strip().lower()
    if not email or not info.get('email_verified'):
        messages.error(request, 'Your Google email is not verified.')
        return redirect('login')

    user = User.objects.filter(email__iexact=email).first()

    if user is None:
        # First time with this email: create the account.
        user = User(
            username=make_unique_username(email),
            email=email,
            first_name=(info.get('given_name') or '')[:150],
            last_name=(info.get('family_name') or '')[:150],
        )
        user.set_unusable_password()   # they sign in with Google, no password
        user.save()
        UserProfile.objects.create(user=user)

    elif not user.is_active:
        # Registered with the form but never typed the OTP. Google has
        # just proved the email is theirs, so we can activate it.
        if hasattr(user, 'email_otp'):
            user.is_active = True
            user.save(update_fields=['is_active'])
            user.email_otp.delete()
        else:
            messages.error(request, 'This account has been disabled.')
            return redirect('login')

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, f'Welcome, {user.first_name or user.username}!')
    return redirect(settings.LOGIN_REDIRECT_URL)


# The "My Profile" page. Shows the current details in a form,
# and saves them when the user submits changes.
@login_required
def profile(request):

    profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == 'POST':

        user_form = UserForm(
            request.POST,
            instance=request.user
        )

        profile_form = UserProfileForm(
            request.POST,
            instance=profile
        )

        if user_form.is_valid() and profile_form.is_valid():

            user_form.save()
            profile_form.save()

            messages.success(
                request,
                'Profile updated successfully.'
            )

            return redirect('profile')

    else:

        user_form = UserForm(
            instance=request.user
        )

        profile_form = UserProfileForm(
            instance=profile
        )

    return render(
        request,
        'accounts/profile.html',
        {
            'user_form': user_form,
            'profile_form': profile_form,
            'addresses': request.user.addresses.all(),
            # The 5 most recently ordered products, shown in the
            # "Order History" section of the profile page.
            'order_items': OrderItem.objects.filter(
                order__user=request.user
            ).select_related('product', 'order').order_by('-order__created_at', '-id')[:5],
        }
    )


# ----------------------------------------------------
# Saved addresses ("My Addresses"). A user enters their
# details once and can save more than one address - handy if
# they move somewhere temporarily and need deliveries sent
# there for a while.
# ----------------------------------------------------

# Add a brand-new saved address for the logged-in user.
@login_required
def address_add(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)

        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user

            # The very first address a user saves automatically
            # becomes their default one.
            if not request.user.addresses.exists():
                address.is_default = True

            address.save()

            if address.is_default:
                request.user.addresses.exclude(id=address.id).update(is_default=False)

            messages.success(request, 'Address saved.')
            return redirect('profile')
    else:
        form = AddressForm(initial={
            'full_name': request.user.get_full_name() or request.user.username,
            'email': request.user.email,
        })

    return render(request, 'accounts/address_form.html', {'form': form, 'is_new': True})


# Edit one of the user's existing saved addresses.
@login_required
def address_edit(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)

        if form.is_valid():
            updated = form.save(commit=False)
            updated.user = request.user
            updated.save()

            if updated.is_default:
                request.user.addresses.exclude(id=updated.id).update(is_default=False)

            messages.success(request, 'Address updated.')
            return redirect('profile')
    else:
        form = AddressForm(instance=address)

    return render(request, 'accounts/address_form.html', {'form': form, 'is_new': False})


# Delete a saved address.
@login_required
def address_delete(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        was_default = address.is_default
        address.delete()

        # If we just deleted the default address, make the next
        # most recent one the new default so checkout still has
        # a sensible pre-selected address.
        if was_default:
            next_address = request.user.addresses.first()
            if next_address:
                next_address.is_default = True
                next_address.save(update_fields=['is_default'])

        messages.success(request, 'Address removed.')

    return redirect('profile')
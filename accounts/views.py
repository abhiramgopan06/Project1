
# accounts/views.py
# ----------------------------------------------------
# Handles account pages: creating a new account (register)
# and editing your profile info (profile).
# ----------------------------------------------------

from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404

from orders.models import OrderItem
from .models import UserProfile, Address, PendingRegistration
from .forms import UserForm, UserProfileForm, AddressForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import random
import secrets
import string
import requests
from urllib.parse import urlencode
import re


# Sign-up page.
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)

        if form.is_valid():
            cleaned = form.cleaned_data
            PendingRegistration.objects.filter(username__iexact=cleaned['username']).delete()
            PendingRegistration.objects.filter(email__iexact=cleaned['email']).delete()

            otp = str(random.randint(100000, 999999))
            pending = PendingRegistration.objects.create(
                username=cleaned['username'],
                first_name=cleaned['first_name'],
                last_name=cleaned['last_name'],
                email=cleaned['email'],
                phone=cleaned['phone'],
                password_hash=make_password(cleaned['password1']),
                otp_hash=make_password(otp),
                attempts=0,
            )

            send_otp_email(pending, otp)
            request.session['pending_registration_id'] = pending.id
            messages.success(request, 'We sent a 6-digit verification code to your email.')
            return redirect('verify_registration')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def send_otp_email(pending, otp):
    subject = 'Verify your E-Commerce Shop account'
    text = (
        f'Hello {pending.first_name},\n\n'
        f'Your E-Commerce Shop verification code is {otp}.\n'
        f'This code expires in 10 minutes.\n\n'
        'If you did not start this registration, you can ignore this email.'
    )
    html = f'''
        <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;padding:32px;background:#f8fafc;">
            <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:16px;padding:32px;">
                <h2 style="margin:0 0 10px;color:#111827;">Verify your E-Commerce Shop account</h2>
                <p style="color:#64748b;line-height:1.6;">Hello {pending.first_name}, use the verification code below to finish creating your account.</p>
                <div style="margin:26px 0;padding:18px;text-align:center;border-radius:12px;background:#eef4ff;">
                    <strong style="font-size:32px;letter-spacing:8px;color:#2563eb;">{otp}</strong>
                </div>
                <p style="color:#64748b;">This code expires in <strong>10 minutes</strong>.</p>
                <p style="color:#94a3b8;font-size:13px;">If you did not request this code, you can safely ignore this email.</p>
            </div>
        </div>
    '''
    send_mail(subject, text, settings.DEFAULT_FROM_EMAIL, [pending.email], html_message=html)


def verify_registration(request):
    pending_id = request.session.get('pending_registration_id')
    if not pending_id:
        messages.info(request, 'Please start registration again.')
        return redirect('register')

    pending = PendingRegistration.objects.filter(id=pending_id).first()
    if not pending:
        request.session.pop('pending_registration_id', None)
        messages.error(request, 'This registration session has expired. Please register again.')
        return redirect('register')

    expired = timezone.now() > pending.otp_created_at + timedelta(minutes=10)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'resend':
            seconds_left = int((pending.otp_created_at + timedelta(seconds=60) - timezone.now()).total_seconds())
            if seconds_left > 0:
                messages.warning(request, f'Please wait {seconds_left} seconds before requesting another code.')
                return redirect('verify_registration')

            otp = str(random.randint(100000, 999999))
            pending.otp_hash = make_password(otp)
            pending.otp_created_at = timezone.now()
            pending.attempts = 0
            pending.save(update_fields=['otp_hash', 'otp_created_at', 'attempts'])
            send_otp_email(pending, otp)
            messages.success(request, 'A new verification code has been sent.')
            return redirect('verify_registration')

        otp = request.POST.get('otp', '').strip()

        if expired:
            messages.error(request, 'This code has expired. Please request a new code.')
        elif not otp.isdigit() or len(otp) != 6:
            messages.error(request, 'Enter the 6-digit verification code.')
        elif pending.attempts >= 5:
            messages.error(request, 'Too many incorrect attempts. Please request a new code.')
        elif not check_password(otp, pending.otp_hash):
            pending.attempts += 1
            pending.save(update_fields=['attempts'])
            remaining = max(0, 5 - pending.attempts)
            messages.error(request, f'Incorrect verification code. You have {remaining} attempt(s) remaining.')
        else:
            if User.objects.filter(username__iexact=pending.username).exists() or User.objects.filter(email__iexact=pending.email).exists():
                messages.error(request, 'This username or email is already registered. Please use different details.')
                pending.delete()
                request.session.pop('pending_registration_id', None)
                return redirect('register')

            user = User.objects.create(
                username=pending.username,
                first_name=pending.first_name,
                last_name=pending.last_name,
                email=pending.email,
                password=pending.password_hash,
            )
            UserProfile.objects.create(user=user, phone=pending.phone)
            pending.delete()
            request.session.pop('pending_registration_id', None)
            messages.success(request, 'Your email is verified. Your account is ready. Please log in.')
            return redirect('login')

    return render(request, 'accounts/verify_registration.html', {
        'pending': pending,
        'expired': expired,
    })


def google_login(request):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.info(request, 'Google Sign-In is not configured yet. Add the Google OAuth keys to your environment settings.')
        return redirect('login')

    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state

    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }
    return redirect('https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params))


def google_callback(request):
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return redirect('login')

    state = request.GET.get('state')
    saved_state = request.session.pop('google_oauth_state', None)
    if not state or state != saved_state:
        messages.error(request, 'Google sign-in could not be verified. Please try again.')
        return redirect('login')

    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Google sign-in was cancelled.')
        return redirect('login')

    token_response = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        },
        timeout=10,
    )
    if token_response.status_code != 200:
        messages.error(request, 'Google sign-in failed. Please try again.')
        return redirect('login')

    token_data = token_response.json()
    access_token = token_data.get('access_token')
    if not access_token:
        messages.error(request, 'Google did not return a valid sign-in token.')
        return redirect('login')

    userinfo_response = requests.get(
        'https://openidconnect.googleapis.com/v1/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10,
    )
    if userinfo_response.status_code != 200:
        messages.error(request, 'Could not read your Google account details.')
        return redirect('login')

    info = userinfo_response.json()
    email = info.get('email', '').strip().lower()
    if not email or not info.get('email_verified'):
        messages.error(request, 'Google did not provide a verified email address.')
        return redirect('login')

    user = User.objects.filter(email__iexact=email).first()

    if not user:
        base_username = re.sub(r'[^a-zA-Z0-9_]', '', email.split('@')[0]) or 'googleuser'
        username = base_username[:140]
        counter = 1
        while User.objects.filter(username__iexact=username).exists():
            username = f'{base_username[:130]}{counter}'
            counter += 1

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=info.get('given_name', ''),
            last_name=info.get('family_name', ''),
        )
        UserProfile.objects.create(user=user)

    login(request, user)
    messages.success(request, 'Welcome back. You signed in with Google.')
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
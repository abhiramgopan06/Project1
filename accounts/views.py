
# accounts/views.py
# ----------------------------------------------------
# Handles account pages: creating a new account (register)
# and editing your profile info (profile).
# ----------------------------------------------------

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.shortcuts import get_object_or_404

from orders.models import OrderItem
from .models import UserProfile, Address
from .forms import UserForm, UserProfileForm, AddressForm


# Sign-up page: creates a new Django User plus an empty
# UserProfile to go with it.
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            UserProfile.objects.create(user=user)

            messages.success(
                request,
                'Registration successful. You can now login.'
            )

            return redirect('login')

    else:
        form = UserCreationForm()

    return render(
        request,
        'accounts/register.html',
        {'form': form}
    )


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
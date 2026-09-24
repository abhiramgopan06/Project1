# accounts/checkout_helpers.py
# ----------------------------------------------------
# One small helper shared by the two checkout flows (Cash on
# Delivery in orders/views.py, and the demo online payment in
# payments/views.py). It figures out which name/email/phone/
# address should be used for the order:
#   - if the user picked one of their saved addresses, use that
#   - otherwise, save whatever they typed as a brand-new address
#     (so next time it shows up in their saved address list too)
# ----------------------------------------------------

from .models import Address


def resolve_checkout_address(request):
    """
    Reads 'address_id' (and, if needed, name/email/phone/address)
    from request.POST. Returns (name, email, phone, address, error).
    'error' is None on success, or a message to show the user.
    """
    address_id = request.POST.get('address_id', '').strip()

    if address_id and address_id != 'new':
        address = Address.objects.filter(id=address_id, user=request.user).first()
        if address is None:
            return None, None, None, None, 'Please choose a valid address.'
        return address.full_name, address.email, address.phone, address.address, None

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address_text = request.POST.get('address', '').strip()
    label = request.POST.get('label', '').strip() or 'Address'

    if not name or not email or not phone or not address_text:
        return None, None, None, None, 'Please fill in all customer information.'

    # Save this as a new address so the user only has to type it
    # once. The first address they ever save becomes the default.
    is_first_address = not request.user.addresses.exists()
    Address.objects.create(
        user=request.user,
        label=label,
        full_name=name,
        email=email,
        phone=phone,
        address=address_text,
        is_default=is_first_address,
    )

    return name, email, phone, address_text, None

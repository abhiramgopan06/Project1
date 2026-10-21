                                                            

from django.core.exceptions import ValidationError
from django.core.validators import validate_email
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
        try:
            validate_email(address.email)
        except ValidationError:
            return None, None, None, None, 'The selected address has an invalid email address.'
        if not address.phone.isdigit() or not 10 <= len(address.phone) <= 15:
            return None, None, None, None, 'The selected address has an invalid phone number.'
        return address.full_name, address.email, address.phone, address.address, None

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address_text = request.POST.get('address', '').strip()
    label = request.POST.get('label', '').strip() or 'Address'

    if not name or not email or not phone or not address_text:
        return None, None, None, None, 'Please fill in all customer information.'

    try:
        validate_email(email)
    except ValidationError:
        return None, None, None, None, 'Please enter a valid email address.'

    if not phone.isdigit() or not 10 <= len(phone) <= 15:
        return None, None, None, None, 'Phone number must contain 10 to 15 digits only.'

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

import uuid
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from products.models import Product, ProductVariant
from .models import StockReservation


def reserve_stock(*, user, product_id, quantity, variant_id=None, minutes=15):
    if quantity < 1:
        raise ValueError('Quantity must be at least one.')
    with transaction.atomic():
        product = Product.objects.select_for_update().get(pk=product_id, is_available=True)
        variant = None
        if variant_id is not None:
            variant = ProductVariant.objects.select_for_update().get(pk=variant_id, product=product, is_active=True)
        now = timezone.now()
        active = StockReservation.objects.filter(product=product, variant=variant, released=False, expires_at__gt=now)
        reserved = sum(active.values_list('quantity', flat=True))
        available = (variant.stock if variant else product.stock) - reserved
        if quantity > available:
            raise ValueError(f'Only {max(available, 0)} units are available.')
        return StockReservation.objects.create(
            product=product,
            variant=variant,
            user=user,
            quantity=quantity,
            reference=f'RSV-{uuid.uuid4().hex}',
            expires_at=now + timedelta(minutes=max(1, min(minutes, 60))),
        )


def release_reservation(reference):
    with transaction.atomic():
        reservation = StockReservation.objects.select_for_update().filter(reference=reference, released=False).first()
        if reservation is None:
            return False
        reservation.released = True
        reservation.save(update_fields=['released'])
        return True


def release_expired_reservations():
    return StockReservation.objects.filter(released=False, expires_at__lte=timezone.now()).update(released=True)

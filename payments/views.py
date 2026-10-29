
import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

from cart.models import Cart
from orders.models import Order, OrderItem
from products.models import Product
from products.recommendations import record_product_history
from accounts.checkout_helpers import resolve_checkout_address
from orders.models import Coupon

def _cart_total(cart_items):
    return sum(
        (item.product.discounted_price * item.quantity for item in cart_items),
        Decimal('0.00')
    )

@login_required
@require_POST
def create_payment_order(request):
    real_payment = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
    if not settings.DEBUG and not real_payment:
        return JsonResponse({'success': False, 'error': 'Configure Razorpay keys before accepting live payments.'}, status=503)

    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cart not found.'}, status=404)

    cart_items = list(cart.items.select_related('product'))
    if not cart_items:
        return JsonResponse({'success': False, 'error': 'Your cart is empty.'}, status=400)

    for item in cart_items:
        if not item.product.is_available:
            return JsonResponse({
                'success': False,
                'error': f'{item.product.name} is no longer available.'
            }, status=400)
        if item.quantity > item.product.stock:
            return JsonResponse({
                'success': False,
                'error': f'Not enough stock for {item.product.name}.'
            }, status=400)

    shipping_method = request.POST.get('shipping_method', Order.SHIPPING_FREE)
    if shipping_method not in (Order.SHIPPING_FREE, Order.SHIPPING_EXPRESS):
        return JsonResponse({'success': False, 'error': 'Please select a valid shipping method.'}, status=400)
    shipping_cost = Decimal('99.00') if shipping_method == Order.SHIPPING_EXPRESS else Decimal('0.00')
    subtotal = _cart_total(cart_items)
    coupon = Coupon.objects.filter(code=request.session.get('applied_coupon', ''), is_active=True).first() if request.session.get('applied_coupon') else None
    discount = Decimal('0.00')
    if coupon and subtotal >= coupon.minimum_order_amount and (not coupon.usage_limit or coupon.used_count < coupon.usage_limit):
        if coupon.discount_percent:
            discount = (subtotal * Decimal(coupon.discount_percent) / Decimal('100')).quantize(Decimal('0.01'))
        else:
            discount = min(coupon.discount_amount, subtotal)
    payable = max(Decimal('0.00'), subtotal - discount) + shipping_cost
    amount = int(payable.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)
    if real_payment:
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            payment_order = client.order.create({'amount': amount, 'currency': 'INR', 'receipt': f'user-{request.user.pk}-{uuid.uuid4().hex[:12]}'})
            provider_order_id = payment_order['id']
        except Exception:
            return JsonResponse({'success': False, 'error': 'Razorpay could not create the payment order. Please try again.'}, status=502)
    else:
        provider_order_id = f'order_DEMO{uuid.uuid4().hex[:14]}'

    request.session['demo_payment_order_id'] = provider_order_id
    request.session['demo_payment_amount'] = amount
    request.session['demo_payment_shipping_method'] = shipping_method
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'razorpay_order_id': provider_order_id,
        'key_id': settings.RAZORPAY_KEY_ID if real_payment else '',
        'amount': amount,
        'shipping_method': shipping_method,
        'currency': 'INR',
        'name': 'E-Commerce Store',
        'description': 'Order payment' if real_payment else 'Order payment (Demo - no real charge)',
    })

@login_required
@require_POST
def verify_payment(request):
    real_payment = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
    if not settings.DEBUG and not real_payment:
        return JsonResponse({'success': False, 'error': 'Live payment verification is not configured.'}, status=503)

    razorpay_payment_id = request.POST.get('razorpay_payment_id', '').strip()
    razorpay_order_id = request.POST.get('razorpay_order_id', '').strip()
    razorpay_signature = request.POST.get('razorpay_signature', '').strip()
    expected_order_id = request.session.get('demo_payment_order_id')
    if not expected_order_id or razorpay_order_id != expected_order_id:
        return JsonResponse({'success': False, 'error': 'Invalid or expired payment session. Please start payment again.'}, status=400)

    if real_payment:
        try:
            import razorpay
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            client.utility.verify_payment_signature({'razorpay_order_id': razorpay_order_id, 'razorpay_payment_id': razorpay_payment_id, 'razorpay_signature': razorpay_signature})
            provider_payment = client.payment.fetch(razorpay_payment_id)
            expected_amount = request.session.get('demo_payment_amount')
            if provider_payment.get('order_id') != expected_order_id or provider_payment.get('currency') != 'INR' or provider_payment.get('amount') != expected_amount or provider_payment.get('status') != 'captured':
                return JsonResponse({'success': False, 'error': 'Payment is not captured for the expected amount.'}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': 'Payment signature verification failed.'}, status=400)
    elif not settings.DEBUG or not razorpay_payment_id.startswith('pay_DEMO'):
        return JsonResponse({'success': False, 'error': 'Invalid demo payment reference.'}, status=400)

    shipping_method = request.session.get('demo_payment_shipping_method', Order.SHIPPING_FREE)
    if shipping_method not in (Order.SHIPPING_FREE, Order.SHIPPING_EXPRESS):
        return JsonResponse({'success': False, 'error': 'Please start checkout again and select shipping.'}, status=400)
    shipping_cost = Decimal('99.00') if shipping_method == Order.SHIPPING_EXPRESS else Decimal('0.00')

    name, email, phone, address, error = resolve_checkout_address(request)
    if error:
        return JsonResponse({
            'success': False,
            'error': error
        }, status=400)
    try:
        with transaction.atomic():
            cart = Cart.objects.select_for_update().get(user=request.user)
            cart_items = list(
                cart.items.select_related('product').select_for_update()
            )

            if not cart_items:
                return JsonResponse({
                    'success': False,
                    'error': 'Your cart is empty.'
                }, status=400)

            product_ids = [item.product_id for item in cart_items]
            products = {
                product.pk: product
                for product in Product.objects.select_for_update().filter(pk__in=product_ids)
            }

            total = Decimal('0.00')
            for item in cart_items:
                product = products.get(item.product_id)
                if product is None or not product.is_available:
                    return JsonResponse({
                        'success': False,
                        'error': f'{item.product.name} is no longer available.'
                    }, status=400)
                if item.quantity > product.stock:
                    return JsonResponse({
                        'success': False,
                        'error': (
                            f'Sorry, only {product.stock} units of '
                            f'{product.name} are available.'
                        )
                    }, status=400)
                total += product.discounted_price * item.quantity

            coupon = Coupon.objects.select_for_update().filter(code=request.session.get('applied_coupon', ''), is_active=True).first() if request.session.get('applied_coupon') else None
            discount = Decimal('0.00')
            if coupon and total >= coupon.minimum_order_amount and (not coupon.usage_limit or coupon.used_count < coupon.usage_limit):
                if coupon.discount_percent:
                    discount = (total * Decimal(coupon.discount_percent) / Decimal('100')).quantize(Decimal('0.01'))
                else:
                    discount = min(coupon.discount_amount, total)
            else:
                coupon = None

            order = Order.objects.create(
                user=request.user,
                name=name,
                email=email,
                phone=phone,
                address=address,
                total_amount=max(Decimal('0.00'), total - discount) + shipping_cost,
                coupon=coupon,
                discount_amount=discount,
                shipping_method=shipping_method,
                shipping_cost=shipping_cost,
                payment_method='razorpay' if real_payment else 'razorpay (demo)',
                payment_status='Paid',
                status=Order.STATUS_CONFIRMED,
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
            )

            for item in cart_items:
                product = products[item.product_id]
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.discounted_price,
                )
                record_product_history(request.user, product, 'order')
                product.stock -= item.quantity
                product.save(update_fields=['stock'])

            if coupon and discount > 0:
                coupon.used_count += 1
                coupon.save(update_fields=['used_count'])
            cart.items.all().delete()

        request.session.pop('demo_payment_order_id', None)
        request.session.pop('demo_payment_shipping_method', None)
        request.session.pop('demo_payment_amount', None)
        request.session.pop('applied_coupon', None)
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=f'Payment received for order #{order.pk}',
                message=f'Hello {order.name}, payment for order #{order.pk} has been verified. Total: ₹{order.total_amount}.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )
        except Exception:
            pass
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('order_success'),
        })

    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cart not found.'}, status=404)

# payments/views.py
# ----------------------------------------------------
# This file runs the "online payment" checkout. It's a DEMO
# payment flow (no real money moves), but it's still written
# carefully: we never trust the browser blindly, we always
# double check stock and prices on the server before saving
# an order.
# ----------------------------------------------------

import uuid
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_POST

from cart.models import Cart
from orders.models import Order, OrderItem
from products.models import Product


# Small helper: adds up price * quantity for every item in the cart.
def _cart_total(cart_items):
    return sum(
        (item.product.price * item.quantity for item in cart_items),
        Decimal('0.00')
    )


# Step 1 of the demo payment: create a fake "order" reference and
# send it back to the page as JSON, so the payment popup can open.
@login_required
@require_POST
def create_payment_order(request):
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

    amount = int(_cart_total(cart_items) * 100)
    demo_order_id = f'order_DEMO{uuid.uuid4().hex[:14]}'

    # The demo order reference is stored server-side so verify_payment
    # cannot accept an arbitrary order id supplied by a client.
    request.session['demo_payment_order_id'] = demo_order_id
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'razorpay_order_id': demo_order_id,
        'amount': amount,
        'currency': 'INR',
        'name': 'E-Commerce Store',
        'description': 'Order payment (Demo - no real charge)',
    })


# Step 2 of the demo payment: check everything is still valid
# (stock, prices, session) and only THEN create the real Order.
@login_required
@require_POST
def verify_payment(request):
    razorpay_payment_id = request.POST.get('razorpay_payment_id', '').strip()
    razorpay_order_id = request.POST.get('razorpay_order_id', '').strip()

    expected_order_id = request.session.get('demo_payment_order_id')
    if not expected_order_id or razorpay_order_id != expected_order_id:
        return JsonResponse({
            'success': False,
            'error': 'Invalid or expired payment session. Please start payment again.'
        }, status=400)

    if not razorpay_payment_id.startswith('pay_DEMO'):
        return JsonResponse({
            'success': False,
            'error': 'Invalid demo payment reference.'
        }, status=400)

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()

    if not all([name, email, phone, address]):
        return JsonResponse({
            'success': False,
            'error': 'Please provide all customer information.'
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
                total += product.price * item.quantity

            order = Order.objects.create(
                user=request.user,
                name=name,
                email=email,
                phone=phone,
                address=address,
                total_amount=total,
                payment_method='razorpay (demo)',
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
                    price=product.price,
                )
                product.stock -= item.quantity
                product.save(update_fields=['stock'])

            cart.items.all().delete()

        request.session.pop('demo_payment_order_id', None)
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('order_success'),
        })

    except Cart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Cart not found.'}, status=404)

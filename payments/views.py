import uuid

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from cart.models import Cart, CartItem
from orders.models import Order, OrderItem


@login_required
@require_POST
def create_payment_order(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart not found.'
        }, status=404)

    cart_items = CartItem.objects.filter(cart=cart).select_related('product')

    if not cart_items.exists():
        return JsonResponse({
            'success': False,
            'error': 'Your cart is empty.'
        }, status=400)

    total = 0

    for item in cart_items:
        if item.product.stock < item.quantity:
            return JsonResponse({
                'success': False,
                'error': f'Not enough stock for {item.product.name}.'
            }, status=400)

        total += item.product.price * item.quantity

    amount = int(total * 100)

    # DEMO MODE: no real Razorpay order is created and no network call
    # is made to Razorpay. A fake order id is generated so the checkout
    # page can simulate the payment popup without any real charge.
    demo_order_id = f'order_DEMO{uuid.uuid4().hex[:14]}'

    return JsonResponse({
        'success': True,
        'razorpay_order_id': demo_order_id,
        'amount': amount,
        'currency': 'INR',
        'name': 'E-Comerce Store',
        'description': 'Order payment (Demo - no real charge)'
    })


@login_required
@require_POST
def verify_payment(request):
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()

    if not all([razorpay_payment_id, razorpay_order_id]):
        return JsonResponse({
            'success': False,
            'error': 'Payment information is missing.'
        }, status=400)

    if not all([name, email, phone, address]):
        return JsonResponse({
            'success': False,
            'error': 'Please provide all customer information.'
        }, status=400)

    # DEMO MODE: there is no real Razorpay signature to verify here,
    # since no real payment gateway was ever contacted. The payment is
    # simulated as always successful once the demo popup is confirmed.

    try:
        with transaction.atomic():
            cart = Cart.objects.select_for_update().get(
                user=request.user
            )

            cart_items = list(
                cart.items.select_related('product').select_for_update()
            )

            if not cart_items:
                return JsonResponse({
                    'success': False,
                    'error': 'Your cart is empty.'
                }, status=400)

            total = 0

            for item in cart_items:
                if item.quantity > item.product.stock:
                    return JsonResponse({
                        'success': False,
                        'error': (
                            f'Sorry, only {item.product.stock} '
                            f'units of {item.product.name} are available.'
                        )
                    }, status=400)

                total += item.product.price * item.quantity

            order = Order.objects.create(
                user=request.user,
                name=name,
                email=email,
                phone=phone,
                address=address,
                total_amount=total,
                payment_method='razorpay (demo)',
                payment_status='Paid',
                status='Confirmed',
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id
            )

            for item in cart_items:
                product = item.product

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price
                )

                product.stock -= item.quantity
                product.save(update_fields=['stock'])

            cart.items.all().delete()

    except Cart.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Cart not found.'
        }, status=404)

    return JsonResponse({
        'success': True,
        'redirect_url': '/order_success/'
    })

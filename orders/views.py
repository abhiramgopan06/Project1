# orders/views.py
# ----------------------------------------------------
# This file handles the checkout flow: turning a cart into a
# real order, and showing order history / order details.
# ----------------------------------------------------

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from cart.models import Cart
from products.models import Product
from .models import Order, OrderItem


# The checkout page. On a normal visit it just shows the order
# summary and the form. When the form is submitted (POST), it
# creates the real Order and empties the cart.
@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('product')

    if not cart_items.exists():
        return render(request, 'orders/checkout.html', {'cart_items': cart_items, 'total': 0})

    total = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        payment = request.POST.get('payment', 'cod')

        if not name or not email or not phone or not address:
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items, 'total': total,
                'error': 'Please fill in all customer information.'
            })

        if payment == 'online':
            # Online payment is finalized by payments.verify_payment.
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items, 'total': total,
                'error': 'Please use the Online Payment button to complete payment.'
            })

        try:
            with transaction.atomic():
                # We "lock" the cart items and products here so that if two
                # people check out the same product at the exact same time,
                # we don't accidentally sell more than we have in stock.
                locked_items = list(
                    cart.items.select_related('product').select_for_update()
                )
                product_ids = [item.product_id for item in locked_items]
                locked_products = {
                    p.pk: p
                    for p in Product.objects.select_for_update().filter(pk__in=product_ids)
                }

                if not locked_items:
                    return render(request, 'orders/checkout.html', {
                        'cart_items': cart.items.select_related('product'), 'total': 0,
                        'error': 'Your cart is empty.'
                    })

                for item in locked_items:
                    product = locked_products[item.product_id]
                    if item.quantity > product.stock:
                        raise ValueError(
                            f'Sorry, only {product.stock} units of {product.name} are available.'
                        )

                current_total = sum(
                    locked_products[item.product_id].price * item.quantity
                    for item in locked_items
                )

                order = Order.objects.create(
                    user=request.user,
                    name=name,
                    email=email,
                    phone=phone,
                    address=address,
                    total_amount=current_total,
                    payment_method='cod',
                    payment_status='Pending',
                    status='Pending'
                )

                for item in locked_items:
                    product = locked_products[item.product_id]
                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item.quantity,
                        price=product.price
                    )
                    product.stock -= item.quantity
                    product.save(update_fields=['stock'])

                cart.items.all().delete()

        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, 'orders/checkout.html', {
                'cart_items': cart.items.select_related('product'),
                'total': total,
                'error': str(exc),
            })

        return redirect('order_success')

    return render(request, 'orders/checkout.html', {'cart_items': cart_items, 'total': total})


# Simple "thank you, your order was placed" page.
@login_required
def order_success(request):
    return render(request, 'orders/order_success.html')


# Shows a list of every order this user has made in the past,
# newest first.
@login_required
def order_history(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    return render(
        request,
        'orders/order_history.html',
        {'orders': orders}
    )


# Shows everything about one single order: the items, the
# address, and a little step-by-step delivery tracker.
@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

    # Build the little "Pending -> Confirmed -> Shipped -> Delivered"
    # tracker so the template can show which steps are already done.
    status_steps = None

    if order.status != Order.STATUS_CANCELLED:
        flow = [
            Order.STATUS_PENDING,
            Order.STATUS_CONFIRMED,
            Order.STATUS_SHIPPED,
            Order.STATUS_DELIVERED,
        ]
        current_index = flow.index(order.status) if order.status in flow else 0

        status_steps = [
            {'label': label, 'done': index <= current_index}
            for index, label in enumerate(flow)
        ]

    return render(
        request,
        'orders/order_detail.html',
        {
            'order': order,
            'status_steps': status_steps,
        }
    )

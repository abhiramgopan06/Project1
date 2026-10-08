
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Avg, F

from cart.models import Cart
from products.models import Product, ProductReview
from products.recommendations import record_product_history
from products.forms import ProductReviewForm
from accounts.checkout_helpers import resolve_checkout_address
from .models import Order, OrderItem, ReturnReplaceRequest


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.select_related('product')
    addresses = request.user.addresses.all()

    if not cart_items.exists():
        return render(request, 'orders/checkout.html', {'cart_items': cart_items, 'total': 0, 'addresses': addresses})

    total = sum(item.product.price * item.quantity for item in cart_items)

    if request.method == 'POST':
        payment = request.POST.get('payment', 'cod')

        name, email, phone, address, error = resolve_checkout_address(request)
        if error:
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items, 'total': total, 'addresses': addresses,
                'error': error
            })

        if payment == 'online':
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items, 'total': total, 'addresses': addresses,
                'error': 'Please use the Online Payment button to complete payment.'
            })

        try:
            with transaction.atomic():
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
                        'addresses': addresses,
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
                    record_product_history(request.user, product, 'order')
                    product.stock -= item.quantity
                    product.save(update_fields=['stock'])

                cart.items.all().delete()

        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, 'orders/checkout.html', {
                'cart_items': cart.items.select_related('product'),
                'total': total,
                'addresses': addresses,
                'error': str(exc),
            })

        return redirect('order_success')

    return render(request, 'orders/checkout.html', {'cart_items': cart_items, 'total': total, 'addresses': addresses})


@login_required
def order_success(request):
    return render(request, 'orders/order_success.html')


@login_required
def order_history(request):
    orders = Order.objects.filter(
        user=request.user
    ).order_by('-created_at')

    order_items = OrderItem.objects.filter(
        order__user=request.user
    ).select_related('product', 'order').order_by('-order__created_at', '-id')

    return render(
        request,
        'orders/order_history.html',
        {'orders': orders, 'order_items': order_items}
    )


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(
        Order,
        id=order_id,
        user=request.user
    )

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

    order_items = order.items.select_related('product', 'return_request')

    existing_reviews = {}
    if order.status == Order.STATUS_DELIVERED:
        product_ids = [item.product_id for item in order_items]
        for review in ProductReview.objects.filter(user=request.user, product_id__in=product_ids):
            existing_reviews[review.product_id] = review

    for item in order_items:
        item.existing_review = existing_reviews.get(item.product_id)
        try:
            item.return_request_obj = item.return_request
        except ReturnReplaceRequest.DoesNotExist:
            item.return_request_obj = None

    can_cancel = order.status in (Order.STATUS_PENDING, Order.STATUS_CONFIRMED, Order.STATUS_SHIPPED)

    for item in order_items:
        item.can_cancel_item = can_cancel and not item.is_cancelled

    return render(
        request,
        'orders/order_detail.html',
        {
            'order': order,
            'order_items': order_items,
            'status_steps': status_steps,
            'can_cancel': can_cancel,
        }
    )


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if request.method == 'POST':
        cancellable = (Order.STATUS_PENDING, Order.STATUS_CONFIRMED, Order.STATUS_SHIPPED)

        if order.status in cancellable:
            with transaction.atomic():
                for item in order.items.filter(is_cancelled=False):
                    Product.objects.filter(pk=item.product_id).update(stock=F('stock') + item.quantity)
                order.status = Order.STATUS_CANCELLED
                order.save(update_fields=['status'])
            messages.success(request, f'Order #{order.id} was cancelled.')
        else:
            messages.error(request, 'This order can no longer be cancelled.')

    return redirect('order_detail', order_id=order.id)


@login_required
def cancel_order_item(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    cancellable = (Order.STATUS_PENDING, Order.STATUS_CONFIRMED, Order.STATUS_SHIPPED)

    if request.method == 'POST':
        if item.is_cancelled:
            messages.error(request, 'This product is already cancelled.')
        elif order.status not in cancellable:
            messages.error(request, 'This product can no longer be cancelled.')
        else:
            with transaction.atomic():
                Product.objects.filter(pk=item.product_id).update(stock=F('stock') + item.quantity)

                item.is_cancelled = True
                item.save(update_fields=['is_cancelled'])

                order.total_amount = order.total_amount - item.line_total

                if not order.items.filter(is_cancelled=False).exists():
                    order.status = Order.STATUS_CANCELLED

                order.save(update_fields=['total_amount', 'status'])

            messages.success(request, f'"{item.product.name}" was cancelled.')

    return redirect('order_detail', order_id=order.id)


@login_required
def request_return_replace(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    if order.status != Order.STATUS_DELIVERED:
        messages.error(request, 'Return/Replace is only available after your order has been delivered.')
        return redirect('order_detail', order_id=order.id)

    if ReturnReplaceRequest.objects.filter(order_item=item).exists():
        messages.error(request, 'You have already submitted a request for this item.')
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        request_type = request.POST.get('request_type')
        reason = request.POST.get('reason', '').strip()

        allowed_types = []
        if item.product.is_returnable:
            allowed_types.append(ReturnReplaceRequest.REQUEST_RETURN)
        if item.product.is_replaceable:
            allowed_types.append(ReturnReplaceRequest.REQUEST_REPLACE)

        if request_type not in allowed_types:
            messages.error(request, 'That option is not available for this product.')
        else:
            ReturnReplaceRequest.objects.create(
                order_item=item,
                request_type=request_type,
                reason=reason,
            )
            messages.success(request, f'Your {request_type.lower()} request for "{item.product.name}" was submitted.')

    return redirect('order_detail', order_id=order.id)


@login_required
def rate_product(request, order_id, item_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    item = get_object_or_404(OrderItem, id=item_id, order=order)

    if order.status != Order.STATUS_DELIVERED:
        messages.error(request, 'You can rate a product once your order has been delivered.')
        return redirect('order_detail', order_id=order.id)

    if request.method == 'POST':
        existing_review = ProductReview.objects.filter(product=item.product, user=request.user).first()
        form = ProductReviewForm(request.POST, instance=existing_review)

        if form.is_valid():
            review = form.save(commit=False)
            review.product = item.product
            review.user = request.user
            review.save()

            Product.objects.filter(pk=item.product_id).update(
                rating_average=ProductReview.objects.filter(product_id=item.product_id).aggregate(v=Avg('rating'))['v'] or 0,
                rating_count=ProductReview.objects.filter(product_id=item.product_id).count(),
            )
            messages.success(request, f'Thanks! Your rating for {item.product.name} was saved.')
        else:
            messages.error(request, 'Please choose a star rating between 1 and 5.')

    return redirect('order_detail', order_id=order.id)

from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction

from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from .models import Payment
from .forms import PaymentForm

import razorpay

def checkout(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            user = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET))
            amount_paise = int(payment.amount * 100)
            resp = user.payment_link.create({
                'amount':amount_paise,
                'currency':'INR',
                'description':payment.description or 'Payment',
                'customer': {
                    'name': payment.user_name,
                    'email':payment.user_email,
                },
                'notify':{'sms':True, 'email':True},
                'callback_url':'http://127.0.0.1:8000/order_success'
            })
            print(resp)
            payment.razorpay_payment_link = resp['short_url']
            payment.payment_id = resp['id']
            payment.save()
            return redirect('payment_list')
    else:
        form = PaymentForm()

    return render(request, 'checkout.html',{'form':form})

def payments_list(request):
    payments = Payment.objects.all().order_by('-create_at')
    return render(request, 'payments_list.html', {'payments' :payments} )

def order_success(request):
    return HttpResponse('Payment Successfull')

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

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )

    try:
        razorpay_order = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Unable to create Razorpay order: {str(e)}'
        }, status=500)

    return JsonResponse({
        'success': True,
        'razorpay_order_id': razorpay_order['id'],
        'amount': amount,
        'currency': 'INR',
        'key': settings.RAZORPAY_KEY_ID,
        'name': 'E-Comerce Store',
        'description': 'Order payment'
    })

@login_required
@require_POST
def verify_payment(request):
    razorpay_payment_id = request.POST.get('razorpay_payment_id')
    razorpay_order_id = request.POST.get('razorpay_order_id')
    razorpay_signature = request.POST.get('razorpay_signature')

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()
    address = request.POST.get('address', '').strip()

    if not all([
        razorpay_payment_id,
        razorpay_order_id,
        razorpay_signature
    ]):
        return JsonResponse({
            'success': False,
            'error': 'Payment verification information is missing.'
        }, status=400)

    if not all([name, email, phone, address]):
        return JsonResponse({
            'success': False,
            'error': 'Please provide all customer information.'
        }, status=400)

    client = razorpay.Client(
        auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        )
    )

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({
            'success': False,
            'error': 'Payment verification failed.'
        }, status=400)
    except Exception:
        return JsonResponse({
            'success': False,
            'error': 'Unable to verify the payment.'
        }, status=400)

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
                payment_method='razorpay',
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
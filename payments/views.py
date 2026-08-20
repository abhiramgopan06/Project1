from django. shortcuts import render,redirect
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction

from cart.models import Cart, CartItem
from .models import Payment
from .forms import PaymentForm
import razorpay
from django.http import HttpResponse

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
        'order_id': razorpay_order['id'],
        'amount': amount,
        'currency': 'INR',
        'key': settings.RAZORPAY_KEY_ID
    })
from django. shortcuts import render,redirect
from django.conf import settings
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


from django.urls import path
from . import views

urlpatterns = [
    path('webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    path('create-order/', views.create_payment_order, name='create_payment_order'),
    path('verify/', views.verify_payment, name='verify_payment'),
]

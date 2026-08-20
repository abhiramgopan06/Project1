from django.urls import path
from . import views

urlpatterns = [
    path('create-order/', views.create_payment_order, name='create_payment_order'),
    path('verify/', views.verify_payment, name='verify_payment'),
    path('order_success/', views.order_success, name='order_success'),

]

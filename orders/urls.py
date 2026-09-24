from django.urls import path
from . import views


urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('order_success/', views.order_success, name='order_success'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('orders/<int:order_id>/rate/<int:item_id>/', views.rate_product, name='rate_product'),
    path('orders/<int:order_id>/return-replace/<int:item_id>/', views.request_return_replace, name='request_return_replace'),
]
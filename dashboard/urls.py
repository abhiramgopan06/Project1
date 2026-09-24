from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('orders/', views.dashboard_orders, name='orders'),
    path('orders/<int:order_id>/', views.dashboard_order_detail, name='order_detail'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('users/', views.dashboard_users, name='users'),
    path('products/', views.dashboard_products, name='products'),
    path('products/add/', views.dashboard_product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views.dashboard_product_edit, name='product_edit'),
    path('products/<int:product_id>/toggle/', views.dashboard_product_toggle, name='product_toggle'),
]

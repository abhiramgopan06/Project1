from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('staff/', views.staff_dashboard_home, name='staff_home'),
    path('integrations/', views.dashboard_integrations, name='integrations'),
    path('orders/', views.dashboard_orders, name='orders'),
    path('orders/<int:order_id>/', views.dashboard_order_detail, name='order_detail'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('users/', views.dashboard_users, name='users'),
    path('staff-activity/', views.dashboard_staff_activity, name='staff_activity'),
    path('users/<int:user_id>/toggle-staff/', views.toggle_staff_role, name='toggle_staff_role'),
    path('categories/', views.dashboard_categories, name='categories'),
    path('products/<int:product_id>/delete/', views.dashboard_product_delete, name='product_delete'),
    path('products/', views.dashboard_products, name='products'),
    path('offers/', views.dashboard_product_offers, name='product_offers'),
    path('offers/history/', views.dashboard_offer_history, name='offer_history'),
    path('offers/previous/', views.dashboard_previous_offers, name='previous_offers'),
    path('offers/categories/', views.dashboard_category_offers, name='category_offers'),
    path('offers/product/<int:product_id>/', views.dashboard_offer_detail, name='offer_detail'),
    path('products/add/', views.dashboard_product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views.dashboard_product_edit, name='product_edit'),
    path('products/<int:product_id>/toggle/', views.dashboard_product_toggle, name='product_toggle'),
]

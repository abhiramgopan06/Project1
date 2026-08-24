from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('orders/', views.dashboard_orders, name='orders'),
    path('orders/<int:order_id>/status/', views.update_order_status, name='update_order_status'),
    path('users/', views.dashboard_users, name='users'),
]

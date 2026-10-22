from django.urls import path
from . import views

app_name = 'storeextras'
urlpatterns = [
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/<int:product_id>/toggle/', views.wishlist_toggle, name='wishlist_toggle'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.notification_read, name='notification_read'),
    path('payments/', views.payment_history, name='payment_history'),
    path('returns/', views.return_history, name='return_history'),
    path('orders/<int:order_id>/invoice/', views.invoice, name='invoice'),
    path('admin/activity-history/', views.activity_history, name='activity_history'),
    path('admin/stock-history/', views.stock_history, name='stock_history'),
    path('admin/returns/', views.return_management, name='return_management'),
]

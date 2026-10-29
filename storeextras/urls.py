from django.urls import path
from . import views, commerce_views

app_name = 'storeextras'
urlpatterns = [
    path('wishlist/', views.wishlist, name='wishlist'),
    path('recently-viewed/', commerce_views.recently_viewed, name='recently_viewed'),
    path('coupons/apply/', commerce_views.apply_coupon, name='apply_coupon'),
    path('coupons/remove/', commerce_views.remove_coupon, name='remove_coupon'),
    path('orders/<int:order_id>/cancel-request/', commerce_views.cancel_order_request, name='cancel_order_request'),
    path('admin/analytics/', commerce_views.analytics, name='analytics'),
    path('admin/reports/orders.csv', commerce_views.export_orders_csv, name='export_orders_csv'),
    path('admin/reports/stock.csv', commerce_views.export_stock_csv, name='export_stock_csv'),
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

from django.urls import path
from . import views, commerce_views

app_name = 'storeextras'
urlpatterns = [
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    path('admin/reports/sales.xlsx', commerce_views.export_sales_excel, name='export_sales_excel'),
    path('admin/reports/inventory.xlsx', commerce_views.export_inventory_excel, name='export_inventory_excel'),
    path('admin/reports/refunds.xlsx', commerce_views.export_refunds_excel, name='export_refunds_excel'),
    path('admin/products/import-csv/', commerce_views.import_products_csv, name='import_products_csv'),
    path('wishlist/', views.wishlist, name='wishlist'),
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

from django.contrib import admin

# Payments are managed through the Order admin (orders/admin.py), since
# every payment is tied to an order's payment_method / payment_status.

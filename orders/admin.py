
from django.contrib import admin
from .models import Order, OrderItem, ReturnReplaceRequest

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'name',
        'phone',
        'address',
        'total_amount',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'created_at',
    )

    search_fields = (
        'user__username',
        'name',
        'email',
        'phone',
        'address',
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'product',
        'quantity',
        'price',
    )

@admin.register(ReturnReplaceRequest)
class ReturnReplaceRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_item',
        'request_type',
        'reason_category',
        'status',
        'created_at',
    )

    list_filter = ('request_type', 'reason_category', 'status')
    search_fields = ('reason', 'order_item__product__name', 'order_item__order__user__username')


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
        'tracking_number',
        'courier_name',
        'estimated_delivery',
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
        'id',
        'customer_name',
        'customer_email',
        'order_item',
        'request_type',
        'reason_category',
        'status',
        'product_condition',
        'refund_status',
        'refund_amount',
        'created_at',
    )

    list_filter = ('request_type', 'reason_category', 'status', 'product_condition', 'refund_status', 'created_at')
    search_fields = ('reason', 'inspection_note', 'order_item__product__name', 'order_item__order__user__username', 'order_item__order__name', 'order_item__order__email', 'order_item__order__phone')
    readonly_fields = ('created_at', 'updated_at', 'received_at')

    @admin.display(description='Customer')
    def customer_name(self, obj):
        return obj.order_item.order.name

    @admin.display(description='Customer email')
    def customer_email(self, obj):
        return obj.order_item.order.email

from .models import Coupon
admin.site.register(Coupon)

from django.contrib import admin
from .models import WishlistItem, Notification, PaymentRecord, StockMovement, ActivityLog, BackInStockAlert

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')

@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'amount', 'method', 'status', 'created_at')
    list_filter = ('status', 'method')

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'change', 'stock_after', 'reason', 'changed_by', 'created_at')
    list_filter = ('reason', 'created_at')

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('actor', 'action', 'object_type', 'object_id', 'created_at')
    list_filter = ('action', 'object_type', 'created_at')
    search_fields = ('actor__username', 'details', 'object_id')


@admin.register(BackInStockAlert)
class BackInStockAlertAdmin(admin.ModelAdmin):
    list_display = ('product', 'variant', 'email', 'is_notified', 'created_at', 'notified_at')
    list_filter = ('is_notified', 'created_at')
    search_fields = ('product__name', 'email')

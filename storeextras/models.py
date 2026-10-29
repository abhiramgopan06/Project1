from django.conf import settings
from django.db import models
from django.utils import timezone

class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'product'], name='unique_user_wishlist_product')]
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.user.username}: {self.product.name}'

class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='store_notifications')
    title = models.CharField(max_length=160)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.user.username}: {self.title}'

class PaymentRecord(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_SUCCESS = 'Successful'
    STATUS_FAILED = 'Failed'
    STATUS_REFUNDED = 'Refunded'
    STATUS_CHOICES = [(STATUS_PENDING, 'Pending'), (STATUS_SUCCESS, 'Successful'), (STATUS_FAILED, 'Failed'), (STATUS_REFUNDED, 'Refunded')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_records')
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payment_records')
    reference = models.CharField(max_length=150, blank=True)
    method = models.CharField(max_length=50, default='cod')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'Payment for order #{self.order_id} - {self.status}'

class StockMovement(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, related_name='stock_movements')
    product_name = models.CharField(max_length=200)
    change = models.IntegerField()
    stock_after = models.PositiveIntegerField()
    reason = models.CharField(max_length=160)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.product_name}: {self.change:+d}'

class ActivityLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='store_activity')
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=80, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return f'{self.action} - {self.created_at:%Y-%m-%d %H:%M}'


class StockReservation(models.Model):
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reservations')
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE, null=True, blank=True, related_name='reservations')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stock_reservations')
    quantity = models.PositiveIntegerField()
    reference = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    released = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['expires_at']
        indexes = [models.Index(fields=['released', 'expires_at'], name='stx_res_exp_idx')]

    def __str__(self):
        return f'{self.product.name}: {self.quantity} reserved'

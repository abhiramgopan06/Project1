from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from orders.models import Order
from products.models import Product
from .models import ActivityLog, Notification, PaymentRecord, StockMovement
from .actor_context import get_current_actor

@receiver(pre_save, sender=Order)
def remember_order_status(sender, instance, **kwargs):
    instance._old_order_status = None
    if instance.pk:
        instance._old_order_status = sender.objects.filter(pk=instance.pk).values_list('status', flat=True).first()

@receiver(post_save, sender=Order)
def record_order_events(sender, instance, created, **kwargs):
    if created:
        PaymentRecord.objects.get_or_create(order=instance, user=instance.user, defaults={'amount': instance.total_amount, 'method': instance.payment_method, 'status': PaymentRecord.STATUS_PENDING, 'note': 'Initial order payment record'})
        Notification.objects.create(user=instance.user, title=f'Order #{instance.pk} placed', message='Your order was created successfully. You can follow its progress from My Orders.', link=f'/orders/{instance.pk}/')
        ActivityLog.objects.create(actor=instance.user, action='Order created', object_type='Order', object_id=instance.pk, details=f'Order total: {instance.total_amount}')
    else:
        old_status = getattr(instance, '_old_order_status', None)
        if old_status and old_status != instance.status:
            actor = get_current_actor()
            ActivityLog.objects.create(actor=actor if actor and actor.is_authenticated else None, action='Order status changed', object_type='Order', object_id=instance.pk, details=f'{old_status} to {instance.status}')
            Notification.objects.create(user=instance.user, title=f'Order #{instance.pk} updated', message=f'Your order status is now {instance.status}.', link=f'/orders/{instance.pk}/')

@receiver(pre_save, sender=Product)
def remember_stock(sender, instance, **kwargs):
    instance._old_stock_value = sender.objects.filter(pk=instance.pk).values_list('stock', flat=True).first() if instance.pk else None

@receiver(post_save, sender=Product)
def record_stock_changes(sender, instance, created, **kwargs):
    old_stock = getattr(instance, '_old_stock_value', None)
    actor = get_current_actor()
    actor = actor if actor and actor.is_authenticated and actor.is_staff else None
    if created:
        StockMovement.objects.create(product=instance, product_name=instance.name, change=instance.stock, stock_after=instance.stock, reason='Product created', changed_by=actor)
    elif old_stock is not None and old_stock != instance.stock:
        StockMovement.objects.create(product=instance, product_name=instance.name, change=instance.stock-old_stock, stock_after=instance.stock, reason='Stock updated', changed_by=actor)

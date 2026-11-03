from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from products.models import Product, ProductVariant
from .models import BackInStockAlert, Notification, StockMovement

def send_stock_alert(alert, subject, message, notification_title, notification_message, product_id):
    if alert.user_id:
        Notification.objects.create(
            user=alert.user,
            title=notification_title,
            message=notification_message,
            link=f'/product/{product_id}/',
        )
    sent = send_mail(
        subject=subject,
        message=message,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        recipient_list=[alert.email],
        fail_silently=True,
    )
    if sent:
        alert.is_notified = True
        alert.notified_at = timezone.now()
        alert.save(update_fields=['is_notified', 'notified_at'])

@receiver(pre_save, sender=Product)
def remember_product_stock(sender, instance, **kwargs):
    instance._previous_stock = sender.objects.filter(pk=instance.pk).values_list('stock', flat=True).first() if instance.pk else 0

@receiver(post_save, sender=Product)
def record_product_stock_change(sender, instance, created, **kwargs):
    previous = getattr(instance, '_previous_stock', 0) or 0
    change = instance.stock - previous
    if change:
        StockMovement.objects.create(
            product=instance,
            product_name=instance.name,
            change=change,
            stock_after=instance.stock,
            reason='Product stock increased' if change > 0 else 'Product stock decreased',
        )
    if change <= 0:
        return
    alerts = BackInStockAlert.objects.filter(product=instance, variant__isnull=True, is_notified=False)
    for alert in alerts:
        send_stock_alert(
            alert,
            f'{instance.name} is back in stock',
            f'Good news! {instance.name} is available again. Visit ShopEasy to order: {getattr(settings, "SITE_URL", "")}/product/{instance.pk}/',
            'Product back in stock',
            f'{instance.name} is available again.',
            instance.pk,
        )

@receiver(pre_save, sender=ProductVariant)
def remember_variant_stock(sender, instance, **kwargs):
    instance._previous_stock = sender.objects.filter(pk=instance.pk).values_list('stock', flat=True).first() if instance.pk else 0

@receiver(post_save, sender=ProductVariant)
def record_variant_stock_change(sender, instance, created, **kwargs):
    previous = getattr(instance, '_previous_stock', 0) or 0
    change = instance.stock - previous
    if change:
        StockMovement.objects.create(
            product=instance.product,
            product_name=f'{instance.product.name} - {instance.display_value}',
            change=change,
            stock_after=instance.stock,
            reason='Variant stock increased' if change > 0 else 'Variant stock decreased',
        )
    if change <= 0:
        return
    alerts = BackInStockAlert.objects.filter(product=instance.product, variant=instance, is_notified=False)
    for alert in alerts:
        send_stock_alert(
            alert,
            f'{instance.product.name} ({instance.display_value}) is back in stock',
            f'Good news! {instance.product.name} ({instance.display_value}) is available again. Visit ShopEasy to order.',
            'Selected option back in stock',
            f'{instance.product.name} ({instance.display_value}) is available again.',
            instance.product_id,
        )

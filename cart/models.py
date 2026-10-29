from django.db import models
from django.contrib.auth.models import User
from products.models import Product

class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart - {self.user.username}"

class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    quantity = models.PositiveIntegerField(default=1)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True, related_name='cart_items')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'product', 'variant'],
                name='unique_cart_product_variant',
            )
        ]

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    @property
    def total_price(self):
    
        unit_price = self.product.discounted_price
        if self.variant_id:
            unit_price += self.variant.price_adjustment
        return unit_price * self.quantity


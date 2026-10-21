from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    offer_percent = models.PositiveSmallIntegerField(default=0)
    offer_ends_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_offer_active(self):
        return bool(self.offer_percent and self.offer_ends_at and self.offer_ends_at > timezone.now())

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
                                                                        
    discount_percent = models.PositiveSmallIntegerField(default=0)
    discount_ends_at = models.DateTimeField(null=True, blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    is_returnable = models.BooleanField(default=False)
    is_replaceable = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vector_data = models.JSONField(default=dict, blank=True)
    rating_average = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    rating_count = models.PositiveIntegerField(default=0)

    @property
    def effective_discount_percent(self):
        if self.discount_percent and self.discount_ends_at and self.discount_ends_at > timezone.now():
            return self.discount_percent
        if self.category and self.category.is_offer_active:
            return self.category.offer_percent
        return 0

    @property
    def discounted_price(self):
        percent = self.effective_discount_percent
        if percent:
            discounted = self.price * (100 - percent) / 100
            return discounted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return self.price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def refresh_vector(self):
        from .recommendations import build_product_vector
        self.vector_data = build_product_vector(self)
        return self.vector_data

    def save(self, *args, **kwargs):
        update_fields = kwargs.get('update_fields')
        vector_fields = {'name', 'description', 'category'}
        if self.category_id and (
            not self.vector_data or update_fields is None or bool(vector_fields & set(update_fields))
        ):
            self.refresh_vector()
            if update_fields is not None:
                update_fields = set(update_fields)
                update_fields.add('vector_data')
                kwargs['update_fields'] = update_fields
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductReview(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='product_reviews'
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)]
    )
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='unique_product_review_per_user'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.product.name} - {self.user.username} ({self.rating}/5)'

class SearchHistory(models.Model):
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='search_history'
    )
    query = models.CharField(max_length=500)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='searches'
    )
    min_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    max_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username}: {self.query}'

class ProductHistory(models.Model):
    ACTION_VIEW = 'view'
    ACTION_CART = 'cart'
    ACTION_ORDER = 'order'

    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='product_history'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='user_history'
    )
    viewed_count = models.PositiveIntegerField(default=0)
    cart_count = models.PositiveIntegerField(default=0)
    ordered_count = models.PositiveIntegerField(default=0)
    search_count = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)
    last_interacted = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                name='unique_product_history_per_user'
            )
        ]
        ordering = ['-last_interacted']

    def __str__(self):
        return f'{self.user.username}: {self.product.name}'

class ProductOfferHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offer_history')
    discount_percent = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['recorded_at']

    def __str__(self):
        return f'{self.product.name} - {self.discount_percent}% offer'

class CategoryOfferHistory(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offer_history'
    )
    category_name = models.CharField(max_length=100)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(default=timezone.now)
    ends_at = models.DateTimeField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f'{self.category_name} - {self.discount_percent}% offer'

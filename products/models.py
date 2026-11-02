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

    @property
    def has_variants(self):
        return self.variants.filter(is_active=True).exists()

    @property
    def has_available_stock(self):
        active_variants = self.variants.filter(is_active=True)
        if active_variants.exists():
            return active_variants.filter(stock__gt=0).exists()
        return self.stock > 0

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
    is_approved = models.BooleanField(default=False, db_index=True)
    verified_purchase = models.BooleanField(default=False, db_index=True)
    moderated_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='moderated_product_reviews')
    moderated_at = models.DateTimeField(null=True, blank=True)
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


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=180, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.product.name} image {self.pk}'


class ProductVariant(models.Model):
    OPTION_SIZE = 'size'
    OPTION_COLOR = 'color'
    OPTION_STORAGE = 'storage'
    OPTION_OTHER = 'other'
    OPTION_TYPE_CHOICES = [
        (OPTION_SIZE, 'Size'),
        (OPTION_COLOR, 'Color'),
        (OPTION_STORAGE, 'Storage capacity'),
        (OPTION_OTHER, 'Other option'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=80, unique=True)
    size = models.CharField(max_length=40, blank=True)
    color = models.CharField(max_length=40, blank=True)
    option_type = models.CharField(max_length=20, choices=OPTION_TYPE_CHOICES, default=OPTION_SIZE)
    option_value = models.CharField(max_length=80, blank=True)
    price_adjustment = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['option_type', 'option_value', 'size', 'color']

    @property
    def display_value(self):
        return self.option_value or self.size or self.color or self.sku

    @property
    def effective_price(self):
        if self.price_override is not None:
            return self.price_override
        return self.product.discounted_price + self.price_adjustment

    def __str__(self):
        label = self.display_value
        return f'{self.product.name} - {label}'

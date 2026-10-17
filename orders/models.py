
from django.db import models
from django.contrib.auth.models import User
from cart.models import Cart


class Order(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_CONFIRMED = 'Confirmed'
    STATUS_SHIPPED = 'Shipped'
    STATUS_DELIVERED = 'Delivered'
    STATUS_CANCELLED = 'Cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    SHIPPING_FREE = 'free'
    SHIPPING_EXPRESS = 'express'
    SHIPPING_CHOICES = [
        (SHIPPING_FREE, 'Free Shipping'),
        (SHIPPING_EXPRESS, 'Express Shipping'),
    ]

    shipping_method = models.CharField(
        max_length=20,
        choices=SHIPPING_CHOICES,
        default=SHIPPING_FREE
    )
    shipping_cost = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    payment_method = models.CharField(
        max_length=50,
        default='cod'
    )

    payment_status = models.CharField(
        max_length=50,
        default='Pending'
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    razorpay_order_id = models.CharField(max_length=100, blank=True, default='')
    razorpay_payment_id = models.CharField(max_length=100, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

                                                             
    is_cancelled = models.BooleanField(default=False)

                                                                             
    @property
    def line_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


                                                           
                                                                 
                                                                  
                                  
class ReturnReplaceRequest(models.Model):
    REQUEST_RETURN = 'Return'
    REQUEST_REPLACE = 'Replace'

    REQUEST_TYPE_CHOICES = [
        (REQUEST_RETURN, 'Return'),
        (REQUEST_REPLACE, 'Replace'),
    ]

    STATUS_REQUESTED = 'Requested'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    STATUS_COMPLETED = 'Completed'

    STATUS_CHOICES = [
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_COMPLETED, 'Completed'),
    ]

                                                               
                                                        
    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.CASCADE,
        related_name='return_request'
    )

    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    reason = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_REQUESTED
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.request_type} request for {self.order_item}'
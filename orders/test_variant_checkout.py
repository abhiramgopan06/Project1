from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from cart.models import Cart, CartItem
from products.models import Category, Product, ProductVariant
from .models import Order, OrderItem

@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class VariantCheckoutTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='variant-checkout-customer',
            email='checkout@example.com',
            password='TestPass123!',
        )
        category = Category.objects.create(name='Shoes')
        product = Product.objects.create(
            category=category,
            name='Running Shoe',
            description='A test shoe',
            price=Decimal('80.00'),
            stock=0,
            is_available=True,
        )
        self.product = product
        self.variant = ProductVariant.objects.create(
            product=product,
            sku='CHECKOUT-SHOE-42',
            option_type=ProductVariant.OPTION_SIZE,
            option_value='42',
            size='42',
            price_override=Decimal('125.00'),
            stock=3,
            is_active=True,
        )
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=product, variant=self.variant, quantity=2)
        self.client.force_login(self.user)

    def test_checkout_uses_variant_price_and_stock(self):
        response = self.client.post(reverse('checkout'), {
            'payment': 'cod',
            'shipping_method': 'free',
            'address_id': 'new',
            'name': 'Test Customer',
            'email': 'checkout@example.com',
            'phone': '9876543210',
            'address': 'Test street, Kerala',
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.user)
        item = OrderItem.objects.get(order=order)
        self.variant.refresh_from_db()
        self.assertEqual(item.variant_id, self.variant.pk)
        self.assertEqual(item.price, Decimal('125.00'))
        self.assertEqual(order.total_amount, Decimal('250.00'))
        self.assertEqual(self.variant.stock, 1)

    def test_cancelling_order_restores_variant_stock(self):
        self.client.post(reverse('checkout'), {
            'payment': 'cod',
            'shipping_method': 'free',
            'address_id': 'new',
            'name': 'Test Customer',
            'email': 'checkout@example.com',
            'phone': '9876543210',
            'address': 'Test street, Kerala',
        })
        order = Order.objects.get(user=self.user)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 1)
        response = self.client.post(reverse('cancel_order', args=[order.pk]))
        self.assertEqual(response.status_code, 302)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock, 3)

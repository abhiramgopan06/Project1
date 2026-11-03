from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from cart.models import Cart, CartItem
from products.models import Category, Product, ProductVariant
from .models import BackInStockAlert

class ProductVariantTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='variant-customer',
            email='customer@example.com',
            password='TestPass123!',
        )
        self.category = Category.objects.create(name='Clothing')
        self.product = Product.objects.create(
            category=self.category,
            name='Everyday Shirt',
            description='A test shirt',
            price=Decimal('100.00'),
            stock=0,
            is_available=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='SHIRT-XL',
            option_type=ProductVariant.OPTION_SIZE,
            option_value='XL',
            size='XL',
            price_override=Decimal('125.00'),
            stock=3,
            is_active=True,
        )

    def test_variant_price_is_used_for_cart_total(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, variant=self.variant, quantity=2)
        self.assertEqual(item.total_price, Decimal('250.00'))

    def test_add_to_cart_requires_and_uses_variant(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('cart:add_to_cart', args=[self.product.pk]),
            {'variant_id': self.variant.pk},
        )
        self.assertEqual(response.status_code, 302)
        item = CartItem.objects.get(cart__user=self.user, product=self.product, variant=self.variant)
        self.assertEqual(item.quantity, 1)

class BackInStockAlertTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Shoes')
        self.product = Product.objects.create(
            category=self.category,
            name='Running Shoe',
            description='A test shoe',
            price=Decimal('80.00'),
            stock=0,
            is_available=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='SHOE-42',
            option_type=ProductVariant.OPTION_SIZE,
            option_value='42',
            size='42',
            stock=0,
            is_active=True,
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_alert_emails_customer_when_variant_stock_returns(self):
        response = self.client.post(
            reverse('storeextras:request_stock_alert', args=[self.product.pk]),
            {'variant_id': self.variant.pk, 'email': 'buyer@example.com'},
        )
        self.assertEqual(response.status_code, 302)
        alert = BackInStockAlert.objects.get(product=self.product, variant=self.variant, email='buyer@example.com')
        self.variant.stock = 4
        self.variant.save(update_fields=['stock'])
        alert.refresh_from_db()
        self.assertTrue(alert.is_notified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Running Shoe', mail.outbox[0].subject)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_alert_emails_customer_when_product_stock_returns(self):
        response = self.client.post(
            reverse('storeextras:request_stock_alert', args=[self.product.pk]),
            {'email': 'product-buyer@example.com'},
        )
        self.assertEqual(response.status_code, 302)
        alert = BackInStockAlert.objects.get(product=self.product, variant__isnull=True, email='product-buyer@example.com')
        self.product.stock = 5
        self.product.save(update_fields=['stock'])
        alert.refresh_from_db()
        self.assertTrue(alert.is_notified)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Running Shoe', mail.outbox[0].subject)

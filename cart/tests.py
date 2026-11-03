from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from products.models import Category, Product, ProductVariant
from .models import Cart, CartItem

class CartPricingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='cartcustomer',
            password='Testpass123!',
        )
        self.category = Category.objects.create(name='Clothing')
        self.product = Product.objects.create(
            category=self.category,
            name='Everyday T-Shirt',
            description='Cotton T-shirt',
            price=500,
            stock=0,
            is_available=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku='TSHIRT-XL-TEST',
            option_type=ProductVariant.OPTION_SIZE,
            option_value='XL',
            price_override=Decimal('575.00'),
            stock=5,
        )
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            variant=self.variant,
            quantity=2,
        )

    def test_cart_total_uses_selected_variant_price(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('cart:cart'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], Decimal('1150.00'))

    def test_cart_page_includes_variant_details(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('cart:cart'))

        self.assertContains(response, 'XL')
        self.assertContains(response, '575.00')

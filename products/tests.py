from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Category, Product, ProductHistory, SearchHistory
from .recommendations import recommended_products, record_product_history


class RecommendationHistoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='Testpass123!')
        self.category = Category.objects.create(name='Electronics')
        self.mouse = Product.objects.create(
            category=self.category,
            name='Gaming Mouse',
            description='RGB gaming mouse',
            price=499,
            stock=10,
            is_available=True,
        )
        self.keyboard = Product.objects.create(
            category=self.category,
            name='Gaming Keyboard',
            description='RGB gaming keyboard',
            price=999,
            stock=10,
            is_available=True,
        )
        self.book = Product.objects.create(
            category=Category.objects.create(name='Books'),
            name='Python Book',
            description='Learn Python programming',
            price=500,
            stock=10,
            is_available=True,
        )

    def test_search_is_saved(self):
        self.client.login(username='testuser', password='Testpass123!')
        response = self.client.get(reverse('products:home'), {'q': 'Gaming'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(SearchHistory.objects.filter(user=self.user).exists())
        self.assertTrue(ProductHistory.objects.filter(user=self.user, product=self.mouse, search_count=1).exists())

    def test_view_and_cart_history_are_saved(self):
        self.client.login(username='testuser', password='Testpass123!')
        self.client.get(reverse('products:product_detail', args=[self.mouse.id]))
        self.assertEqual(ProductHistory.objects.get(user=self.user, product=self.mouse).viewed_count, 1)
        self.client.post(reverse('cart:add_to_cart', args=[self.mouse.id]), {'next': reverse('products:home')})
        self.assertEqual(ProductHistory.objects.get(user=self.user, product=self.mouse).cart_count, 1)

    def test_recommendations_use_history(self):
        record_product_history(self.user, self.mouse, 'view')
        record_product_history(self.user, self.mouse, 'cart')
        record_product_history(self.user, self.mouse, 'order')
        results = recommended_products(self.user, limit=3)
        self.assertTrue(results)
        self.assertIn(self.mouse, results)

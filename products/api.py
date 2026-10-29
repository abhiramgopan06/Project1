from rest_framework import serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product, Category, ProductReview
from orders.models import Order

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category', 'category_name', 'price', 'discounted_price', 'discount_percent', 'stock', 'image', 'rating_average', 'rating_count', 'is_available']

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'username', 'rating', 'review', 'created_at']
        read_only_fields = ['id', 'username', 'created_at']

class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Product.objects.filter(is_available=True, stock__gt=0).select_related('category').prefetch_related('gallery_images', 'variants')
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'created_at', 'rating_average', 'rating_count']
    ordering = ['-created_at']

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    queryset = Category.objects.all().order_by('name')

class MyOrderViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = None
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related('items__product').order_by('-created_at')
    def list(self, request):
        rows = self.get_queryset().values('id', 'status', 'payment_status', 'total_amount', 'created_at', 'tracking_number', 'courier_name', 'estimated_delivery')
        return Response(list(rows))
    def retrieve(self, request, pk=None):
        order = self.get_queryset().filter(pk=pk).first()
        if order is None:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        return Response({'id': order.pk, 'status': order.status, 'payment_status': order.payment_status, 'total_amount': str(order.total_amount), 'created_at': order.created_at, 'tracking_number': order.tracking_number, 'courier_name': order.courier_name, 'estimated_delivery': order.estimated_delivery, 'items': [{'product': item.product.name, 'quantity': item.quantity, 'price': str(item.price)} for item in order.items.all()]})

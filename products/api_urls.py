from rest_framework.routers import DefaultRouter
from .api import ProductViewSet, CategoryViewSet, MyOrderViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='api-products')
router.register('categories', CategoryViewSet, basename='api-categories')
router.register('my-orders', MyOrderViewSet, basename='api-my-orders')
urlpatterns = router.urls


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from payments import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('products.urls')),
    path('', include('cart.urls')),
    path('accounts/', include('accounts.urls')),
    path('', include('orders.urls')),
    path('payments/', include('payments.urls')),
    path('payment_list/',views.payments_list,name='payment_list'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

  
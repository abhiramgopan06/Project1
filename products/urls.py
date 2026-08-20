from django.urls import path
from . import views


app_name = 'products'


urlpatterns = [

    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'product/<int:id>/',
        views.product_detail,
        name='product_detail'
    ),

]
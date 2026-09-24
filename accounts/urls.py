
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    path(
        'register/',
        views.register,
        name='register'
    ),

    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='accounts/login.html'
        ),
        name='login'
    ),

    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),

    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'addresses/add/',
        views.address_add,
        name='address_add'
    ),

    path(
        'addresses/<int:address_id>/edit/',
        views.address_edit,
        name='address_edit'
    ),

    path(
        'addresses/<int:address_id>/delete/',
        views.address_delete,
        name='address_delete'
    ),
]
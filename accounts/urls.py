from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # ---- Sign up + email OTP ----
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),

    # ---- Login / logout ----
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # ---- Continue with Google ----
    path('google/login/', views.google_login, name='google_login'),
    path('google/callback/', views.google_callback, name='google_callback'),

    # ---- Profile and saved addresses ----
    path('profile/', views.profile, name='profile'),
    path('addresses/add/', views.address_add, name='address_add'),
    path('addresses/<int:address_id>/edit/', views.address_edit, name='address_edit'),
    path('addresses/<int:address_id>/delete/', views.address_delete, name='address_delete'),
]

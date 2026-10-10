from django.contrib import admin
from .models import UserProfile, Address, EmailOTP

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'phone', 'city', 'state', 'pincode')
    search_fields = ('user__username', 'user__email', 'phone', 'city')
    readonly_fields = ('vector_data',)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'label', 'full_name', 'phone', 'is_default', 'created_at')
    list_filter = ('is_default',)
    search_fields = ('user__username', 'full_name', 'phone', 'address')


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'attempts')
    search_fields = ('user__username', 'user__email')
    # The code is stored hashed, so there is nothing useful to edit.
    readonly_fields = ('code_hash',)

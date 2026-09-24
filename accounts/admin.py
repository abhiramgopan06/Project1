from django.contrib import admin
from .models import UserProfile, Address

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

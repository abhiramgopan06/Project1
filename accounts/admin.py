from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'phone',
        'city',
        'state',
        'pincode',
    )

    search_fields = (
        'user__username',
        'user__email',
        'phone',
        'city',
    )

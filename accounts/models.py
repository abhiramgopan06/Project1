
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    phone = models.CharField(max_length=15, blank=True)

    address = models.TextField(blank=True)

    city = models.CharField(max_length=100, blank=True)

    state = models.CharField(max_length=100, blank=True)

    pincode = models.CharField(max_length=10, blank=True)
    vector_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.user.username


# A saved delivery address. A user can have more than one of these
# (home, a temporary place while traveling, a relative's house, etc).
# At checkout the user picks one instead of typing everything again.
class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )

    # A short label so the user can tell their addresses apart,
    # e.g. "Home", "Hostel", "Temporary".
    label = models.CharField(max_length=50, blank=True, default='Address')

    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f'{self.label} - {self.user.username}'
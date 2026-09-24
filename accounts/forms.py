from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Address


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
        ]


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'phone',
            'address',
            'city',
            'state',
            'pincode',
        ]


# A saved delivery address. Used both on the "My Addresses" page
# and on the checkout page when the user adds a new address.
class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['label', 'full_name', 'email', 'phone', 'address', 'is_default']
        widgets = {
            'label': forms.TextInput(attrs={'class': 'input', 'placeholder': 'e.g. Home, Hostel, Temporary'}),
            'full_name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'class': 'input', 'placeholder': 'Email address'}),
            'phone': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Phone number'}),
            'address': forms.Textarea(attrs={'class': 'input', 'rows': 4, 'placeholder': 'Complete delivery address'}),
        }
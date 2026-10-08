from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Address


class RegistrationForm(UserCreationForm):
    """Beginner-friendly registration form."""

    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, max_length=150)
    last_name = forms.CharField(required=True, max_length=150)
    phone = forms.CharField(
        required=True,
        max_length=15,
        widget=forms.TextInput(attrs={
            'type': 'tel',
            'inputmode': 'numeric',
            'pattern': '[0-9]{10,15}',
            'maxlength': '15',
            'autocomplete': 'tel',
        })
    )

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'password1',
            'password2',
        )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            raise forms.ValidationError('Phone number must contain 10 to 15 digits.')
        return phone


class UserForm(forms.ModelForm):
    """Form used to edit the logged-in user's basic information."""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
        widgets = {
            'email': forms.EmailInput(),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Another account already uses this email.')
        return email


class UserProfileForm(forms.ModelForm):
    """Form for the phone and profile delivery details."""

    class Meta:
        model = UserProfile
        fields = ('phone', 'address', 'city', 'state', 'pincode')

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if phone and (not phone.isdigit() or not 10 <= len(phone) <= 15):
            raise forms.ValidationError('Phone number must contain 10 to 15 digits.')
        return phone

    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode', '').strip()
        if pincode and (not pincode.isdigit() or len(pincode) != 6):
            raise forms.ValidationError('Pincode must contain 6 digits.')
        return pincode


class AddressForm(forms.ModelForm):
    """Form for saving a delivery address."""

    class Meta:
        model = Address
        fields = ('label', 'full_name', 'email', 'phone', 'address', 'is_default')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not phone.isdigit() or not 10 <= len(phone) <= 15:
            raise forms.ValidationError('Phone number must contain 10 to 15 digits.')
        return phone

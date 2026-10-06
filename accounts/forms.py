from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Address


class RegistrationForm(UserCreationForm):
    """Simple registration form with the fields used by the shop."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input',
            'placeholder': 'Enter your email address',
            'autocomplete': 'email',
        })
    )

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'First name',
        })
    )

    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': 'Last name',
        })
    )

    phone = forms.CharField(
        required=True,
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'input',
            'placeholder': '10-15 digit phone number',
            'type': 'tel',
            'inputmode': 'numeric',
            'pattern': '[0-9]{10,15}',
            'maxlength': '15',
            'autocomplete': 'tel',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Keep the registration page order simple and beginner-friendly.
        # Keep the fields in a natural registration order:
        # account name -> personal details -> contact -> password.
        # This matches the layout used by the other project and is
        # easier for a beginner to follow.
        self.order_fields([
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'password1',
            'password2',
        ])
        self.fields['password1'].widget.attrs.update({
            'class': 'input',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'input',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        })

    class Meta:
        model = User
        # The order here is the order shown on the registration page.
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Choose a username',
                'autocomplete': 'username',
            }),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not phone.isdigit():
            raise forms.ValidationError('Phone number must contain numbers only.')
        if not 10 <= len(phone) <= 15:
            raise forms.ValidationError('Phone number must be 10 to 15 digits.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
        return user


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
        ]
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': 'Email address',
                'autocomplete': 'email',
            }),
        }


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
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': '10-15 digit phone number',
                'type': 'tel',
                'inputmode': 'numeric',
                'pattern': '[0-9]{10,15}',
                'maxlength': '15',
            }),
            'pincode': forms.TextInput(attrs={
                'class': 'input',
                'inputmode': 'numeric',
                'pattern': '[0-9]*',
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if phone and (not phone.isdigit() or not 10 <= len(phone) <= 15):
            raise forms.ValidationError('Phone number must contain 10 to 15 digits only.')
        return phone


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['label', 'full_name', 'email', 'phone', 'address', 'is_default']
        widgets = {
            'label': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'e.g. Home, Hostel, Temporary'
            }),
            'full_name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Full name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input',
                'placeholder': 'Email address',
                'autocomplete': 'email',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': '10-15 digit phone number',
                'type': 'tel',
                'inputmode': 'numeric',
                'pattern': '[0-9]{10,15}',
                'maxlength': '15',
                'autocomplete': 'tel',
            }),
            'address': forms.Textarea(attrs={
                'class': 'input',
                'rows': 4,
                'placeholder': 'Complete delivery address'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip()
        if not phone.isdigit():
            raise forms.ValidationError('Phone number must contain numbers only.')
        if not 10 <= len(phone) <= 15:
            raise forms.ValidationError('Phone number must be 10 to 15 digits.')
        return phone

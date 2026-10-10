from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
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

    # Placeholder text and browser hints shown inside the boxes.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Choose a username', 'autocomplete': 'username'})
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'First name', 'autocomplete': 'given-name'})
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Last name', 'autocomplete': 'family-name'})
        self.fields['email'].widget.attrs.update({
            'placeholder': 'you@example.com', 'autocomplete': 'email'})
        self.fields['phone'].widget.attrs.update({
            'placeholder': '10 digit mobile number'})
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Create a password', 'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Re-enter the password', 'autocomplete': 'new-password'})

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


class LoginForm(AuthenticationForm):
    """Normal login form, plus one extra check: if the person registered
    but never entered the OTP, tell them (instead of "wrong password")."""

    # Set when the username + password are right but the email is not verified.
    unverified_user = None

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            user = User.objects.filter(username=username).first()

            # An account that is not active AND still has a pending OTP
            # is one that has not finished email verification.
            if (user is not None
                    and not user.is_active
                    and hasattr(user, 'email_otp')
                    and user.check_password(password)):
                self.unverified_user = user
                raise forms.ValidationError(
                    'Your email is not verified yet.',
                    code='unverified'
                )

        return super().clean()

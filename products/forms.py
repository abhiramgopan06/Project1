from django import forms
from .models import ProductReview, Product

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.Select(attrs={'class': 'select'}),
            'review': forms.Textarea(attrs={'class': 'input', 'rows': 4, 'placeholder': 'Write your review...'}),
        }


# Used by the staff dashboard to add and edit products - this is
# the "separate admin dashboard" product form (as opposed to the
# built-in Django /admin/ site).
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name', 'category', 'description', 'price', 'image', 'stock', 'is_available',
            'is_returnable', 'is_replaceable',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Product name'}),
            'category': forms.Select(attrs={'class': 'select'}),
            'description': forms.Textarea(attrs={'class': 'input', 'rows': 5, 'placeholder': 'Product description'}),
            'price': forms.NumberInput(attrs={'class': 'input', 'step': '0.01', 'min': '0'}),
            'stock': forms.NumberInput(attrs={'class': 'input', 'min': '0'}),
        }
        labels = {
            'is_returnable': 'Customers can return this product',
            'is_replaceable': 'Customers can replace this product',
        }

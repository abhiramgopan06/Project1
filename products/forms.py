from django import forms
from .models import ProductReview

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.Select(attrs={'class': 'select'}),
            'review': forms.Textarea(attrs={'class': 'input', 'rows': 4, 'placeholder': 'Write your review...'}),
        }

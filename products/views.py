
from django.shortcuts import render, get_object_or_404
from .models import Product, Category



def home(request):
    products = Product.objects.filter(
        is_available=True
    )

    q = request.GET.get('q')

    if q:
        products = products.filter(
            name__icontains=q
        )

    category = request.GET.get('category')

    if category:
        products = products.filter(
            category_id=category
        )

    min_price = request.GET.get('min_price')

    if min_price:
        products = products.filter(
            price__gte=min_price
        )

    max_price = request.GET.get('max_price')

    if max_price:
        products = products.filter(
            price__lte=max_price
        )

    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories,
    }

    return render(
        request,
        'products/home.html',
        context
    )


def product_detail(request, id):
    product = get_object_or_404(
        Product,
        id=id
    )

    return render(
        request,
        'products/product_details.html',
        {
            'product': product
        }
    )


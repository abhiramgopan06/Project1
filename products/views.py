from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Avg, Q

from .models import Product, Category, ProductReview
from .forms import ProductReviewForm
from .recommendations import add_to_user_vector, recommended_products
from accounts.models import UserProfile


def _record_search(request, q, category, min_price, max_price):
    if not request.user.is_authenticated:
        return
    from .models import SearchHistory
    query_text = ' '.join(filter(None, [q, category.name if category else '', min_price, max_price]))
    if query_text:
        SearchHistory.objects.create(user=request.user, query=query_text, category=category, min_price=min_price or None, max_price=max_price or None)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        add_to_user_vector(profile, query_text, weight=2)


def home(request):
    products = Product.objects.filter(is_available=True).select_related('category')
    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    category = None

    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q) | Q(category__name__icontains=q))
    if category_id:
        products = products.filter(category_id=category_id)
        category = Category.objects.filter(id=category_id).first()
    price_error = None
    min_price_value = None
    max_price_value = None

    if min_price:
        try:
            min_price_value = float(min_price)
            if min_price_value < 0:
                raise ValueError
        except (TypeError, ValueError):
            price_error = 'Minimum price must be a valid non-negative number.'
        else:
            products = products.filter(price__gte=min_price_value)

    if max_price and not price_error:
        try:
            max_price_value = float(max_price)
            if max_price_value < 0:
                raise ValueError
        except (TypeError, ValueError):
            price_error = 'Maximum price must be a valid non-negative number.'
        else:
            products = products.filter(price__lte=max_price_value)

    if min_price_value is not None and max_price_value is not None and min_price_value > max_price_value:
        price_error = 'Minimum price cannot be greater than maximum price.'
        products = Product.objects.none()

    _record_search(request, q, category, min_price, max_price)
    categories = Category.objects.all()
    recommendations = recommended_products(request.user, limit=6) if request.user.is_authenticated else []
    return render(request, 'products/home.html', {'products': products, 'categories': categories, 'recommendations': recommendations, 'price_error': price_error})


def product_detail(request, id):
    product = get_object_or_404(Product.objects.select_related('category'), id=id)
    if not product.vector_data:
        product.refresh_vector()
        product.save(update_fields=['vector_data'])

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        add_to_user_vector(profile, f'{product.name} {product.category.name}', weight=0.25)

    review = None
    if request.user.is_authenticated:
        review = ProductReview.objects.filter(product=product, user=request.user).first()

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        form = ProductReviewForm(request.POST, instance=review)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.product = product
            obj.user = request.user
            obj.save()
            add_to_user_vector(request.user.profile, f'{product.name} {product.category.name}', weight=float(obj.rating) * 1.5)
            Product.objects.filter(pk=product.pk).update(
                rating_average=ProductReview.objects.filter(product=product).aggregate(v=Avg('rating'))['v'] or 0,
                rating_count=ProductReview.objects.filter(product=product).count(),
            )
            messages.success(request, 'Your rating and review were saved.')
            return redirect('products:product_detail', id=product.id)
    else:
        form = ProductReviewForm(instance=review)

    reviews = product.reviews.select_related('user').all()
    recommendations = recommended_products(request.user, exclude_id=product.id, limit=4) if request.user.is_authenticated else list(Product.objects.filter(is_available=True).exclude(id=product.id).order_by('-rating_average')[:4])
    return render(request, 'products/product_details.html', {'product': product, 'form': form, 'reviews': reviews, 'recommendations': recommendations, 'user_review': review})

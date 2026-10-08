import re
from collections import Counter

STOP_WORDS = {
    'the','a','an','and','or','for','to','of','in','on','with','is','are','this','that',
    'by','from','at','as','be','it','your','you','new','best','more','all','one'
}


def tokenize(text):
    words = re.findall(r'[a-zA-Z0-9]+', (text or '').lower())
    return [w for w in words if len(w) > 1 and w not in STOP_WORDS]


def build_product_vector(product):
    text = f"{product.name} {product.description} {product.category.name if product.category_id else ''}"
    counts = Counter(tokenize(text))
    return dict(counts.most_common(80))


def add_to_user_vector(profile, text, weight=1):
    vector = dict(profile.vector_data or {})
    for token in tokenize(text):
        vector[token] = round(float(vector.get(token, 0)) + weight, 4)
    profile.vector_data = dict(sorted(vector.items(), key=lambda x: x[1], reverse=True)[:200])
    profile.save(update_fields=['vector_data'])


def record_product_history(user, product, action):
    from django.utils import timezone
    from .models import ProductHistory

    history, _ = ProductHistory.objects.get_or_create(user=user, product=product)
    if action == ProductHistory.ACTION_VIEW:
        history.viewed_count += 1
        history.last_viewed = timezone.now()
    elif action == ProductHistory.ACTION_CART:
        history.cart_count += 1
    elif action == ProductHistory.ACTION_ORDER:
        history.ordered_count += 1
    history.save()
    return history


def sync_existing_history(user):
    from django.db.models import Sum
    from .models import Product, ProductHistory, SearchHistory
    from cart.models import Cart
    from orders.models import OrderItem
    from accounts.models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=user)
    if not profile.vector_data:
        for search in SearchHistory.objects.filter(user=user):
            if search.query:
                add_to_user_vector(profile, search.query, weight=2)

    search_rows = {}
    for search in SearchHistory.objects.filter(user=user):
        query = search.query.split()[0] if search.query else ''
        if not query:
            continue
        matches = Product.objects.filter(
            name__icontains=query
        ) | Product.objects.filter(
            description__icontains=query
        ) | Product.objects.filter(
            category__name__icontains=query
        )
        for product_id in matches.values_list('id', flat=True).distinct()[:30]:
            search_rows[product_id] = search_rows.get(product_id, 0) + 1

    order_rows = {
        row['product_id']: row['total'] or 0
        for row in OrderItem.objects.filter(order__user=user).exclude(order__status='Cancelled')
        .values('product_id')
        .annotate(total=Sum('quantity'))
    }

    cart_rows = {}
    try:
        cart = Cart.objects.get(user=user)
        cart_rows = {
            row['product_id']: row['total'] or 0
            for row in cart.items.values('product_id').annotate(total=Sum('quantity'))
        }
    except Cart.DoesNotExist:
        pass

    product_ids = set(search_rows) | set(order_rows) | set(cart_rows)
    for product_id in product_ids:
        history, _ = ProductHistory.objects.get_or_create(user=user, product_id=product_id)
        history.search_count = max(history.search_count, search_rows.get(product_id, 0))
        history.ordered_count = max(history.ordered_count, order_rows.get(product_id, 0))
        history.cart_count = max(history.cart_count, cart_rows.get(product_id, 0))
        history.save()


def product_score(product, user_vector, history_map):
    score = 0.0
    pv = product.vector_data or {}
    for token, weight in user_vector.items():
        if token in pv:
            score += float(weight) * (1.0 + float(pv[token]))

    history = history_map.get(product.id)
    if history:
        score += history.viewed_count * 2.0
        score += history.cart_count * 3.0
        score += history.ordered_count * 5.0
        score += history.search_count * 4.0

    score += float(getattr(product, 'rating_average', 0) or 0) * 0.8
    return score


def recommended_products(user, exclude_id=None, limit=12):
    from .models import Product, ProductHistory

    products = list(Product.objects.filter(is_available=True).select_related('category'))
    sync_existing_history(user)
    history_map = {
        item.product_id: item
        for item in ProductHistory.objects.filter(user=user)
    }

    try:
        profile = user.profile
        user_vector = profile.vector_data or {}
    except Exception:
        user_vector = {}

    scored = [
        (product_score(product, user_vector, history_map), product)
        for product in products
        if product.id != exclude_id
    ]
    scored.sort(
        key=lambda item: (item[0], float(item[1].rating_average or 0), item[1].created_at),
        reverse=True
    )

    selected = [product for score, product in scored if score > 0][:limit]
    if len(selected) < limit:
        seen = {product.id for product in selected}
        fallback = [
            product for product in products
            if product.id not in seen and product.id != exclude_id
        ]
        selected.extend(fallback[:limit - len(selected)])
    return selected

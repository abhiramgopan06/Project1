import re
from collections import Counter
from decimal import Decimal

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


def product_score(product, user_vector):
    if not user_vector:
        return 0.0
    pv = product.vector_data or {}
    score = 0.0
    for token, weight in user_vector.items():
        if token in pv:
            score += float(weight) * (1.0 + float(pv[token]))
    score += float(getattr(product, 'rating_average', 0) or 0) * 0.8
    return score


def recommended_products(user, exclude_id=None, limit=12):
    from .models import Product, SearchHistory

    products = list(
        Product.objects.filter(is_available=True)
        .select_related('category')
    )

    try:
        profile = user.profile
    except Exception:
        profile = None

    user_vector = profile.vector_data if profile else {}

    # Use recent searches as an easy-to-understand extra signal.
    # A product matching the user's recent category or search words gets
    # a higher score, so recommendations change as the user shops.
    recent_history = list(
        SearchHistory.objects.filter(user=user)
        .select_related('category')
        .order_by('-created_at')[:10]
    )

    recent_words = Counter()
    recent_categories = Counter()
    for history in recent_history:
        for word in tokenize(history.query):
            recent_words[word] += 1
        if history.category_id:
            recent_categories[history.category_id] += 1

    scored = []
    for product in products:
        if product.id == exclude_id:
            continue

        score = product_score(product, user_vector)
        product_words = set((product.vector_data or {}).keys())

        # Recent search words have a strong influence.
        for word, count in recent_words.items():
            if word in product_words:
                score += count * 3

        # Recently searched categories also get a small boost.
        if product.category_id in recent_categories:
            score += recent_categories[product.category_id] * 4

        # Ratings help break ties between otherwise similar products.
        score += float(product.rating_average or 0) * 0.8
        scored.append((score, product))

    scored.sort(
        key=lambda item: (item[0], item[1].created_at),
        reverse=True
    )

    selected = [product for score, product in scored if score > 0][:limit]

    # If there is not enough history yet, fill the remaining places with
    # newer products so the recommendation section is still useful.
    if len(selected) < limit:
        seen = {product.id for product in selected}
        fallback = sorted(
            [product for product in products
             if product.id not in seen and product.id != exclude_id],
            key=lambda product: (
                float(product.rating_average or 0),
                product.created_at
            ),
            reverse=True
        )
        selected.extend(fallback[:limit - len(selected)])

    return selected

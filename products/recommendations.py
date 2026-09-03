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


def recommended_products(user, exclude_id=None, limit=6):
    from .models import Product
    try:
        profile = user.profile
    except Exception:
        return Product.objects.filter(is_available=True).order_by('-created_at')[:limit]

    products = list(Product.objects.filter(is_available=True).select_related('category'))
    scored = [(product_score(p, profile.vector_data or {}), p) for p in products if p.id != exclude_id]
    scored.sort(key=lambda x: (x[0], float(x[1].rating_average or 0), x[1].created_at), reverse=True)
    selected = [p for score, p in scored if score > 0][:limit]
    if len(selected) < limit:
        seen = {p.id for p in selected}
        selected.extend([p for p in products if p.id not in seen and p.id != exclude_id][:limit-len(selected)])
    return selected

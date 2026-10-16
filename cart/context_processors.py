def cart_count(request):
    if not request.user.is_authenticated:
        return {'cart_count': 0}

    from .models import Cart
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        return {'cart_count': 0}

    cart_items = cart.items.all()
    return {
        'cart_count': sum(item.quantity for item in cart_items),
        # Product IDs currently in the user's cart. Templates use this
        # simple list to decide whether a button should say
        # 'Add to Cart' or 'Go to Cart'.
        'cart_product_ids': list(cart_items.values_list('product_id', flat=True)),
    }

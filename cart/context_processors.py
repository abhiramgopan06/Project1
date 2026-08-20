def cart_count(request):
    if not request.user.is_authenticated:
        return {'cart_count': 0}

    from .models import Cart
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        return {'cart_count': 0}

    return {'cart_count': sum(item.quantity for item in cart.items.all())}

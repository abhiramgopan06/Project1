from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import Cart, CartItem
from products.models import Product


@login_required
def add_to_cart(request, id):
    product = get_object_or_404(
        Product,
        id=id,
        is_available=True
    )

    if product.stock <= 0:
        messages.error(request, 'This product is out of stock.')
        return redirect('products:product_detail', id=id)

    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            messages.error(
                request,
                'You cannot add more than the available stock.'
            )
            return redirect('products:product_detail', id=id)

    messages.success(request, f'{product.name} added to cart.')
    return redirect('cart:cart')


@login_required
def cart(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_items = cart.items.select_related('product')
    total = sum(item.product.price * item.quantity for item in cart_items)

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
        'cart_count': sum(item.quantity for item in cart_items),
    }

    return render(request, 'products/cart.html', context)


@login_required
def remove_from_cart(request, id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(
        CartItem,
        cart=cart,
        product_id=id
    )

    cart_item.delete()
    messages.success(request, 'Product removed from cart.')
    return redirect('cart:cart')


@login_required
def increase_quantity(request, id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(
        CartItem,
        cart=cart,
        product_id=id
    )

    if cart_item.quantity < cart_item.product.stock:
        cart_item.quantity += 1
        cart_item.save()
    else:
        messages.error(
            request,
            'You cannot add more than the available stock.'
        )

    return redirect('cart:cart')


@login_required
def decrease_quantity(request, id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(
        CartItem,
        cart=cart,
        product_id=id
    )

    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()

    return redirect('cart:cart')


@login_required
def update_cart(request, id):
    cart = get_object_or_404(Cart, user=request.user)
    cart_item = get_object_or_404(
        CartItem,
        cart=cart,
        id=id
    )

    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1

        if quantity < 1:
            cart_item.delete()

        elif quantity > cart_item.product.stock:
            messages.error(
                request,
                'You cannot add more than the available stock.'
            )

        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully.')

    return redirect('cart:cart')

# cart/views.py
# ----------------------------------------------------
# This file has all the simple functions ("views") for the
# shopping cart: adding a product, showing the cart page,
# removing a product, and changing how many of a product
# the user wants. Each function below does ONE small job.
# ----------------------------------------------------

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Cart, CartItem
from products.models import Product


@login_required
@require_POST
def add_to_cart(request, id):
    # Step 1: find the product the user clicked "Add to Cart" on.
    product = get_object_or_404(
        Product,
        id=id,
        is_available=True
    )

    # Step 2: work out where to send the user back to. Every
    # "Add to Cart" form includes a hidden "next" field with the
    # page it was submitted from (home page, product page, etc) -
    # we stay on that page instead of jumping to the cart, so a
    # small "Added to cart" box can pop up there with a
    # "Go to Cart" button. The user only goes to the cart when
    # they actually click that button.
    next_url = request.POST.get('next', '')
    if not next_url.startswith('/'):
        next_url = reverse('products:product_detail', args=[id])

    if product.stock <= 0:
        messages.error(request, 'This product is out of stock.')
        return redirect(next_url)

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
            return redirect(next_url)

    # extra_tags='cart_added' marks this message so base.html shows
    # it as a small "Go to Cart" notification box instead of a
    # plain banner.
    messages.success(request, f'{product.name} added to cart.', extra_tags='cart_added')
    return redirect(next_url)


# Shows the cart page: every item in the cart plus the total price.
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


# Deletes one product from the cart completely.
@login_required
@require_POST
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


# The "+" button: adds one more of this product to the cart.
@login_required
@require_POST
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


# The "-" button: removes one of this product. If we're already
# down to 1, remove the whole item instead of going to 0.
@login_required
@require_POST
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


# Used when the user types a new quantity into the box and
# clicks "Update" (instead of using the + / - buttons).
@login_required
@require_POST
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

# dashboard/views.py
# ----------------------------------------------------
# This is the staff-only admin dashboard: overview numbers,
# the list of orders (with a way to update their status),
# and the list of registered users. Only staff members
# (people with is_staff=True) are allowed to see these pages.
# ----------------------------------------------------

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from orders.models import Order
from products.models import Product


# The dashboard "home" page: a few summary numbers (total orders,
# revenue, products, users) plus recent orders and low-stock items.
@staff_member_required
def dashboard_home(request):
    total_orders = Order.objects.count()

    total_revenue = Order.objects.filter(
        payment_status='Paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    total_products = Product.objects.count()
    total_users = User.objects.count()

    recent_orders = Order.objects.order_by('-created_at')[:5]

    low_stock_products = Product.objects.filter(
        stock__lte=5
    ).order_by('stock')[:5]

    context = {
        'active': 'home',
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'total_users': total_users,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
    }

    return render(request, 'dashboard/home.html', context)


# Shows every order in the store, with an optional filter by
# status (e.g. only "Pending" orders).
@staff_member_required
def dashboard_orders(request):
    orders = Order.objects.select_related('user').order_by('-created_at')

    status_filter = request.GET.get('status', '')

    if status_filter:
        orders = orders.filter(status=status_filter)

    context = {
        'active': 'orders',
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'status_filter': status_filter,
    }

    return render(request, 'dashboard/orders.html', context)


# Lets a staff member change an order's status (e.g. from
# "Pending" to "Shipped") using the dropdown on the orders page.
@staff_member_required
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = dict(Order.STATUS_CHOICES)

        if new_status in valid_statuses:
            order.status = new_status
            order.save(update_fields=['status'])
            messages.success(
                request,
                f'Order #{order.id} status updated to {valid_statuses[new_status]}.'
            )
        else:
            messages.error(request, 'Invalid status selected.')

    return redirect('dashboard:orders')


# Shows every registered user and how many orders each one has made.
@staff_member_required
def dashboard_users(request):
    users = User.objects.annotate(
        order_count=Count('order')
    ).order_by('-date_joined')

    context = {
        'active': 'users',
        'users': users,
    }

    return render(request, 'dashboard/users.html', context)


# Shows everything about one single order for staff: the customer's
# account info, the delivery address they typed in at checkout, the
# items ordered, and a form to update the order status. This is the
# page the "View" button on the orders table opens.
@staff_member_required
def dashboard_order_detail(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('user'),
        id=order_id
    )

    order_items = order.items.select_related('product')

    context = {
        'active': 'orders',
        'order': order,
        'order_items': order_items,
        'status_choices': Order.STATUS_CHOICES,
    }

    return render(request, 'dashboard/order_detail.html', context)

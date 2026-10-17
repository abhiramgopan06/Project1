                    
                                                           
                                                         
                                                      
                                                             

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from orders.models import Order
from products.models import Product, Category
from products.forms import ProductForm


                                                                 
                                                                   
@staff_member_required
def dashboard_home(request):
    total_orders = Order.objects.count()

    total_revenue = Order.objects.filter(
        payment_status='Paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    total_products = Product.objects.count()
    total_users = User.objects.count()

    recent_orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:5]

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


                                                                
                                                                 
                               

                                                             
                                       
@staff_member_required
def dashboard_products(request):
    products = Product.objects.select_related('category').order_by('-created_at')

    context = {
        'active': 'products',
        'products': products,
    }

    return render(request, 'dashboard/products.html', context)


                                         
@staff_member_required
def dashboard_product_add(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)

        if form.is_valid():
            product = form.save()
            messages.success(request, f'"{product.name}" was added to the catalog.')
            return redirect('dashboard:products')
    else:
        form = ProductForm()

    context = {
        'active': 'products',
        'form': form,
        'is_new': True,
    }

    return render(request, 'dashboard/product_form.html', context)


                                                               
@staff_member_required
def dashboard_product_edit(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)

        if form.is_valid():
            form.save()
            messages.success(request, f'"{product.name}" was updated.')
            return redirect('dashboard:products')
    else:
        form = ProductForm(instance=product)

    context = {
        'active': 'products',
        'form': form,
        'is_new': False,
        'product': product,
    }

    return render(request, 'dashboard/product_form.html', context)


                                                              
                                                                  
                                                                  
                                                                  
@staff_member_required
def dashboard_product_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.is_available = not product.is_available
        product.save(update_fields=['is_available'])
        state = 'activated' if product.is_available else 'deactivated'
        messages.success(request, f'"{product.name}" was {state}.')

    return redirect('dashboard:products')


                                                                        
@staff_member_required
def dashboard_product_offers(request):
    products = Product.objects.select_related('category').order_by('name')
    categories = Category.objects.order_by('name')
    selected_id = request.POST.get('product') or request.GET.get('product')
    selected_product = Product.objects.filter(id=selected_id).first() if selected_id else None

    if request.method == 'POST' and request.POST.get('offer_type') == 'category':
        category_id = request.POST.get('category')
        category = Category.objects.filter(id=category_id).first()
        try:
            percent = int(request.POST.get('category_discount_percent', ''))
            duration = int(request.POST.get('duration_days', ''))
        except (TypeError, ValueError):
            percent, duration = -1, 0
        if not category:
            messages.error(request, 'Please select a category.')
        elif percent < 0 or percent > 90:
            messages.error(request, 'Enter a category offer from 0% to 90%.')
        elif percent == 0:
            category.offer_percent = 0
            category.offer_ends_at = None
            category.save(update_fields=['offer_percent', 'offer_ends_at'])
            messages.success(request, f'The category offer for {category.name} was cancelled.')
        elif duration < 1 or duration > 365:
            messages.error(request, 'Offer duration must be between 1 and 365 days.')
        else:
            category.offer_percent = percent
            category.offer_ends_at = timezone.now() + timedelta(days=duration)
            category.save(update_fields=['offer_percent', 'offer_ends_at'])
            messages.success(request, f'{percent}% offer set for {category.name} for {duration} day(s).')
        return redirect('dashboard:product_offers')

    if request.method == 'POST':
        if not selected_product:
            messages.error(request, 'Please select a product.')
        else:
            try:
                percent = int(request.POST.get('discount_percent', ''))
            except (TypeError, ValueError):
                percent = -1
            if percent < 0 or percent > 90:
                messages.error(request, 'Enter an offer from 0% to 90%. Use 0% to remove an offer.')
            else:
                selected_product.discount_percent = percent
                selected_product.save(update_fields=['discount_percent'])
                if percent:
                    messages.success(request, f'{percent}% offer saved for "{selected_product.name}".')
                else:
                    messages.success(request, f'Offer removed from "{selected_product.name}".')
                return redirect('dashboard:product_offers')

    return render(request, 'dashboard/product_offers.html', {
        'active': 'offers',
        'products': products,
        'categories': categories,
        'selected_product': selected_product,
    })


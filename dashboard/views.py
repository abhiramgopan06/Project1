from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum, Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from orders.models import Order
from products.models import Product, Category, ProductOfferHistory, CategoryOfferHistory
from products.forms import ProductForm
from storeextras.models import ActivityLog, StockMovement

@staff_member_required
def dashboard_home(request):
    if not request.user.is_superuser:
        return redirect('dashboard:staff_home')
    total_orders = Order.objects.count()

    total_revenue = Order.objects.filter(
        payment_status='Paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    total_products = Product.objects.filter(is_available=True).count()
    total_users = User.objects.count()

    recent_orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:5]

    low_stock_products = Product.objects.filter(
        is_available=True, stock__lte=5
    ).select_related('category').order_by('stock', 'name')[:5]

    context = {
        'active': 'home',
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_products': total_products,
        'total_users': total_users,
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'total_categories': Category.objects.count(),
        'total_staff': User.objects.filter(is_staff=True, is_superuser=False).count(),
        'recent_activity': ActivityLog.objects.select_related('actor').filter(actor__is_staff=True, actor__is_superuser=False).order_by('-created_at')[:6],
    }

    return render(request, 'dashboard/home.html', context)


@staff_member_required
def staff_dashboard_home(request):
    if request.user.is_superuser:
        return redirect('dashboard:home')

    from products.models import ProductOfferHistory, CategoryOfferHistory

    recent_activity = ActivityLog.objects.filter(actor=request.user).order_by('-created_at')[:8]
    low_stock_products = Product.objects.filter(is_available=True, stock__lte=5).select_related('category').order_by('stock', 'name')[:6]
    context = {
        'active': 'staff_home',
        'total_products': Product.objects.filter(is_available=True).count(),
        'total_categories': Category.objects.count(),
        'total_orders': Order.objects.count(),
        'low_stock_products': low_stock_products,
        'recent_activity': recent_activity,
        'active_product_offers': Product.objects.filter(discount_percent__gt=0, discount_ends_at__gt=timezone.now()).count(),
        'active_category_offers': Category.objects.filter(offer_percent__gt=0, offer_ends_at__gt=timezone.now()).count(),
    }
    return render(request, 'dashboard/staff_home.html', context)

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
@require_POST
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        valid_statuses = dict(Order.STATUS_CHOICES)

        if new_status in valid_statuses:
            previous_status = order.status
            order.status = new_status
            order.save(update_fields=['status'])
            ActivityLog.objects.create(actor=request.user, action='Order status changed', object_type='Order', object_id=order.pk, details=f'Order #{order.pk} status changed from {previous_status} to {new_status}.')
            messages.success(
                request,
                f'Order #{order.id} status updated to {valid_statuses[new_status]}.'
            )
        else:
            messages.error(request, 'Invalid status selected.')

    return redirect('dashboard:orders')

@user_passes_test(lambda user: user.is_superuser)
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
            ActivityLog.objects.create(actor=request.user, action='Product created', object_type='Product', object_id=product.pk, details=f'Added product {product.name}; category: {product.category.name}; price: {product.price}; starting stock: {product.stock}.')
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
            old = Product.objects.get(pk=product.pk)
            old_stock = old.stock
            product = form.save()
            ActivityLog.objects.create(actor=request.user, action='Product updated', object_type='Product', object_id=product.pk, details=f'Updated {product.name}; category: {product.category.name}; price: {product.price}; stock: {old_stock} -> {product.stock}; available: {product.is_available}.')
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
@require_POST
def dashboard_product_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        product.is_available = not product.is_available
        product.save(update_fields=['is_available'])
        ActivityLog.objects.create(actor=request.user, action='Product availability changed', object_type='Product', object_id=product.pk, details=f'{product.name} availability set to {product.is_available}.')
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
            now = timezone.now()
            CategoryOfferHistory.objects.filter(
                category=category, ends_at__gt=now
            ).update(ends_at=now)
            ActivityLog.objects.create(actor=request.user, action='Category offer cancelled', object_type='Category', object_id=category.pk, details=f'Cancelled category offer for {category.name}.')
            category.offer_percent = 0
            category.offer_ends_at = None
            category.save(update_fields=['offer_percent', 'offer_ends_at'])
            messages.success(request, f'The category offer for {category.name} was cancelled.')
        elif duration < 1 or duration > 365:
            messages.error(request, 'Offer duration must be between 1 and 365 days.')
        else:
            now = timezone.now()
            CategoryOfferHistory.objects.filter(
                category=category, ends_at__gt=now
            ).update(ends_at=now)
            category.offer_percent = percent
            category.offer_ends_at = now + timedelta(days=duration)
            category.save(update_fields=['offer_percent', 'offer_ends_at'])
            CategoryOfferHistory.objects.create(
                category=category,
                category_name=category.name,
                discount_percent=percent,
                started_at=now,
                ends_at=category.offer_ends_at,
            )
            ActivityLog.objects.create(actor=request.user, action='Category offer created', object_type='Category', object_id=category.pk, details=f'{percent}% offer on {category.name} for {duration} day(s), ending {category.offer_ends_at}.')
            messages.success(request, f'{percent}% offer set for {category.name} for {duration} day(s).')
        return redirect('dashboard:category_offers')

    if request.method == 'POST':
        if not selected_product:
            messages.error(request, 'Please select a product.')
        else:
            try:
                percent = int(request.POST.get('discount_percent', ''))
                duration = int(request.POST.get('duration_days', ''))
            except (TypeError, ValueError):
                percent, duration = -1, 0
            if percent < 0 or percent > 90:
                messages.error(request, 'Enter an offer from 0% to 90%. Use 0% to remove an offer.')
            elif percent and (duration < 1 or duration > 365):
                messages.error(request, 'Offer duration must be between 1 and 365 days.')
            else:
                now = timezone.now()
                ProductOfferHistory.objects.filter(
                    product=selected_product, ends_at__gt=now
                ).update(ends_at=now)
                selected_product.discount_percent = percent
                selected_product.discount_ends_at = now + timedelta(days=duration) if percent else None
                selected_product.save(update_fields=['discount_percent', 'discount_ends_at'])
                if percent:
                    ProductOfferHistory.objects.create(
                        product=selected_product,
                        discount_percent=percent,
                        started_at=now,
                        ends_at=selected_product.discount_ends_at,
                    )
                    ActivityLog.objects.create(actor=request.user, action='Product offer created', object_type='Product', object_id=selected_product.pk, details=f'{percent}% offer on {selected_product.name} for {duration} day(s), ending {selected_product.discount_ends_at}.')
                    messages.success(request, f'{percent}% offer saved for "{selected_product.name}" for {duration} day(s).')
                else:
                    ActivityLog.objects.create(actor=request.user, action='Product offer cancelled', object_type='Product', object_id=selected_product.pk, details=f'Removed offer from {selected_product.name}.')
                    messages.success(request, f'Offer removed from "{selected_product.name}".')
                return redirect('dashboard:product_offers')

    now = timezone.now()
    present_offers = [p for p in products if p.discount_percent and p.discount_ends_at and p.discount_ends_at > now]
    old_offers = ProductOfferHistory.objects.select_related('product', 'product__category').filter(ends_at__lte=now).order_by('-ends_at')
    for product in products:
        product.offer_history_rows = product.offer_history.all()
    return render(request, 'dashboard/product_offers.html', {
        'active': 'offers',
        'products': products,
        'categories': categories,
        'selected_product': selected_product,
        'present_offers': present_offers,
        'old_offers': old_offers,
    })

@staff_member_required
def dashboard_category_offers(request):
    now = timezone.now()
    categories = Category.objects.order_by('name')
    present_offers = CategoryOfferHistory.objects.select_related('category').filter(
        ends_at__gt=now
    ).order_by('ends_at')
    tracked_category_ids = CategoryOfferHistory.objects.values_list('category_id', flat=True)
    legacy_present_categories = categories.filter(
        offer_percent__gt=0, offer_ends_at__gt=now
    ).exclude(id__in=tracked_category_ids)
    expired_offers = CategoryOfferHistory.objects.select_related('category').filter(
        ends_at__lte=now
    ).order_by('-ends_at')
    return render(request, 'dashboard/category_offers.html', {
        'active': 'category_offers',
        'categories': categories,
        'present_offers': present_offers,
        'legacy_present_categories': legacy_present_categories,
        'expired_offers': expired_offers,
        'now': now,
    })

@staff_member_required
def dashboard_previous_offers(request):
    now = timezone.now()
    expired = ProductOfferHistory.objects.select_related(
        'product', 'product__category'
    ).filter(ends_at__lte=now).order_by('-ends_at')
    page_obj = Paginator(expired, 10).get_page(request.GET.get('page'))
    return render(request, 'dashboard/previous_offers.html', {
        'active': 'offers',
        'page_obj': page_obj,
        'now': now,
    })

@staff_member_required
def dashboard_offer_detail(request, product_id):
    product = get_object_or_404(Product.objects.select_related('category'), id=product_id)
    offer_history = ProductOfferHistory.objects.filter(product=product).order_by('recorded_at')
    return render(request, 'dashboard/product_offer_detail.html', {
        'active': 'offers',
        'product': product,
        'offer_history': offer_history,
        'now': timezone.now(),
    })

@staff_member_required
def dashboard_offer_history(request):
    product_history = ProductOfferHistory.objects.select_related(
        'product', 'product__category'
    ).order_by('-recorded_at')
    category_history = CategoryOfferHistory.objects.select_related(
        'category'
    ).order_by('-recorded_at')
    product_page = Paginator(product_history, 10).get_page(request.GET.get('product_page'))
    category_page = Paginator(category_history, 10).get_page(request.GET.get('category_page'))
    return render(request, 'dashboard/product_offer_history.html', {
        'active': 'offers',
        'product_page': product_page,
        'category_page': category_page,
        'now': timezone.now(),
    })


@user_passes_test(lambda user: user.is_superuser)
@require_POST
def toggle_staff_role(request, user_id):
    target = get_object_or_404(User, pk=user_id)
    if target.is_superuser:
        messages.error(request, 'Superuser access cannot be changed here.')
    elif target.pk == request.user.pk:
        messages.error(request, 'You cannot change your own staff role.')
    else:
        target.is_staff = not target.is_staff
        target.save(update_fields=['is_staff'])
        role = 'staff' if target.is_staff else 'customer'
        ActivityLog.objects.create(actor=request.user, action='User role changed', object_type='User', object_id=target.pk, details=f'{target.username} was changed to {role}.')
        messages.success(request, f'{target.username} is now a {role}.')
    return redirect('dashboard:users')

@staff_member_required
@require_POST
def dashboard_product_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    name = product.name
    product.is_available = False
    product.save(update_fields=['is_available'])
    ActivityLog.objects.create(actor=request.user, action='Product archived', object_type='Product', object_id=product.pk, details=f'Archived {name}; order and offer history was preserved.')
    messages.success(request, f'{name} was archived. Existing order and offer history has been preserved.')
    return redirect('dashboard:products')

@staff_member_required
def dashboard_categories(request):
    categories = Category.objects.annotate(product_count=Count('products')).order_by('name')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, 'Enter a category name.')
            elif Category.objects.filter(name__iexact=name).exists():
                messages.error(request, 'That category already exists.')
            else:
                category = Category.objects.create(name=name)
                ActivityLog.objects.create(actor=request.user, action='Category created', object_type='Category', object_id=category.pk, details=f'Created category {category.name}.')
                messages.success(request, f'Category {name} was created.')
            return redirect('dashboard:categories')
        if action == 'delete':
            category = get_object_or_404(Category, pk=request.POST.get('category_id'))
            if category.products.exists():
                messages.error(request, 'This category has products. Move or delete those products before deleting the category.')
            else:
                name = category.name
                ActivityLog.objects.create(actor=request.user, action='Category deleted', object_type='Category', object_id=category.pk, details=f'Deleted category {name}.')
                category.delete()
                messages.success(request, f'Category {name} was deleted.')
            return redirect('dashboard:categories')
    return render(request, 'dashboard/categories.html', {'active': 'categories', 'categories': categories})


@user_passes_test(lambda user: user.is_superuser)
def dashboard_staff_activity(request):
    staff_members = User.objects.filter(is_staff=True, is_superuser=False).order_by('username')
    staff_actions = [
        'Product created', 'Product updated', 'Product availability changed',
        'Product archived', 'Category created', 'Category deleted',
        'Product offer created', 'Product offer cancelled',
        'Category offer created', 'Category offer cancelled',
        'Order status changed', 'Return workflow updated',
    ]
    records = ActivityLog.objects.select_related('actor').filter(
        Q(actor__is_staff=True, actor__is_superuser=False) | Q(action__in=staff_actions)
    ).exclude(actor__is_superuser=True).order_by('-created_at')
    movements = StockMovement.objects.select_related('changed_by', 'product').filter(
        changed_by__isnull=False, changed_by__is_superuser=False
    ).order_by('-created_at')
    staff_id = request.GET.get('staff', '').strip()
    search = request.GET.get('q', '').strip()
    if staff_id.isdigit():
        records = records.filter(actor_id=int(staff_id))
        movements = movements.filter(changed_by_id=int(staff_id))
    if search:
        records = records.filter(
            Q(action__icontains=search) | Q(object_type__icontains=search) |
            Q(details__icontains=search) | Q(actor__username__icontains=search)
        )
        movements = movements.filter(
            Q(product_name__icontains=search) | Q(reason__icontains=search) |
            Q(changed_by__username__icontains=search)
        )
    activity_page = Paginator(records, 25).get_page(request.GET.get('page'))
    stock_page = Paginator(movements, 25).get_page(request.GET.get('stock_page'))
    context = {
        'active': 'staff_activity',
        'staff_members': staff_members,
        'selected_staff': staff_id,
        'search_query': search,
        'activity_page': activity_page,
        'stock_page': stock_page,
        'total_staff': User.objects.filter(is_staff=True, is_superuser=False).count(),
        'total_actions': ActivityLog.objects.filter(
            Q(actor__is_staff=True, actor__is_superuser=False) | Q(action__in=staff_actions)
        ).exclude(actor__is_superuser=True).count(),
        'today_actions': ActivityLog.objects.filter(
            Q(actor__is_staff=True, actor__is_superuser=False) | Q(action__in=staff_actions),
            created_at__date=timezone.localdate()
        ).exclude(actor__is_superuser=True).count(),
        'today_stock_updates': StockMovement.objects.filter(
            changed_by__isnull=False, changed_by__is_superuser=False, created_at__date=timezone.localdate()
        ).count(),
    }
    return render(request, 'dashboard/staff_activity.html', context)

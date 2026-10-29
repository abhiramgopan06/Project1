import csv
from decimal import Decimal
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from orders.models import Coupon, Order, OrderItem
from products.models import Product, ProductHistory

@login_required
def recently_viewed(request):
    history = ProductHistory.objects.filter(user=request.user).select_related('product', 'product__category').order_by('-last_viewed', '-last_interacted')[:30]
    return render(request, 'storeextras/recently_viewed.html', {'history': history})

@login_required
@require_POST
def apply_coupon(request):
    code = request.POST.get('coupon_code', '').strip().upper()
    coupon = Coupon.objects.filter(code=code, is_active=True).first()
    if not coupon:
        messages.error(request, 'That coupon code is not valid.')
        return redirect('checkout')
    now = timezone.now()
    if coupon.starts_at and coupon.starts_at > now or coupon.expires_at and coupon.expires_at < now:
        messages.error(request, 'This coupon is not currently active.')
        return redirect('checkout')
    if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
        messages.error(request, 'This coupon has reached its usage limit.')
        return redirect('checkout')
    from cart.models import Cart
    cart = Cart.objects.filter(user=request.user).first()
    subtotal = sum((item.total_price for item in cart.items.select_related('product', 'variant')), Decimal('0.00')) if cart else Decimal('0.00')
    if subtotal < coupon.minimum_order_amount:
        messages.error(request, f'The minimum order for this coupon is ₹{coupon.minimum_order_amount}.')
        return redirect('checkout')
    request.session['applied_coupon'] = coupon.code
    messages.success(request, f'Coupon {coupon.code} applied. Discount will be checked again at checkout.')
    return redirect('checkout')

@login_required
@require_POST
def remove_coupon(request):
    request.session.pop('applied_coupon', None)
    messages.success(request, 'Coupon removed.')
    return redirect('checkout')

@login_required
@require_POST
def cancel_order_request(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if order.status not in [Order.STATUS_PENDING, Order.STATUS_CONFIRMED]:
        messages.error(request, 'This order can no longer be cancelled online. Please contact support.')
        return redirect('order_detail', order_id=order.id)
    reason = request.POST.get('reason', '').strip()[:255]
    order.cancellation_reason = reason or 'Customer requested cancellation'
    order.status = Order.STATUS_CANCELLED
    order.save(update_fields=['status', 'cancellation_reason'])
    for item in order.items.select_related('product'):
        if not item.is_cancelled:
            item.product.stock += item.quantity
            item.product.save(update_fields=['stock'])
            item.is_cancelled = True
            item.save(update_fields=['is_cancelled'])
    messages.success(request, 'Cancellation request processed. Any prepaid refund must be handled through the payment provider.')
    return redirect('order_detail', order_id=order.id)

@staff_member_required
def analytics(request):
    paid_orders = Order.objects.filter(payment_status='Paid').exclude(status=Order.STATUS_CANCELLED)
    context = {'orders_count': Order.objects.count(), 'paid_revenue': paid_orders.aggregate(total=Sum('total_amount'))['total'] or 0, 'customers_count': Order.objects.values('user_id').distinct().count(), 'low_stock': Product.objects.filter(is_available=True, stock__lte=5).order_by('stock')[:12], 'top_products': OrderItem.objects.values('product__name').annotate(units=Sum('quantity'), revenue=Sum('price')).order_by('-units')[:10]}
    return render(request, 'dashboard/analytics.html', context)

@staff_member_required
def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders-report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Email', 'Status', 'Payment status', 'Total', 'Created'])
    for order in Order.objects.select_related('user').order_by('-created_at'):
        writer.writerow([order.pk, order.name, order.email, order.status, order.payment_status, order.total_amount, order.created_at.isoformat()])
    return response

@staff_member_required
def export_stock_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="stock-report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Product ID', 'Product', 'Category', 'Stock', 'Price', 'Available'])
    for product in Product.objects.select_related('category').order_by('name'):
        writer.writerow([product.pk, product.name, product.category.name, product.stock, product.price, product.is_available])
    return response

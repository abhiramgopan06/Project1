from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from cart.models import Cart
from products.models import Product
from orders.models import Order, ReturnReplaceRequest
from .models import WishlistItem, Notification, PaymentRecord, StockMovement, ActivityLog

@login_required
def wishlist(request):
    items = WishlistItem.objects.filter(user=request.user).select_related('product', 'product__category')
    return render(request, 'storeextras/wishlist.html', {'items': items})

@login_required
@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_available=True)
    item, created = WishlistItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        item.delete()
        messages.success(request, 'Product removed from your wishlist.')
    else:
        messages.success(request, 'Product saved to your wishlist.')
    next_url = request.POST.get('next', '')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect('storeextras:wishlist')

@login_required
def notifications(request):
    items = Notification.objects.filter(user=request.user)
    return render(request, 'storeextras/notifications.html', {'items': items})

@login_required
@require_POST
def notification_read(request, notification_id):
    item = get_object_or_404(Notification, pk=notification_id, user=request.user)
    item.is_read = True
    item.save(update_fields=['is_read'])
    return redirect('storeextras:notifications')

@login_required
def payment_history(request):
    records = PaymentRecord.objects.filter(user=request.user).select_related('order')
    return render(request, 'storeextras/payment_history.html', {'records': records})

@login_required
def return_history(request):
    requests = ReturnReplaceRequest.objects.filter(order_item__order__user=request.user).select_related('order_item__product', 'order_item__order')
    return render(request, 'storeextras/return_history.html', {'requests': requests})

@login_required
def invoice(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related('items__product'), pk=order_id, user=request.user)
    return render(request, 'storeextras/invoice.html', {'order': order})

@user_passes_test(lambda user: user.is_superuser)
def activity_history(request):
    records = ActivityLog.objects.select_related('actor')[:250]
    return render(request, 'storeextras/activity_history.html', {'records': records, 'active': 'activity_history'})

@user_passes_test(lambda user: user.is_superuser)
def stock_history(request):
    records = StockMovement.objects.select_related('changed_by', 'product')[:250]
    return render(request, 'storeextras/stock_history.html', {'records': records, 'active': 'stock_history'})

@user_passes_test(lambda user: user.is_staff)
def return_management(request):
    requests = ReturnReplaceRequest.objects.select_related('order_item__product', 'order_item__order', 'order_item__order__user', 'inspected_by').order_by('-created_at')
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        item = get_object_or_404(ReturnReplaceRequest, pk=request_id)
        note = request.POST.get('inspection_note', '').strip()

        if action == 'approve' and item.status == ReturnReplaceRequest.STATUS_REQUESTED:
            item.status = ReturnReplaceRequest.STATUS_APPROVED
            item.save(update_fields=['status', 'updated_at'])
            messages.success(request, 'Return request approved. Ask the customer to send the product back.')
        elif action == 'reject' and item.status == ReturnReplaceRequest.STATUS_REQUESTED:
            item.status = ReturnReplaceRequest.STATUS_REJECTED
            item.product_condition = ReturnReplaceRequest.CONDITION_PENDING
            item.refund_status = ReturnReplaceRequest.REFUND_NOT_ELIGIBLE
            item.inspection_note = note or 'Request rejected by staff before return shipment.'
            item.inspected_by = request.user
            item.save(update_fields=['status', 'product_condition', 'refund_status', 'inspection_note', 'inspected_by', 'updated_at'])
            messages.success(request, 'Request rejected. No refund was recorded.')
        elif action == 'received' and item.status == ReturnReplaceRequest.STATUS_APPROVED:
            condition = request.POST.get('product_condition')
            if condition == ReturnReplaceRequest.CONDITION_DAMAGED:
                item.product_condition = condition
                item.status = ReturnReplaceRequest.STATUS_REJECTED
                item.refund_status = ReturnReplaceRequest.REFUND_NOT_ELIGIBLE
                item.inspection_note = note or 'Returned product was damaged during inspection.'
                item.inspected_by = request.user
                item.received_at = timezone.now()
                item.save(update_fields=['product_condition', 'status', 'refund_status', 'inspection_note', 'inspected_by', 'received_at', 'updated_at'])
                messages.warning(request, 'The product was marked damaged. The return was rejected and the refund process was stopped.')
            elif condition == ReturnReplaceRequest.CONDITION_GOOD:
                item.product_condition = condition
                item.inspection_note = note
                item.inspected_by = request.user
                item.received_at = timezone.now()
                if item.request_type == ReturnReplaceRequest.REQUEST_RETURN:
                    item.status = ReturnReplaceRequest.STATUS_RECEIVED
                    item.refund_status = ReturnReplaceRequest.REFUND_PENDING
                    item.refund_amount = item.order_item.line_total
                    item.save(update_fields=['product_condition', 'status', 'refund_status', 'refund_amount', 'inspection_note', 'inspected_by', 'received_at', 'updated_at'])
                    messages.success(request, 'Product received in good condition. Refund is awaiting staff confirmation.')
                else:
                    item.status = ReturnReplaceRequest.STATUS_COMPLETED
                    item.refund_status = ReturnReplaceRequest.REFUND_NOT_ELIGIBLE
                    item.save(update_fields=['product_condition', 'status', 'refund_status', 'inspection_note', 'inspected_by', 'received_at', 'updated_at'])
                    messages.success(request, 'Returned product received in good condition. Replacement request marked completed. Staff should arrange the replacement shipment.')
            else:
                messages.error(request, 'Select whether the received product is in good or damaged condition.')
        elif action == 'refund' and item.status == ReturnReplaceRequest.STATUS_RECEIVED and item.product_condition == ReturnReplaceRequest.CONDITION_GOOD:
            item.refund_status = ReturnReplaceRequest.REFUND_PROCESSED
            item.status = ReturnReplaceRequest.STATUS_REFUNDED
            item.save(update_fields=['refund_status', 'status', 'updated_at'])
            Notification.objects.create(user=item.order_item.order.user, title='Refund status updated', message=f'Refund for {item.order_item.product.name} was marked processed by staff. If this was an online payment, confirm the transfer in the payment provider dashboard.', link='/account/returns/')
            messages.success(request, 'Refund marked processed. For real online payments, complete the refund with your payment provider too.')
        else:
            messages.error(request, 'That action is not available for this request at its current stage.')

        ActivityLog.objects.create(actor=request.user, action='Return workflow updated', object_type='ReturnReplaceRequest', object_id=item.pk, details=f'{item.request_type} request: {item.status}; condition: {item.product_condition}; refund: {item.refund_status}.')
        Notification.objects.create(user=item.order_item.order.user, title='Return or refund update', message=f'Your {item.request_type.lower()} request for {item.order_item.product.name} is now {item.status}. Refund status: {item.refund_status}.', link='/account/returns/')
        return redirect('storeextras:return_management')
    return render(request, 'storeextras/return_management.html', {'requests': requests, 'active': 'returns'})


@login_required
def customer_dashboard(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product').order_by('-created_at')[:8]
    context = {
        'orders': orders,
        'orders_count': Order.objects.filter(user=request.user).count(),
        'wishlist_count': WishlistItem.objects.filter(user=request.user).count(),
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        'returns_count': ReturnReplaceRequest.objects.filter(order_item__order__user=request.user).count(),
    }
    return render(request, 'storeextras/customer_dashboard.html', context)

import logging

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from cart.cart import Cart
from products.models import Product
from .models import Order, OrderProduct
from .tasks import send_order_success_email

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(['POST'])
@transaction.atomic
def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('cart_detail')
    product_ids = [int(pid) for pid in cart.cart.keys()]
    existing_ids = set(Product.objects.filter(pk__in=product_ids).values_list('pk', flat=True))
    missing = [pid for pid in product_ids if pid not in existing_ids]
    if missing:
        messages.error(request, '購物車中的商品已下架，請先移除後再結帳')
        return redirect('cart_detail')
    order = Order.objects.create(customer=request.user)
    for item in cart:
        product = item['product']
        quantity = item['quantity']
        updated = Product.objects.filter(pk=product.pk, stock__gte=quantity).update(
            stock=F('stock') - quantity
        )
        if updated == 0:
            raise PermissionDenied('庫存不夠')
        OrderProduct.objects.create(
            order=order,
            from_user=request.user,
            to_user=product.author,
            product=product,
            quantity=quantity,
            expense=item['total_price'],
        )
    try:
        send_order_success_email.delay(request.user.id, order.id)
    except Exception:
        logger.exception('Failed to dispatch order confirmation email')
    cart.clear()
    return render(request, 'orders/success.html')


@login_required
def order_list(request):
    user = request.user
    orders = user.orders.all().values()
    for i in range(len(orders)):
        orders[i]['is_new_row'] = True if i%4 == 0 else False
        orders[i]['is_end_row'] = True if i%4 == 3 else False
        if i == (len(orders) -1):
            orders[i]['is_end_row'] = True
    return render(request,'orders/list.html', {'orders':orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id, customer=request.user)
    products = order.products.select_related('product')
    return render(request, 'orders/detail.html', {"products": products})

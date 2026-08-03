from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from products.models import Product
from shop.settings import CART_SESSION_ID


def stock_should_enough(view_function):
    def wrapper(request, *args, **kwargs):
        if request.method == 'POST':
            try:
                product_id = int(request.POST['product_id'])
                quantity = int(request.POST['quantity'])
            except (KeyError, TypeError, ValueError):
                messages.error(request, '加入購物車失敗：數量不正確')
                return redirect('product_list')
            product = get_object_or_404(Product, pk=product_id)
            in_cart = request.session.get(CART_SESSION_ID, {}).get(str(product_id), {}).get('quantity', 0)
            if quantity < 1 or quantity + in_cart > product.stock:
                messages.error(request, f'庫存不足，目前最多可加入 {product.stock - in_cart} 件')
                return redirect(product.get_absolute_url())
        return view_function(request, *args, **kwargs)
    return wrapper

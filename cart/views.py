from django.shortcuts import render, redirect
from .cart import Cart
from products.models import Product
from .decorators import stock_should_enough
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse

@require_http_methods(['POST'])
@stock_should_enough
def cart_update(request):
    product_id = int(request.POST['product_id'])
    quantity = int(request.POST['quantity'])
    cart = Cart(request)
    product = Product.objects.get(pk=product_id)
    update_quantity = True if cart.is_product_exist(product_id) else False
    cart.add(product, quantity, update_quantity)
    return redirect(product.get_absolute_url())

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart' : cart})

@require_http_methods(['POST'])
def cart_delete(request):
    product_id = request.POST.get('product_id')
    if product_id is None:
        return JsonResponse({"is_processed": False})
    cart = Cart(request)
    product = Product.objects.filter(pk=product_id).first()
    if product is not None:
        cart.remove(product)
    return JsonResponse({"is_processed": True, "product_id": product_id})
from .models import Product
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
def member_is_owner_of_product(view_function):
    def wrapper(request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        if product_id is None:
            raise PermissionDenied("你沒有權限刪除該商品")
        product = get_object_or_404(Product, pk = product_id)
        owner_id = product.author.id
        member_id = request.user.id
        if owner_id == member_id:
            return view_function(request, *args, **kwargs)
        else:
            raise PermissionDenied("你沒有權限刪除該商品")
    return wrapper
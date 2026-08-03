from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from django.urls import reverse
from .models import Product
from .forms import ProductForm
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .decorators import member_is_owner_of_product
from functools import reduce
import operator
import re

def _pagination_context(request, queryset, per_page=3):
    paginator = Paginator(queryset, per_page)

    current_page = paginator.get_page(request.GET.get('page'))
    page_array = list(range(1,paginator.num_pages + 1))

    try:
        previous_page_number = current_page.previous_page_number()
    except:
        previous_page_number = current_page.number
    try:
        next_page_number = current_page.next_page_number()
    except:
        next_page_number = current_page.number

    return {
        'current_page' : current_page,
        'page_array': page_array,
        'previous_page_number': previous_page_number,
        'next_page_number': next_page_number
    }

def product_list(request):

    products = Product.objects.all()

    return render(request, 'products/list.html', _pagination_context(request, products))


def product_detail(request, slug):
    product = get_object_or_404(Product, slug = slug)
    return render(request, 'products/detail.html', {'product' : product})

@login_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.author = request.user
            product.save()
            return HttpResponseRedirect(product.get_absolute_url())
    else:
        form = ProductForm()
    return render(request, 'products/create.html', {'form' : form})

@require_http_methods(['POST'])
@login_required
@member_is_owner_of_product
def product_delete(request):
    product_id = int(request.POST['product_id'])
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    return redirect(reverse('product_delete_success'))


@login_required
def product_delete_success(request):
    return render(request, 'products/product_delete_success.html')

@require_http_methods(['GET'])
def product_search(request):
    data = request.GET.get('query', '')
    if data:
        request.session['query'] = data
    else:
        data = request.session.get('query', '')
    query_list = [q for q in re.split("[,\- @!~#$%^&*()><?/|]", data) if q]
    if query_list:
        query_result = Product.objects.filter(
            reduce(operator.or_, (Q(name__icontains=q) for q in query_list))
        )
    else:
        query_result = Product.objects.none()

    return render(request, 'products/list.html', _pagination_context(request, query_result))

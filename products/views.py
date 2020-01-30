from django.shortcuts import render, get_object_or_404, redirect, HttpResponseRedirect
from django.urls import reverse
from .models import Product
from .forms import ProductForm
from django.views.decorators.http import require_http_methods

def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products' : products})

def product_detail(request, slug):
    product = Product.objects.get(slug = slug)
    return render(request, 'products/detail.html', {'product' : product})

def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            return HttpResponseRedirect(product.get_absolute_url())
    else:
        form = ProductForm(initial={'author':request.user})
    return render(request, 'products/create.html', {'form' : form})

@require_http_methods(['POST'])
def product_delete(request):
    product_id = int(request.POST['product_id'])
    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    return redirect(reverse('product_delete_success'))


def product_delete_success(request):
    return render(request, 'products/product_delete_success.html')
    
    #if request.method == 'POST':
        #getting product id from form
        #id = form....
        #query Product with given id 
        # delete object from database
        #if operation sucess, redirect user to home

def product_update(request):
    pass
    #if request method is get
    #getting product id from form
    #query Product instance with given id
    #create product form
    #bind Product instance with form
    #return form
    #else if method is post

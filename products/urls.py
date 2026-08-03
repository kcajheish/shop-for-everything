from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/product/list', permanent=False)),
    path('detail/<str:slug>', views.product_detail, name = 'product_detail'),
    path('list', views.product_list, name = "product_list"),
    path('create', views.product_create, name='product_create'),
    path('delete', views.product_delete, name='product_delete'),
    path('delete_success', views.product_delete_success, name='product_delete_success'),
    path('search', views.product_search, name='product_search'),
]

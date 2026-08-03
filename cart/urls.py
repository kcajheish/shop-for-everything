from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/cart/detail', permanent=False)),
    path('update', views.cart_update, name="update_cart"),
    path('detail', views.cart_detail, name="cart_detail"),
    path('delete', views.cart_delete, name="cart_delete"),
]
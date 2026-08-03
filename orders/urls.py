from django.urls import path
from django.views.generic.base import RedirectView
from . import views

urlpatterns = [
    path('', RedirectView.as_view(url='/order/list', permanent=False)),
    path('checkout', views.checkout, name="checkout"),
    path('list', views.order_list, name="order_list"),
    path('detail/<int:order_id>', views.order_detail, name="order_detail"),
]
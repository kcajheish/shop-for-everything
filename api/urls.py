from django.urls import path
from django.views.generic.base import RedirectView
from . import views
from rest_framework.urlpatterns import format_suffix_patterns
urlpatterns = [
    path('', RedirectView.as_view(url='/api/products', permanent=False)),
    path('products', views.ProductList.as_view()),
    path('products/<int:pk>', views.ProductDetail.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)   
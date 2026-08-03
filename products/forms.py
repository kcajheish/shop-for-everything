from .models import Product
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

class ProductForm(ModelForm):

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image']
        labels = {
            'name': _('商品名稱'),
            'description': _('商品描述'),
            'price': _('價位'),
            'stock': _('庫存'),
            'image': _('商品圖片'),
        }
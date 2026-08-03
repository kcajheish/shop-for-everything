from .models import Product
from django.forms import ModelForm

class ProductForm(ModelForm):

    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'image']
        labels = {
            'name': '商品名稱',
            'description': '商品描述',
            'price': '價位',
            'stock': '庫存',
            'image': '商品圖片',
        }
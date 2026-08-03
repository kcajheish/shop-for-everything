from django.db import models
from django.contrib.auth.models import User
from products.models import Product
from django.core.validators import MinValueValidator
from datetime import datetime
from django.urls import reverse

# Create your models here.
class Order(models.Model):
    pub_date = models.DateTimeField(auto_now=True)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')

    def get_total_expense(self):
        products = self.products.all()
        total_expense = sum(product.expense for product in products) if products else 0
        return total_expense
    
    def get_absolute_url(self):
        return reverse('order_detail', args=[self.id,])
    
    def get_pub_date(self):
        return self.pub_date.strftime("%Y/%m/%d %I:%M:%S %p")


class OrderProduct(models.Model):
    #on_delete=models.CASCADE
    ##定單將被刪除，如果使用者被刪除
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='products')
    from_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='sold_product')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE,related_name='bought_product')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sold_items')
    quantity = models.IntegerField(validators=[MinValueValidator(0)])
    expense = models.IntegerField(validators=[MinValueValidator(0)])

    def save(self, *args, **kwargs):        
        super().save(*args, **kwargs)

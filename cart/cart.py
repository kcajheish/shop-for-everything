from django.conf.settings import CART_SESSION_ID
from products.models import Product
class Cart(models.Model):

    def __init__(self, request):
        self.session = request.session
        cart = request.session.get(CART_SESSION_ID)
        if not cart:
            request.session[CART_SESSION_ID]={}
        self.cart=cart
    
    def add(self, product, quantity, update_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[prodct_id]={'quantity':0, 'price':product.price}

        if update_quantity == True:
            self.cart[product_id] += quantity
        else:
            self.cart[product] = quantity
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart.keys():
            del self.cart[product_id]
        self.save()
    
    def get_total_price(self):
        return sum(item['quantity']*item['price'] for item in self.cart.values())
    
    def __iter__(self):
        '''
        產生iterable 內含product instance, total price
        '''
        for product_id in self.cart.keys():
            product = Product.objects.get(pk=int(product_id))
            self.cart[product_id]['product']=product

        for item in self.cart.values():
            item['total_price']=item['quantity']*int(item['price'])
            yield item
    
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    def clear(self):
        del self.session[CART_SESSION_ID]
        self.session.modified = True

    def save():
        self.session[CART_SESSION_ID] = self.cart
        self.session.modified = True
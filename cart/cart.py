from shop.settings import CART_SESSION_ID
from products.models import Product
class Cart(object):

    def __init__(self, request):
        self.session = request.session
        cart = request.session.get(CART_SESSION_ID)
        if not cart:
            request.session[CART_SESSION_ID]={}
        self.cart=request.session[CART_SESSION_ID]
    
    def add(self, product, quantity, update_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id]={'quantity':0, 'price':product.price}
        
        item = self.cart[product_id]
        if update_quantity == True:
            item['quantity'] = quantity
        else:
            item['quantity'] += quantity
        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart.keys():
            del self.cart[product_id]
        self.save()
    
    def get_total_price(self):
        return sum(item['quantity']*item['price'] for item in self.cart.values())
    
    def is_product_exist(self, product_id):
        if str(product_id) in self.cart.keys():
            return True
        return False

    def __iter__(self):
        '''
        產生iterable 內含product instance, total price
        '''
        product_ids = [int(pid) for pid in self.cart.keys()]
        products = Product.objects.filter(pk__in=product_ids)
        for product in products:
            self.cart[str(product.id)]['product']=product

        for product_id, item in self.cart.items():
            if 'product' not in item:
                continue
            item['total_price']=item['quantity']*int(item['price'])
            yield item
    
    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())
    
    def clear(self):
        del self.session[CART_SESSION_ID]
        self.session.modified = True

    def save(self):
        self.session[CART_SESSION_ID] = self.cart
        self.session.modified = True
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from products.models import Product
from cart.cart import Cart


class CartAddTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cart_add', password='pw')
        self.product = Product.objects.create(
            name='p', price=10, stock=10, description='d', author=self.user,
        )

    def make_cart(self):
        request = RequestFactory().get('/')
        request.session = self.client.session
        return Cart(request)

    def test_add_increments_by_default(self):
        cart = self.make_cart()
        cart.add(self.product, 2)
        cart.add(self.product, 3)
        self.assertEqual(cart.cart[str(self.product.id)]['quantity'], 5)

    def test_add_with_update_quantity_replaces(self):
        cart = self.make_cart()
        cart.add(self.product, 2)
        cart.add(self.product, 7, update_quantity=True)
        self.assertEqual(cart.cart[str(self.product.id)]['quantity'], 7)

    def test_cart_update_view_replaces_existing_quantity(self):
        self.client.post('/cart/update', {'product_id': self.product.id, 'quantity': 3})
        self.client.post('/cart/update', {'product_id': self.product.id, 'quantity': 5})
        cart = self.client.session['cart']
        self.assertEqual(cart[str(self.product.id)]['quantity'], 5)


class CartDeleteTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cart_user', password='pw')
        self.product = Product.objects.create(
            name='item', price=1, stock=5, description='d', author=self.user,
        )

    def put_in_cart(self):
        session = self.client.session
        session['cart'] = {str(self.product.id): {'quantity': 1, 'price': self.product.price}}
        session.save()

    def test_delete_requires_post(self):
        response = self.client.get('/cart/delete')
        self.assertEqual(response.status_code, 405)

    def test_delete_without_product_id(self):
        response = self.client.post('/cart/delete', {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['is_processed'])

    def test_delete_removes_item(self):
        self.put_in_cart()
        response = self.client.post('/cart/delete', {'product_id': self.product.id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_processed'])
        self.assertNotIn(str(self.product.id), self.client.session['cart'])

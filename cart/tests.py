from django.test import TestCase
from django.contrib.auth.models import User
from products.models import Product


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

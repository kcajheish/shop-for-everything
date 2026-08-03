from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.test import TestCase

from products.models import Product


class ProductAPITest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='api_author', password='pw')
        self.product = Product.objects.create(
            name='original', price=50, stock=5,
            description='desc', author=self.author,
        )
        self.client = APIClient()

    def test_post_creates_product(self):
        response = self.client.post(
            '/api/products',
            {
                'name': 'new product',
                'price': 10,
                'stock': 3,
                'description': 'a brand new product',
                'author': self.author.id,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Product.objects.filter(name='new product').exists())

    def test_post_without_required_fields_returns_400(self):
        response = self.client.post('/api/products', {'name': 'incomplete'})
        self.assertEqual(response.status_code, 400)

    def test_put_updates_product(self):
        response = self.client.put(
            '/api/products/%d' % self.product.id,
            {
                'name': 'renamed',
                'price': 60,
                'stock': 7,
                'description': 'updated description',
                'author': self.author.id,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'renamed')
        self.assertEqual(self.product.price, 60)

    def test_put_returns_400_for_invalid_data(self):
        response = self.client.put(
            '/api/products/%d' % self.product.id,
            {'name': 'renamed', 'price': 'not-an-int'},
        )
        self.assertEqual(response.status_code, 400)

    def test_get_still_works(self):
        response = self.client.get('/api/products')
        self.assertEqual(response.status_code, 200)

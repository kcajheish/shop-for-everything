from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Product
class ProductListViewTest(TestCase):

    def test_url_exist_at_address(self):
        response = self.client.get('/product/list')
        self.assertEquals(response.status_code, 200)

    def test_view_accessible_by_name(self):
        response = self.client.get(reverse('product_list'))
        self.assertEquals(response.status_code,200)
    
    def test_view_use_correct_template(self):
        response = self.client.get('/product/list')
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/list.html')


class ProductDetailTest(TestCase):
    def test_unknown_slug_returns_404(self):
        response = self.client.get('/product/detail/does-not-exist')
        self.assertEqual(response.status_code, 404)


class ProductSearchTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='search_user', password='pw')
        self.p1 = Product.objects.create(name='紅蘋果', price=10, description='a', author=self.user)
        self.p2 = Product.objects.create(name='青蘋果', price=20, description='b', author=self.user)
        self.p3 = Product.objects.create(name='香蕉', price=30, description='c', author=self.user)

    def test_search_without_query_on_fresh_session(self):
        response = self.client.get('/product/search')
        self.assertEqual(response.status_code, 200)

    def test_search_does_not_return_duplicates(self):
        response = self.client.get('/product/search?query=蘋果 蘋果')
        self.assertEqual(response.status_code, 200)
        names = [p.name for p in response.context['current_page'].object_list]
        self.assertEqual(names.count('紅蘋果'), 1)
        self.assertEqual(names.count('青蘋果'), 1)


class PaginationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='page_user', password='pw')
        for i in range(10):
            Product.objects.create(name='商品%d' % i, price=i, description='d', author=self.user)

    def test_invalid_page_returns_first_page(self):
        response = self.client.get('/product/list?page=abc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['current_page'].number, 1)

    def test_out_of_range_page_returns_last_page(self):
        response = self.client.get('/product/list?page=999')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['current_page'].number,
            response.context['current_page'].paginator.num_pages,
        )


class ProductCreateAuthorTest(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(username='creator', password='pw')
        self.other = User.objects.create_user(username='other', password='pw')

    def test_author_is_set_to_request_user_and_cannot_be_spoofed(self):
        self.client.force_login(self.author)
        response = self.client.post('/product/create', {
            'name': '我的商品',
            'description': 'd',
            'price': 10,
            'stock': 5,
            'author': self.other.id,
        })
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name='我的商品')
        self.assertEqual(product.author, self.author)


class ProductDeleteAccessTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pw')
        self.other = User.objects.create_user(username='other', password='pw')
        self.product = Product.objects.create(
            name='del', price=1, stock=5, description='d', author=self.owner,
        )

    def test_get_is_rejected(self):
        self.client.force_login(self.owner)
        response = self.client.get('/product/delete')
        self.assertEqual(response.status_code, 405)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.post('/product/delete', {'product_id': self.product.id})
        self.assertEqual(response.status_code, 302)
        self.assertIn('/user/login', response.url)

    def test_non_owner_gets_403(self):
        self.client.force_login(self.other)
        response = self.client.post('/product/delete', {'product_id': self.product.id})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Product.objects.filter(pk=self.product.id).exists())

    def test_owner_can_delete(self):
        self.client.force_login(self.owner)
        response = self.client.post('/product/delete', {'product_id': self.product.id})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Product.objects.filter(pk=self.product.id).exists())
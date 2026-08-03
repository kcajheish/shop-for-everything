from unittest import mock

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from orders.models import Order, OrderProduct
from products.models import Product


class OrderDetailTest(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username='buyer', password='pw')
        self.other = User.objects.create_user(username='other', password='pw')

    def test_owner_can_view_own_order(self):
        order = Order.objects.create(customer=self.buyer)
        self.client.force_login(self.buyer)
        response = self.client.get(reverse('order_detail', args=[order.id]))
        self.assertEqual(response.status_code, 200)

    def test_other_user_cannot_view_order(self):
        order = Order.objects.create(customer=self.buyer)
        self.client.force_login(self.other)
        response = self.client.get(reverse('order_detail', args=[order.id]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_is_redirected_to_login(self):
        order = Order.objects.create(customer=self.buyer)
        response = self.client.get(reverse('order_detail', args=[order.id]))
        self.assertEqual(response.status_code, 302)


class CheckoutTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='seller', password='pw')
        self.buyer = User.objects.create_user(username='buyer', password='pw')
        self.product = Product.objects.create(
            name='test', price=100, stock=10,
            description='desc', author=self.seller,
        )

    def put_in_cart(self, quantity):
        session = self.client.session
        session['cart'] = {str(self.product.id): {'quantity': quantity, 'price': self.product.price}}
        session.save()

    def test_checkout_creates_order_decrements_stock_and_dispatches_email(self):
        self.client.force_login(self.buyer)
        self.put_in_cart(2)
        with mock.patch('orders.views.send_order_success_email.delay') as delay:
            response = self.client.post(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(customer=self.buyer)
        delay.assert_called_once_with(self.buyer.id, order.id)
        self.assertEqual(OrderProduct.objects.filter(order=order).count(), 1)
        order_product = order.products.get()
        self.assertEqual(order_product.quantity, 2)
        self.assertEqual(order_product.expense, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)

    def test_checkout_rolls_back_when_stock_insufficient(self):
        self.client.force_login(self.buyer)
        self.product.stock = 1
        self.product.save()
        self.put_in_cart(2)
        response = self.client.post(reverse('checkout'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(OrderProduct.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)

    def test_checkout_succeeds_even_if_email_dispatch_fails(self):
        self.client.force_login(self.buyer)
        self.put_in_cart(1)
        with mock.patch(
            'orders.views.send_order_success_email.delay',
            side_effect=Exception('broker down'),
        ):
            response = self.client.post(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 9)

    def test_checkout_get_is_rejected(self):
        self.client.force_login(self.buyer)
        self.put_in_cart(1)
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 405)

    def test_checkout_with_empty_cart_redirects(self):
        self.client.force_login(self.buyer)
        response = self.client.post(reverse('checkout'))
        self.assertRedirects(response, reverse('cart_detail'))

    def test_checkout_redirects_when_cart_contains_deleted_product(self):
        self.client.force_login(self.buyer)
        self.put_in_cart(1)
        self.product.delete()
        response = self.client.post(reverse('checkout'))
        self.assertRedirects(response, reverse('cart_detail'))
        self.assertEqual(Order.objects.count(), 0)

    def test_cart_detail_renders_with_deleted_product(self):
        self.client.force_login(self.buyer)
        self.put_in_cart(1)
        self.product.delete()
        response = self.client.get(reverse('cart_detail'))
        self.assertEqual(response.status_code, 200)

    def test_order_detail_fetches_products_with_single_query(self):
        self.client.force_login(self.buyer)
        order = Order.objects.create(customer=self.buyer)
        for _ in range(3):
            OrderProduct.objects.create(
                order=order, from_user=self.buyer, to_user=self.seller,
                product=self.product, quantity=1, expense=10,
            )
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('order_detail', args=[order.id]))
        self.assertEqual(response.status_code, 200)
        product_queries = [q for q in ctx.captured_queries if 'products_product' in q['sql']]
        self.assertEqual(len(product_queries), 1)


class OrderProductValidatorTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='v_seller', password='pw')
        self.buyer = User.objects.create_user(username='v_buyer', password='pw')
        self.product = Product.objects.create(
            name='v', price=10, stock=5, description='d', author=self.seller,
        )
        self.order = Order.objects.create(customer=self.buyer)

    def test_negative_quantity_is_rejected(self):
        op = OrderProduct(
            order=self.order, from_user=self.buyer, to_user=self.seller,
            product=self.product, quantity=-1, expense=10,
        )
        with self.assertRaises(ValidationError):
            op.full_clean()

    def test_negative_expense_is_rejected(self):
        op = OrderProduct(
            order=self.order, from_user=self.buyer, to_user=self.seller,
            product=self.product, quantity=1, expense=-10,
        )
        with self.assertRaises(ValidationError):
            op.full_clean()


class SendOrderEmailTest(TestCase):
    def setUp(self):
        self.seller = User.objects.create_user(username='e_seller', password='pw')
        self.buyer = User.objects.create_user(username='e_buyer', password='pw', email='buyer@example.com')
        self.product = Product.objects.create(
            name='e', price=10, stock=5, description='d', author=self.seller,
        )
        self.order = Order.objects.create(customer=self.buyer)
        OrderProduct.objects.create(
            order=self.order, from_user=self.buyer, to_user=self.seller,
            product=self.product, quantity=1, expense=10,
        )

    @mock.patch('orders.tasks.send_mail')
    def test_email_uses_configured_sender(self, send_mail):
        from django.conf import settings
        from orders.tasks import send_order_success_email
        send_order_success_email(self.buyer.id, self.order.id)
        _, kwargs = send_mail.call_args
        self.assertEqual(kwargs['from_email'], settings.DEFAULT_FROM_EMAIL)

from unittest import mock

from django.contrib.auth.models import User
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

from django.test import TestCase
from django.contrib.auth.models import User


class SignUpFormTest(TestCase):
    def test_empty_passwords_do_not_500(self):
        response = self.client.post('/user/signup', {
            'username': 'newbie',
            'password': '',
            'password_confirm': '',
            'email': 'a@b.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newbie').exists())

    def test_mismatched_passwords_are_rejected(self):
        response = self.client.post('/user/signup', {
            'username': 'newbie2',
            'password': 'aaa',
            'password_confirm': 'bbb',
            'email': 'a@b.com',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newbie2').exists())

    def test_valid_signup_creates_user(self):
        response = self.client.post('/user/signup', {
            'username': 'newbie3',
            'password': 'secret123',
            'password_confirm': 'secret123',
            'email': 'a@b.com',
        })
        self.assertRedirects(response, '/user/signup-success')
        self.assertTrue(User.objects.filter(username='newbie3').exists())

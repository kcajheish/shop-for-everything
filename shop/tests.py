import os

from django.conf import settings
from django.test import TestCase


LEAKED_SECRET_KEY = 't)%0b&=8v4g9kdjk(kmfj6vt9u2dc_8=0!9-x(yaz$t+h8n-ia'


class SettingsSecurityTest(TestCase):
    def test_leaked_secret_key_is_not_used(self):
        self.assertNotEqual(settings.SECRET_KEY, LEAKED_SECRET_KEY)

    def test_debug_defaults_to_false(self):
        if 'DJANGO_DEBUG' not in os.environ:
            self.assertFalse(settings.DEBUG)


class CelerySettingsTest(TestCase):
    def test_celery_accept_content_is_configured(self):
        self.assertTrue(hasattr(settings, 'CELERY_ACCEPT_CONTENT'))

    def test_celery_timezone_is_a_string(self):
        self.assertIsInstance(settings.CELERY_TIMEZONE, str)

    def test_default_from_email_is_configured(self):
        self.assertEqual(settings.DEFAULT_FROM_EMAIL, 'shopEveryThing@myshop.com')

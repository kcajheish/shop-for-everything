from django.test import TestCase, override_settings
from ..models import Product
from django.contrib.auth.models import User
from unidecode import unidecode
from django.utils.text import slugify
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image as PILImage
import io
import tempfile
# Create your tests here.
class ProductModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            username = 'test_user',
            password = 'test_password',
        )
        cls.user.save()

        cls.product = Product(
            name = "測試產品",
            price = 100,
            description = "測試產品描述",
            author = cls.user,
        )
        cls.product.save()

    def test_name_max_length(self):
        #在test裡，被建立的第一個物件id為1
        product = Product.objects.get(pk=1)
        print(product.slug)
        max_length = product._meta.get_field('name').max_length
        #左邊實際值 右邊期望值
        self.assertEquals(max_length, 50)
        
    def test_slug_is_unique(self):
        product = Product.objects.get(pk=1)
        is_unique = product._meta.get_field('slug').unique
        self.assertEquals(is_unique, True)

    def test_slug_not_null(self):
        product = Product.objects.get(pk=1)
        is_null = product._meta.get_field('slug').null
        self.assertEquals(is_null, False)
    
    def test_pubdate_field_label(self):
        product = Product.objects.get(pk=1)
        field_label = product._meta.get_field('pub_date').verbose_name
        self.assertEquals(field_label, 'first published date')
    
    def test_last_date_field_label(self):
        product = Product.objects.get(pk=1)
        field_label = product._meta.get_field('last_date').verbose_name
        self.assertEquals(field_label, 'last modified date')
    
    def test_default_image_path(self):
        product = Product.objects.get(pk=1)
        image = product.image
        self.assertEquals(image.url, '/media/default.jpg')


class ProductSlugTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='slug_user', password='pw')

    def test_duplicate_name_gets_unique_slug(self):
        p1 = Product.objects.create(name='重複', price=1, description='d', author=self.user)
        p2 = Product.objects.create(name='重複', price=2, description='d', author=self.user)
        self.assertNotEqual(p1.slug, p2.slug)
        self.assertTrue(p2.slug.endswith('-2'))
        self.assertEqual(Product.objects.filter(slug=p2.slug).count(), 1)

    def test_slug_stays_stable_on_update(self):
        product = Product.objects.create(name='穩定', price=1, description='d', author=self.user)
        old_slug = product.slug
        product.price = 999
        product.save()
        product.refresh_from_db()
        self.assertEqual(product.slug, old_slug)


class ProductImageResizeTest(TestCase):
    @override_settings(MEDIA_ROOT=tempfile.mkdtemp())
    def test_uploaded_image_is_resized(self):
        buf = io.BytesIO()
        PILImage.new('RGB', (600, 400), 'red').save(buf, format='JPEG')
        image = SimpleUploadedFile('big.jpg', buf.getvalue(), content_type='image/jpeg')
        user = User.objects.create_user(username='img_user', password='pw')
        product = Product.objects.create(
            name='大圖', price=1, description='d', author=user, image=image,
        )
        with PILImage.open(product.image.path) as img:
            self.assertLessEqual(img.width, 300)
            self.assertLessEqual(img.height, 300)

from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
import time
from django.utils.text import slugify
from PIL import Image
from django.urls import reverse
from unidecode import unidecode

from pygments.lexers import get_all_lexers
from pygments.styles import get_all_styles

LEXERS = [item for item in get_all_lexers() if item[1]]
LANGUAGE_CHOICES = sorted([(item[1][0], item[0]) for item in LEXERS])
STYLE_CHOICES = sorted([(item, item) for item in get_all_styles()])

class Product(models.Model):
    name = models.CharField(max_length = 50)
    price = models.IntegerField(validators = [MinValueValidator(0)])
    stock = models.IntegerField(validators = [MinValueValidator(0)], default = 0)
    description = models.TextField(max_length = 250)
    pub_date = models.DateTimeField(auto_now_add = True, verbose_name='first published date')
    last_date = models.DateTimeField(auto_now = True, verbose_name='last modified date')
    author = models.ForeignKey(User, on_delete = models.CASCADE, blank=True)
    def get_image_path(instance, filename):
        current_time = time.strftime("%Y/%m/%d")
        return f"products/{current_time}/{filename}"
    image = models.ImageField(upload_to=get_image_path, null=True, blank=True, default='/default.jpg')
    slug = models.SlugField(max_length = 50, blank = True, unique=True, allow_unicode=True)

    def update_stock(self, qty):
        self.stock = qty

    def _generate_slug(self):
        base = slugify(unidecode(self.name)) or 'product'
        slug = base
        num = 2
        while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            tail = '-%d' % num
            slug = base[:50 - len(tail)] + tail
            num += 1
        return slug

    def save(self, *args, **kwargs):
        if not self.pk:
            self.slug = self._generate_slug()
        super().save(*args, **kwargs)
        #將圖片大小調整為300x300像素
        if self.image and self.image.name != '/default.jpg':
            try:
                initial_path = self.image.path
                img = Image.open(self.image.open())
                size = 300, 300
                img.thumbnail(size)
                img.save(initial_path, quality=95)
            except (IOError, OSError):
                pass

    def get_absolute_url(self):
        return reverse('product_detail', args = [self.slug])
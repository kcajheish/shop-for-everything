# Generated by Django 2.1.1 on 2020-01-24 08:25

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import products.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('price', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('description', models.TextField(max_length=250)),
                ('pub_date', models.DateTimeField(auto_now_add=True)),
                ('last_date', models.DateTimeField(auto_now=True)),
                ('image', models.ImageField(upload_to=products.models.Product.get_image_path)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
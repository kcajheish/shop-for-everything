from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

#讓celery使用django環境裡的設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')

app = Celery('shop')

#namespace: 從settings讀取所有'Celery'開頭的參數
app.config_from_object('django.conf:settings', namespace='CELERY')

#從django定義的所有app folder，尋找celery註冊的function
app.autodiscover_tasks()
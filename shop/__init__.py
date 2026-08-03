
from __future__ import absolute_import, unicode_literals

#將celery app讀取，確保server啟動後，celery app 一定會被執行
from .celery import app as celery_app

#讓celery_app變global
__all__ = ('celery_app',)
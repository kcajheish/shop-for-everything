from __future__ import absolute_import, unicode_literals
#從celery library 輸入shared_task功能
from celery import shared_task
import time
from django.conf import settings
from django.core.mail import BadHeaderError, send_mail
from django.contrib.auth.models import User
from .models import Order
from django.template.loader import render_to_string
#autodiscover_tasks() 會搜尋所有tasks.py 被標記@shared_task的功能
@shared_task
def say_hello():
    #模擬繁重的運算
    time.sleep(6)

    return None

@shared_task
def add(x, y):
    return x + y

@shared_task
def xsum(numbers):
    return sum(numbers)

@shared_task
def send_order_success_email(user_id, order_id):
    
    order = Order.objects.get(pk=int(order_id))
    user = User.objects.get(pk=int(user_id))
    recipient_list = (
        user.email,
    )

    html_message= render_to_string(
        'orders/email_template.html', 
        {
            'order':order, 
            'user':user,
        }
    )

    send_mail(
        subject ='[下單成功]你已經成功下單',
        message = '',
        from_email = settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        fail_silently = False,
        html_message=html_message,
    )  
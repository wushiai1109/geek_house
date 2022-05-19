# coding:utf-8

from celery import Celery
from geek_house.utils.send_message import SendMessageUtil

# 定义celery对象
celery_app = Celery("geek_house", broker="redis://localhost:6379/1")


@celery_app.task
def send_sms(tid, mobile, datas):
    """发送短信的异步任务"""
    send_message_util = SendMessageUtil()
    send_message_util.send_message(tid, mobile, datas)

# celery开启的命令
# python3 -m celery -A geek_house.utils.celery_task worker -l info

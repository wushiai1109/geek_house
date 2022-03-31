# coding:utf-8

from celery import Celery
# 为什么使用CELERY而不使用线程发送耗时任务：https://blog.csdn.net/qq_42377379/article/details/84997915
# 为什么要使用celery，以及broker的选择标准：https://blog.csdn.net/weixin_45572139/article/details/106469805?spm=1001.2101.3001.6650.3&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7ERate-3.pc_relevant_antiscan_v2&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7ERate-3.pc_relevant_antiscan_v2&utm_relevant_index=6
from geek_house.libs.CCP import CCP

# 定义celery对象
celery_app = Celery("geek_house", broker="redis://49.235.15.188:6379/1")


# 然后后面要去指明 Redis 的这样的数据库了，如果不去指明的话，那默认使用的是 Redis 里面的 0 号库，
# Redis的有数据库这里知道，它一共有 16 个库，默认尺度是0。那么之前是不是在项目当中已经去用过别的库了，所以咱们就来独立一下。
# 比如说独立哪个东西呢？咱们把 0 号空出来，我使用一号库。好比如说使用这样的一号库，那就斜线指明 1 就可以了，
# 这相当于我指明了一个 brook 中间消息人指明完了之后，那我接下来就可以去定义任务了。

@celery_app.task
def send_sms(tid, mobile, datas):
    """发送短信的异步任务"""
    ccp = CCP()
    ccp.send_message(tid, mobile, datas)

# celery开启的命令
# celery -A geek_house.tasks.task_sms worker -l info

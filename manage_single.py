# coding:utf-8

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# 引入session，当成一个请求的上下文，一个对象来进行存储、提取操作，session数据放在了后端-redis中
# Flask-Session https://lienze.tech/archives/181/  https://www.cnblogs.com/cnhyk/p/12755994.html  https://ziperlee.github.io/2019/03/25/flask%E5%88%86%E5%B8%83%E5%BC%8F%E9%83%A8%E7%BD%B2%E5%8F%8Aflask-session/
from flask_session import Session
from flask_wtf import CSRFProtect

import redis

# 创建flask的应用对象
app = Flask(__name__)


class Config(object):
    """配置信息"""
    SECRET_KEY = "XHSOI*Y9dfs9cshd9"

    # 数据库
    SQLALCHEMY_DATABASE_URI = "mysql://root:@WSAwsa18723746541@49.235.15.188:3306/geek_house"
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis
    REDIS_HOST = "49.235.15.188"
    REDIS_PORT = 6379

    # flask-session配置
    SESSION_TYPE = "redis"
    # 实际中使用redis的服务器不是同一台
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # 对cookie中session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 86400  # session数据的有效期，单位秒


app.config.from_object(Config)

db = SQLAlchemy(app)

# 创建redis连接对象
redis_store = redis.StrictRedis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# 利用flask-session，将session数据保存到redis中
Session(app)

# 为flask补充csrf防护
CSRFProtect(app)


@app.route("/index")
def index():
    return "index page"


if __name__ == '__main__':
    app.run()

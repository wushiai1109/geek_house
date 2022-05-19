# coding:utf-8

import redis
from urllib import parse


class Config(object):
    """配置信息"""
    SECRET_KEY = "XHSOI*Y9dfs9cshd9"

    # 数据库
    # SQLALCHEMY_DATABASE_URI用于连接的数据库URI：sqlite:////tmp/test.db 或 mysql://username:password@server/db
    SQLALCHEMY_DATABASE_URI = "mysql://root:{}@localhost:3306/geek_house?charset=utf8".format(
        parse.quote_plus("@WSAwsa18723746541"))
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379

    # flask-session配置
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=2)
    SESSION_USE_SIGNER = True  # 对cookie中session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 7200  # session数据的有效期，单位秒


class DevelopmentConfig(Config):
    """开发模式的配置信息"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置信息"""
    pass


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductionConfig
}

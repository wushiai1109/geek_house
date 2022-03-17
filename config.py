# coding:utf-8

import redis


class Config(object):
    """配置信息"""
    # 随便写
    # https://blog.csdn.net/Enjolras_fuu/article/details/82152834
    # https://blog.csdn.net/diyiday/article/details/80578355?utm_medium=distribute.pc_relevant.none-task-blog-2~default~baidujs_title~default-1.queryctrv4&spm=1001.2101.3001.4242.2&utm_relevant_index=4
    SECRET_KEY = "XHSOI*Y9dfs9cshd9"

    # 数据库
    # SQLALCHEMY_DATABASE_URI用于连接的数据库URI：sqlite:////tmp/test.db 或 mysql://username:password@server/db
    # http://www.pythondoc.com/flask-sqlalchemy/config.html
    SQLALCHEMY_DATABASE_URI = "mysql://root:@WSAwsa18723746541@localhost:3306/geek_house"
    # https://www.jianshu.com/p/6e8abf8f5d61 这个配置键的作用是：如果设置成 True (默认情况)，Flask-SQLAlchemy 将会追踪对象的修改并且发送信号。这需要额外的内存， 如果不必要的可以禁用它。
    # 配置完成后即可在shell模式下测试，通过db.create_all()创建数据库，然后添加一些行，用db.session.add()添加，最后用db.session.commit()提交（修改行，删除行等不做赘述）。检验方式可以继续在shell模式下用命令查你插入行的id值是否已经添加，或者借助图形化工具MySQLWorkbench检验。
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # redis
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379

    # flask-session配置
    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # 对cookie中session_id进行隐藏处理
    PERMANENT_SESSION_LIFETIME = 86400  # session数据的有效期，单位秒


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

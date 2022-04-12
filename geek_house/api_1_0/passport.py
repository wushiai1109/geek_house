# coding:utf-8

from geek_house.api_1_0 import api
# 聊一聊 Flask 的 jsonify: https://www.jianshu.com/p/a25357f2d930
from flask import request, jsonify, current_app, session
from geek_house.conf.response_code import RET
from geek_house import redis_store, db
from geek_house.conf import constants
from geek_house.models.models import GeekHouseUser
from sqlalchemy.exc import IntegrityError  # 重复键
import re


@api.route("/users/retrieve", methods=["POST"])
def retrieve():
    """
    重置密码
    请求的参数： 手机号、短信验证码、密码、确认密码
    参数格式：json
    """
    # 获取请求的json数据，返回字典
    req_dict = request.get_json()

    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 校验参数
    if not all([mobile, sms_code, password, password2]):
        return jsonify(code=RET.PARAMERR, msg="参数不完整")

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        # 表示格式不对
        return jsonify(code=RET.PARAMERR, msg="手机号格式错误")

    if password != password2:
        return jsonify(code=RET.PARAMERR, msg="两次密码不一致")

    # 从redis中取出短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
        real_sms_code = real_sms_code.decode()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="读取真实短信验证码异常")

    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(code=RET.NODATA, msg="短信验证码失效")

    # 删除redis中的短信验证码，防止重复使用校验
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写短信验证码的正确性
    if real_sms_code != sms_code:
        return jsonify(code=RET.DATAERR, msg="短信验证码错误")

    # 保存用户的注册数据到数据库中
    exist_user = GeekHouseUser.query.filter(GeekHouseUser.mobile == mobile).first()
    if not exist_user:
        user = GeekHouseUser(name=mobile, mobile=mobile)
        user.password = password  # 设置属性
        user.avatar_url = 'default_avatar'
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError as e:
            # 数据库操作错误后的回滚
            db.session.rollback()
            # 表示手机号出现了重复值，即手机号已注册过
            current_app.logger.error(e)
            return jsonify(code=RET.DATAEXIST, msg="手机号已存在")
        except Exception as e:
            db.session.rollback()
            # 表示手机号出现了重复值，即手机号已注册过
            current_app.logger.error(e)
            return jsonify(code=RET.DBERR, msg="查询数据库异常")
        # 保存登录状态到session中
        session["name"] = mobile
        session["mobile"] = mobile
        session["user_id"] = user.id
    else:
        exist_user.password = password
        db.session.commit()
        session["name"] = exist_user.name
        session["mobile"] = exist_user.mobile
        session["user_id"] = exist_user.id

    # 返回结果
    return jsonify(code=RET.OK, msg="重置密码成功")


@api.route("/users", methods=["POST"])
def register():
    """注册
    请求的参数： 手机号、短信验证码、密码、确认密码
    参数格式：json
    """
    # 获取请求的json数据，返回字典
    req_dict = request.get_json()

    mobile = req_dict.get("mobile")
    sms_code = req_dict.get("sms_code")
    password = req_dict.get("password")
    password2 = req_dict.get("password2")

    # 校验参数
    if not all([mobile, sms_code, password, password2]):
        return jsonify(code=RET.PARAMERR, msg="参数不完整")

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        # 表示格式不对
        return jsonify(code=RET.PARAMERR, msg="手机号格式错误")

    if password != password2:
        return jsonify(code=RET.PARAMERR, msg="两次密码不一致")

    # 从redis中取出短信验证码
    try:
        real_sms_code = redis_store.get("sms_code_%s" % mobile)
        real_sms_code = real_sms_code.decode()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="读取真实短信验证码异常")

    # 判断短信验证码是否过期
    if real_sms_code is None:
        return jsonify(code=RET.NODATA, msg="短信验证码失效")

    # 删除redis中的短信验证码，防止重复使用校验
    try:
        redis_store.delete("sms_code_%s" % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断用户填写短信验证码的正确性
    if real_sms_code != sms_code:
        return jsonify(code=RET.DATAERR, msg="短信验证码错误")

    # 判断用户的手机号是否注册过
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(code=RET.DBERR, msg="数据库异常")
    # else:
    #     if user is not None:
    #         # 表示手机号已存在
    #         return jsonify(code=RET.DATAEXIST, msg="手机号已存在")
    #  # 保存用户的注册数据到数据库中
    # user = User()
    # db.session.add(user)
    # db.session.commit()

    # 盐值   salt  随机字符串

    #  注册
    #  用户1   password="123456" + "abc"   sha1   abc$hxosifodfdoshfosdhfso
    #  用户2   password="123456" + "def"   sha1   def$dfhsoicoshdoshfosidfs
    #
    # 用户登录  password ="123456"  "abc"  sha256      sha1   hxosufodsofdihsofho

    # 保存用户的注册数据到数据库中
    user = GeekHouseUser(name=mobile, mobile=mobile)
    # user.generate_password_hash(password)

    user.password = password  # 设置属性
    user.avatar_url = 'default_avatar'

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 数据库操作错误后的回滚
        db.session.rollback()
        # 表示手机号出现了重复值，即手机号已注册过
        current_app.logger.error(e)
        return jsonify(code=RET.DATAEXIST, msg="手机号已存在")
    except Exception as e:
        db.session.rollback()
        # 表示手机号出现了重复值，即手机号已注册过
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="查询数据库异常")

    # 保存登录状态到session中
    session["name"] = mobile
    session["mobile"] = mobile
    session["user_id"] = user.id

    # 返回结果
    return jsonify(code=RET.OK, msg="注册成功")


@api.route("/sessions", methods=["POST"])
def login():
    """用户登录
    参数： 手机号、密码， json
    """
    # 获取参数
    req_dict = request.get_json()
    mobile = req_dict.get("mobile")
    password = req_dict.get("password")

    # 校验参数
    # 参数完整的校验
    if not all([mobile, password]):
        return jsonify(code=RET.PARAMERR, msg="参数不完整")

    # 手机号的格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(code=RET.PARAMERR, msg="手机号格式错误")

    # 判断错误次数是否超过限制，如果超过限制，则返回
    # redis记录： "access_ip_请求的ip": "次数"
    user_ip = request.remote_addr  # 用户的ip地址
    try:
        access_nums = redis_store.get("access_ip_%s" % user_ip)
        access_nums = access_nums.decode()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(code=RET.REQERR, msg="错误次数过多，请稍后重试")

    # 从数据库中根据手机号查询用户的数据对象
    try:
        user = GeekHouseUser.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="获取用户信息失败")

    # 用数据库的密码与用户填写的密码进行对比验证
    if user is None or not user.check_password(password):
        # 如果验证失败，记录错误次数，返回信息
        try:
            # redis的incr可以对字符串类型的数字数据进行加一操作，如果数据一开始不存在，则会初始化为1
            redis_store.incr("access_ip_%s" % user_ip)
            redis_store.expire("access_ip_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(code=RET.DATAERR, msg="手机号或密码错误")

    # 如果验证相同成功，保存登录状态， 在session中
    session["name"] = user.name
    session["mobile"] = user.mobile
    session["user_id"] = user.id

    return jsonify(code=RET.OK, msg="登录成功")


@api.route("/session", methods=["GET"])
def check_login():
    """检查登陆状态"""
    # 尝试从session中获取用户的名字
    name = session.get("name")
    # 如果session中数据name名字存在，则表示用户已登录，否则未登录
    if name is not None:
        return jsonify(code=RET.OK, msg="true", data={"name": name})
    else:
        return jsonify(code=RET.SESSIONERR, msg="false")


@api.route("/session", methods=["DELETE"])
def logout():
    """登出"""
    # 清除session数据
    csrf_token = session.get("csrf_token")
    session.clear()
    session["csrf_token"] = csrf_token
    return jsonify(code=RET.OK, msg="OK")

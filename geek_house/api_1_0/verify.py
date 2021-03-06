# coding:utf-8
from geek_house.api_1_0 import api
from geek_house.utils.captcha.captcha import captcha
from geek_house import redis_store
from geek_house.conf import constants
from flask import current_app, jsonify, make_response, request
from geek_house.conf.response_code import RET
from geek_house.models.models import GeekHouseUser
import random
from geek_house.utils.celery_task import send_sms


# GET /api/v1.0/image_codes/<image_code_id>
@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    : params image_code_id:  图片验证码编号
    :return:  正常:验证码图片  异常：返回json
    """
    # 业务逻辑处理，生成验证码图片
    # 名字，真实文本， 图片数据
    name, text, image_data = captcha.generate_captcha()

    # 将验证码真实值与编号保存到redis中, 设置有效期
    # redis：  字符串   列表  哈希   set
    # "key": xxx
    # 使用哈希维护有效期的时候只能整体设置
    # "image_codes": {"id1":"abc", "":"", "":""} 哈希  hset("image_codes", "id1", "abc")  hget("image_codes", "id1")

    # 单条维护记录，选用字符串
    # "image_code_编号1": "真实值"
    # "image_code_编号2": "真实值"

    # redis_store.set("image_code_%s" % image_code_id, text)
    # redis_store.expire("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES)
    #                   记录名字                          有效期                              记录值
    try:
        redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="保存图片验证码失败")

    # 返回图片
    resp = make_response(image_data)
    resp.headers["Content-Type"] = "image/jpg"
    return resp


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
@api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""
    # 获取参数
    image_code_id = request.args.get("image_code_id")
    image_code = request.args.get("image_code")

    # 校验参数
    if not all([image_code_id, image_code]):
        # 表示参数不完整
        return jsonify(code=RET.PARAMERR, msg="参数不完整")

    # 业务逻辑处理
    # 从redis中取出真实的图片验证码
    try:
        real_image_code = redis_store.get("image_code_%s" % image_code_id)
        if real_image_code:
            real_image_code = real_image_code.decode()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="redis数据库异常")

    # 判断图片验证码是否过期
    if real_image_code is None:
        # 表示图片验证码没有或者过期
        return jsonify(code=RET.NODATA, msg="图片验证码失效")

    # 删除redis中的图片验证码，防止用户使用同一个图片验证码验证多次
    try:
        redis_store.delete("image_code_%s" % image_code_id)
    except Exception as e:
        current_app.logger(e)

    real_image_code = real_image_code
    # 与用户填写的值进行对比
    if real_image_code.lower() != image_code.lower():
        # 表示用户填写错误
        return jsonify(code=RET.DATAERR, msg="图片验证码错误")

    # 判断对于这个手机号的操作，在60秒内有没有之前的记录，如果有，则认为用户操作频繁，不接受处理
    try:
        send_flag = redis_store.get("send_sms_code_%s" % mobile)
        if send_flag:
            send_flag = send_flag.decode()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示在60秒内之前有过发送的记录
            return jsonify(code=RET.REQERR, msg="请求过于频繁，请60秒后重试")

    # 判断手机号是否存在
    # try:
    #     user = GeekHouseUser.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    # else:
    #     if user is not None:
    #         # 表示手机号已存在
    #         return jsonify(code=RET.DATAEXIST, msg="手机号已存在")
    #
    # 如果手机号不存在，则生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存真实的短信验证码
    try:
        redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给这个手机号的记录，防止用户在60s内再次出发发送短信的操作
        redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="保存短信验证码异常")

    # # 发送短信
    # try:
    #     ccp = CCP()
    #     result = ccp.send_message(1, mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)])
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(code=RET.THIRDERR, msg="发送异常")
    # # 返回值
    # if result == 0:
    #     # 发送成功
    #     return jsonify(code=RET.OK, msg="发送成功")
    # else:
    #     return jsonify(code=RET.THIRDERR, msg="发送失败")

    # 发送短信
    # 使用celery异步发送短信, delay函数调用后立即返回（非阻塞）
    send_sms.delay(1, mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)])

    # # 返回异步任务的对象
    # result_obj = send_sms.delay(1, mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)])
    # print(result_obj.id)
    #
    # # 通过异步任务对象的get方法获取异步任务的结果, 默认get方法是阻塞的
    # ret = result_obj.get()
    # print("ret=%s" % ret)

    # 返回值
    # 发送成功
    return jsonify(code=RET.OK, msg="发送成功")

#
#
# # GET /api/v1.0/sms_codes/<mobile>?image_code=xxxx&image_code_id=xxxx
# @api.route("/sms_codes/<re(r'1[34578]\d{9}'):mobile>")
# def get_sms_code(mobile):
#     """获取短信验证码"""
#     # 获取参数
#     image_code_id = request.args.get("image_code_id")
#     image_code = request.args.get("image_code")
#
#     # 校验参数
#     if not all([image_code_id, image_code]):
#         # 表示参数不完整
#         return jsonify(code = RET.PARAMERR, msg="参数不完整")
#
#     # 业务逻辑处理
#     # 从redis中取出真实的图片验证码
#     try:
#         real_image_code = redis_store.get("image_code_%s" % image_code_id)
#         real_image_code = real_image_code.decode()
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(code=RET.DBERR, msg="redis数据库异常")
#
#     # 判断图片验证码是否过期
#     if real_image_code is None:
#         # 表示图片验证码没有或者过期
#         return jsonify(code=RET.NODATA, msg="图片验证码失效")
#
#     # 删除redis中的图片验证码，防止用户使用同一个图片验证码验证多次
#     try:
#         redis_store.delete("image_code_%s" % image_code_id)
#     except Exception as e:
#         current_app.logger(e)
#
#     real_image_code = real_image_code.decode()
#     # 与用户填写的值进行对比
#     if real_image_code.lower() != image_code.lower():
#         # 表示用户填写错误
#         return jsonify(code=RET.DATAERR, msg="图片验证码错误")
#
#     # 判断对于这个手机号的操作，在60秒内有没有之前的记录，如果有，则认为用户操作频繁，不接受处理
#     try:
#         send_flag = redis_store.get("send_sms_code_%s" % mobile)
#         send_flag = send_flag.decode()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if send_flag is not None:
#             # 表示在60秒内之前有过发送的记录
#             return jsonify(code=RET.REQERR, msg="请求过于频繁，请60秒后重试")
#
#     # 判断手机号是否存在
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user is not None:
#             # 表示手机号已存在
#             return jsonify(code=RET.DATAEXIST, msg="手机号已存在")
#
#     # 如果手机号不存在，则生成短信验证码
#     sms_code = "%06d" % random.randint(0, 999999)
#
#     # 保存真实的短信验证码
#     try:
#         redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
#         # 保存发送给这个手机号的记录，防止用户在60s内再次出发发送短信的操作
#         redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(code=RET.DBERR, msg="保存短信验证码异常")
#
#     # 发送短信
#     try:
#         ccp = CCP()
#         result = ccp.send_message(1, mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)])
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(code=RET.THIRDERR, msg="发送异常")
#
#     # 返回值
#     if result == 0:
#         # 发送成功
#         return jsonify(code=RET.OK, msg="发送成功")
#     else:
#         return jsonify(code=RET.THIRDERR, msg="发送失败")
#
#

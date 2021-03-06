# coding:utf-8

from geek_house.api_1_0 import api
from geek_house.utils.login_required import login_required
from geek_house.models.models import GeekHouseOrder
from flask import g, current_app, jsonify, request
from geek_house.conf.response_code import RET
from alipay import AliPay
from geek_house import db
from geek_house.conf import constants
import os


@api.route("/orders/<int:order_id>/payment", methods=["POST"])
@login_required
def order_pay(order_id):
    """发起支付宝支付"""
    user_id = g.user_id

    # 判断订单状态
    try:
        order = GeekHouseOrder.query.filter(GeekHouseOrder.id == order_id, GeekHouseOrder.user_id == user_id,
                                            GeekHouseOrder.status == "WAIT_PAYMENT").first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="数据库异常")

    if order is None:
        return jsonify(code=RET.NODATA, msg="订单数据有误")

    # 创建支付宝sdk的工具对象
    alipay_client = AliPay(
        appid="2021000118650926",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=open(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "/conf/keys/app_private_key.pem").read(),
        # 私钥
        alipay_public_key_string=open(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "/conf/keys/alipay_public_key.pem").read(),
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    # 手机网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
    order_string = alipay_client.api_alipay_trade_wap_pay(
        out_trade_no=order.id,  # 订单编号
        total_amount=str(order.amount / 100.0),  # 总金额
        subject=u"GEEK租房 %s" % order.id,  # 订单标题
        return_url="http://www.wushiai.cn/payComplete.html",  # 返回的连接地址
        # return_url="http://localhost/payComplete.html",  # 返回的连接地址
        # return_url="http://10.1.61.32/payComplete.html",  # 返回的连接地址
        # return_url="http://192.168.1.10/payComplete.html",  # 返回的连接地址
        notify_url=None  # 可选, 不填则使用默认notify url
    )

    # 构建让用户跳转的支付连接地址
    pay_url = constants.ALIPAY_URL_PREFIX + order_string
    return jsonify(code=RET.OK, msg="OK", data={"pay_url": pay_url})


@api.route("/order/payment", methods=["PUT"])
def save_order_payment_result():
    """保存订单支付结果"""
    alipay_dict = request.form.to_dict()

    # 对支付宝的数据进行分离  提取出支付宝的签名参数sign 和剩下的其他数据
    alipay_sign = alipay_dict.pop("sign")

    # 创建支付宝sdk的工具对象
    alipay_client = AliPay(
        appid="2021000118650926",
        app_notify_url=None,  # 默认回调url
        app_private_key_string=open(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "/conf/keys/app_private_key.pem").read(),
        # 私钥
        alipay_public_key_string=open(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) + "/conf/keys/alipay_public_key.pem").read(),
        # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
        sign_type="RSA2",  # RSA 或者 RSA2
        debug=True  # 默认False
    )

    # 借助工具验证参数的合法性
    # 如果确定参数是支付宝的，返回True，否则返回false
    result = alipay_client.verify(alipay_dict, alipay_sign)

    if result:
        # 修改数据库的订单状态信息
        order_id = alipay_dict.get("out_trade_no")
        trade_no = alipay_dict.get("trade_no")  # 支付宝的交易号
        try:
            GeekHouseOrder.query.filter_by(id=order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()

    return jsonify(code=RET.OK, msg="OK")

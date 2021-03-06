# coding:utf-8

from geek_house.api_1_0 import api
from geek_house.utils.login_required import login_required
from flask import g, current_app, jsonify, request, session
from geek_house.conf.response_code import RET
from geek_house.utils.image_storage import storage
from geek_house.utils.name_auth import name_auth
from geek_house.models.models import GeekHouseUser
from geek_house import db
from geek_house.conf import constants


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
    """设置用户的头像
    参数： 图片(多媒体表单格式)  用户id (g.user_id)
    """
    # 装饰器的代码中已经将user_id保存到g对象中，所以视图中可以直接读取
    user_id = g.user_id

    # 获取图片
    image_file = request.files.get("avatar")

    if image_file is None:
        return jsonify(code=RET.PARAMERR, msg="未上传图片")

    image_data = image_file.read()

    # 调用七牛云接口上传图片, 接口返回文件名称
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.THIRDERR, msg="上传图片失败")

    # 将文件名保存到数据库中
    try:
        GeekHouseUser.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="保存图片信息失败")

    avatar_url = constants.QINIU_URL_DOMAIN + file_name
    # 保存成功返回
    return jsonify(code=RET.OK, msg="保存成功", data={"avatar_url": avatar_url})


@api.route("/users/name", methods=["PUT"])
@login_required
def change_user_name():
    """修改用户名"""
    # 使用了login_required装饰器后，可以从g对象中获取用户user_id
    user_id = g.user_id

    # 获取用户想要设置的用户名
    req_data = request.get_json()
    if not req_data:
        return jsonify(code=RET.PARAMERR, msg="参数不完整")

    name = req_data.get("name")  # 用户想要设置的名字
    if not name:
        return jsonify(code=RET.PARAMERR, msg="名字不能为空")

    # 保存用户昵称name，并同时判断name是否重复（利用数据库的唯一索引)
    try:
        GeekHouseUser.query.filter_by(id=user_id).update({"name": name})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR, msg="设置用户错误")

    # 修改session数据中的name字段
    session["name"] = name
    return jsonify(code=RET.OK, msg="OK", data={"name": name})


@api.route("/user", methods=["GET"])
@login_required
def get_user_profile():
    """获取个人信息"""
    user_id = g.user_id
    # 查询数据库获取个人信息
    try:
        user = GeekHouseUser.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="获取用户信息失败")

    if user is None:
        return jsonify(code=RET.NODATA, msg="无效操作")

    return jsonify(code=RET.OK, msg="OK", data=user.to_dict())


@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    """获取用户的实名认证信息"""
    user_id = g.user_id

    # 在数据库中查询信息
    try:
        user = GeekHouseUser.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="获取用户实名信息失败")

    if user is None:
        return jsonify(code=RET.NODATA, msg="无效操作")

    return jsonify(code=RET.OK, msg="OK", data=user.auth_to_dict())


@api.route("/users/auth", methods=["POST"])
@login_required
def set_user_auth():
    """保存实名认证信息"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(code=RET.PARAMERR, msg="参数错误")

    real_name = req_data.get("real_name")  # 真实姓名
    id_card = req_data.get("id_card")  # 身份证号

    # 参数校验
    if not all([real_name, id_card]):
        return jsonify(code=RET.PARAMERR, msg="参数错误")

    if name_auth(real_name, id_card) != 0:
        return jsonify(code=RET.AUTHERR, msg="认证失败，请检查您的输入信息")

    # 保存用户的姓名与身份证号
    try:
        GeekHouseUser.query.filter_by(id=user_id).update(dict(real_name=real_name, id_card=id_card))
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR, msg="保存用户实名信息失败")

    return jsonify(code=RET.OK, msg="OK")

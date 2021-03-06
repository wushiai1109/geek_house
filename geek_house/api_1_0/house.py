# coding:utf-8
from werkzeug.datastructures import ImmutableMultiDict

from geek_house.api_1_0 import api
from flask import g, current_app, jsonify, request, session
from geek_house.conf.response_code import RET
from geek_house.models.models import GeekHouseInfo, GeekHouseFacilityInfo, GeekHouseImage, GeekHouseOrder, \
    GeekHouseFacility, GeekHouseFavorite, GeekHouseUser
from geek_house import db, redis_store
from geek_house.conf import constants
from geek_house.utils.login_required import login_required
from geek_house.utils.image_storage import storage
from datetime import datetime
import json


@api.route("/houses/favorite", methods=["POST"])
@login_required
def set_house_favorite():
    user_id = g.user_id
    house_data = request.get_json()
    house_id = house_data.get("house_id")
    favorite = house_data.get("favorite")
    user = GeekHouseUser.query.get(user_id)
    if favorite:
        user.favorites.append((GeekHouseInfo.query.get(house_id)))
    else:
        user.favorites.remove((GeekHouseInfo.query.get(house_id)))
    db.session.commit()

    house = GeekHouseInfo.query.get(house_id)
    house_data = house.to_full_dict()
    if not house_data.get("img_urls"):
        house_data["img_urls"] = ['http://rd52d6n5l.hd-bkt.clouddn.com/no_picture']
    if GeekHouseInfo.query.get(house_id) in user.favorites:
        house_data["favorite"] = 1
    else:
        house_data["favorite"] = 0
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)
    return jsonify(code=RET.OK, data={"house": house_data})


@api.route("/houses/favorite/<int:house_id>", methods=["GET"])
@login_required
def get_house_favorite(house_id):
    user_id = session.get("user_id", "-1")
    user = GeekHouseUser.query.get(user_id)
    if GeekHouseInfo.query.get(house_id) in user.favorites:
        return jsonify(code=RET.OK, data={"favorite": True})
    return jsonify(code=RET.OK, data={"favorite": False, "len": len(user.favorites)})


@api.route("/user/favorite", methods=["GET"])
@login_required
def get_house_favorite_list():
    user_id = g.user_id
    user = GeekHouseUser.query.get(user_id)
    houses = user.favorites

    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(code=RET.OK, msg="OK", data={"houses": houses_list})


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """保存房屋的基本信息
    前端发送过来的json数据
    {
        "title":"",
        "price":"",
        "aname":"",
        "address":"",
        "room_count":"",
        "acreage":"",
        "unit":"",
        "capacity":"",
        "beds":"",
        "deposit":"",
        "min_days":"",
        "max_days":"",
        "facility":["7","8"]
    }
    """
    # 获取数据
    user_id = g.user_id
    house_data = request.get_json()

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    aname = house_data.get("aname")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    aname_list = aname.split("-")
    if not aname_list[2]:
        return jsonify(code=RET.PARAMERR, msg="三级地址未选择完成")

    # 校验参数
    if not all(
            [title, price, aname, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(code=RET.PARAMERR, msg="参数不完整")

    address = aname.replace("-", "") + address

    # 判断金额是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.PARAMERR, msg="参数错误")

    # 保存房屋信息
    house = GeekHouseInfo(
        user_id=user_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 处理房屋的设施信息
    facility_ids = house_data.get("facility")

    # 如果用户勾选了设施信息，再保存数据库
    if facility_ids:
        # ["7","8"]
        try:
            # select  * from ih_facility_info where id in []
            facilities = GeekHouseFacilityInfo.query.filter(GeekHouseFacilityInfo.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.DBERR, msg="数据库异常")

        if facilities:
            # 表示有合法的设施数据
            # 保存设施数据
            house.facilities = facilities

    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(code=RET.DBERR, msg="保存数据失败")

    # 保存数据成功
    return jsonify(code=RET.OK, msg="OK", data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """
    保存房屋的图片
    参数 图片 房屋的id
    """

    house_id = request.form.get("house_id")
    house_image = request.files.get("house_image")

    if not all([house_image, house_id]):
        return jsonify(code=RET.PARAMERR, msg="参数错误")

    image_file_dict = ImmutableMultiDict(request.files).lists()
    image_file_list = []
    for house_image in image_file_dict:
        image_file_list = house_image[1]

    data = []
    for image_file in image_file_list:
        # 判断house_id正确性
        try:
            house = GeekHouseInfo.query.get(house_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.DBERR, msg="数据库异常")

        if house is None:  # if not house:
            return jsonify(code=RET.NODATA, msg="房屋不存在")

        image_data = image_file.read()
        # 保存图片到七牛中
        try:
            file_name = storage(image_data)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.THIRDERR, msg="保存图片失败")

        # 保存图片信息到数据库中
        house_image = GeekHouseImage(house_id=house_id, url=file_name)
        db.session.add(house_image)

        # 处理房屋的主图片
        if not house.index_image_url or house.index_image_url == "no_picture":
            house.index_image_url = file_name
            db.session.add(house)

        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return jsonify(code=RET.DBERR, msg="保存图片数据异常")

        image_url = constants.QINIU_URL_DOMAIN + file_name
        data.append(image_url)

    return jsonify(code=RET.OK, msg="OK", data=data)


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    """获取房东发布的房源信息条目"""
    user_id = g.user_id

    try:
        houses = GeekHouseInfo.query.filter(GeekHouseInfo.user_id == user_id).order_by(
            GeekHouseInfo.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="获取数据失败")

    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(code=RET.OK, msg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋基本信息"""
    # 从缓存中尝试获取数据
    try:
        ret = redis_store.get("house_index_data")
    except Exception as e:
        current_app.logger.error(e)
        ret = None

    if ret:
        current_app.logger.info("hit house index info redis")
        # 因为redis中保存的是json字符串，所以直接进行字符串拼接返回
        return jsonify(code=RET.OK, msg="OK", data=json.loads(ret))
    else:
        try:
            # 查询数据库，返回房屋订单数目最多的5条数据
            houses = GeekHouseInfo.query.order_by(GeekHouseInfo.create_time).limit(constants.HOME_PAGE_MAX_HOUSES)
            # houses = GeekHouseInfo.query.order_by(GeekHouseInfo.create_time.desc()).limit(
            #     constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(code=RET.DBERR, msg="查询数据失败")

        if not houses:
            return jsonify(code=RET.NODATA, msg="查询无数据")

        houses_list = []
        for house in houses:
            # 如果房屋未设置主图片，则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json，并保存到redis缓存
        json_houses = json.dumps(houses_list)  # "[{},{},{}]"
        try:
            redis_store.setex("house_index_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(code=RET.OK, msg="OK", data=json.loads(json_houses))


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", 0)

    # 校验参数
    if not house_id:
        return jsonify(code=RET.PARAMERR, msg="参数确实")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        ret = None
    if ret:
        current_app.logger.info("hit house info redis")
        return jsonify(code=RET.OK, msg="OK", data={"user_id": user_id, "house": json.loads(ret)})

    # 查询数据库
    try:
        house = GeekHouseInfo.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="查询数据失败")

    if not house:
        return jsonify(code=RET.NODATA, msg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
        if not house_data.get("img_urls"):
            house_data["img_urls"] = ['http://rd52d6n5l.hd-bkt.clouddn.com/no_picture']
        if user_id:
            user = GeekHouseUser.query.get(user_id)
            if house in user.favorites:
                house_data["favorite"] = 1
            else:
                house_data["favorite"] = 0
        else:
            house_data["favorite"] = 0
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DATAERR, msg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        current_app.logger.error(e)

    return jsonify(code=RET.OK, msg="OK", data={"user_id": user_id, "house": json.loads(json_house)})


# GET /api/v1.0/houses?sd=2022-02-01&ed=2022-02-31&aid=10&sk=new&p=1
@api.route("/houses")
def get_house_list():
    """获取房屋的列表信息（搜索页面）"""
    start_date = request.args.get("sd", "")  # 用户想要的起始时间
    aname = request.args.get("aname", "")  # 用户想要的起始时间
    end_date = request.args.get("ed", "")  # 用户想要的结束时间
    sort_key = request.args.get("sk", "new")  # 排序关键字
    page = request.args.get("p")  # 页数

    # 处理时间
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.PARAMERR, msg="日期参数有误")

    # 处理页数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 获取缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, aname, sort_key)

    aname_str = aname.replace("-", "", 2)
    aname_list = aname_str.split("-")
    aname = aname_list[0]
    detail_aname = aname_list[1] if len(aname_list) > 1 else ""

    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json:
            return jsonify(json.loads(resp_json))

    # 过滤条件的参数列表容器
    filter_params = []

    # 填充过滤参数
    # 时间条件
    conflict_orders = None

    try:
        if start_date and end_date:
            # 查询冲突的订单
            conflict_orders = GeekHouseOrder.query.filter(GeekHouseOrder.begin_date <= end_date,
                                                          GeekHouseOrder.end_date >= start_date).all()
        elif start_date:
            conflict_orders = GeekHouseOrder.query.filter(GeekHouseOrder.end_date >= start_date).all()
        elif end_date:
            conflict_orders = GeekHouseOrder.query.filter(GeekHouseOrder.begin_date <= end_date).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="数据库异常")

    if conflict_orders:
        # 从订单中获取冲突的房屋id
        conflict_house_ids = [order.house_id for order in conflict_orders]

        # 如果冲突的房屋id不为空，向查询参数中添加条件
        if conflict_house_ids:
            filter_params.append(GeekHouseInfo.id.notin_(conflict_house_ids))

    filter_params.append(GeekHouseInfo.address.like("%" + aname + "%" + detail_aname + "%"))

    # 查询数据库
    # 补充排序条件
    if sort_key == "booking":  # 入住做多
        house_query = GeekHouseInfo.query.filter(*filter_params).order_by(GeekHouseInfo.order_count.desc())
    elif sort_key == "price-inc":
        house_query = GeekHouseInfo.query.filter(*filter_params).order_by(GeekHouseInfo.price.asc())
    elif sort_key == "price-des":
        house_query = GeekHouseInfo.query.filter(*filter_params).order_by(GeekHouseInfo.price.desc())
    else:  # 新旧
        house_query = GeekHouseInfo.query.filter(*filter_params).order_by(GeekHouseInfo.create_time.desc())

    # 处理分页
    try:
        #                               当前页数          每页数据量                              自动的错误输出
        page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(code=RET.DBERR, msg="数据库异常")

    # 获取页面数据
    house_li = page_obj.items
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 获取总页数
    total_page = page_obj.pages

    resp_dict = dict(code=RET.OK, msg="OK", data={"total_page": total_page, "houses": houses, "current_page": page})
    resp_json = json.dumps(resp_dict)

    if page <= total_page:
        # 设置缓存数据
        redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, aname, sort_key)
        # 哈希类型
        try:
            # redis_store.hset(redis_key, page, resp_json)
            # redis_store.expire(redis_key, constants.HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES)

            # 创建redis管道对象，可以一次执行多个语句
            pipeline = redis_store.pipeline()

            # 开启多个语句的记录
            pipeline.multi()

            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES)

            # 执行语句
            pipeline.execute()
        except Exception as e:
            current_app.logger.error(e)

    return jsonify(json.loads(resp_json))

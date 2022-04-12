function hrefBack() {
    history.go(-1);
}

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

// 解析提取url中的查询字符串参数
function decodeQuery() {
    var search = decodeURI(document.location.search);
    return search.replace(/(^\?)/, '').split('&').reduce(function (result, item) {
        values = item.split('=');
        result[values[0]] = values[1];
        return result;
    }, {});
}

$(document).ready(function () {
    // 获取详情页面要展示的房屋编号
    var queryData = decodeQuery();
    var houseId = queryData["id"];

    // 获取该房屋的详细信息
    $.get("/api/v1.0/houses/" + houseId, function (resp) {
        if ("0" == resp.code) {
            $(".swiper-container").html(template("house-image-tmpl", {
                img_urls: resp.data.house.img_urls,
                price: resp.data.house.price
            }));
            $(".detail-con").html(template("house-detail-tmpl", {house: resp.data.house}));

            // resp.user_id为访问页面用户,resp.data.user_id为房东
            if (resp.data.user_id != resp.data.house.user_id) {
                $(".book-house").attr("href", "/booking.html?hid=" + resp.data.house.hid);
                $(".book-house").show();
            }
            var mySwiper = new Swiper('.swiper-container', {
                loop: true,
                autoplay: 2000,
                autoplayDisableOnInteraction: false,
                pagination: '.swiper-pagination',
                paginationType: 'fraction'
            });
        }
    });
});

//点击收藏按钮触发的方法
function addFavorite() {
    var queryData = decodeQuery();
    var house_id = queryData["id"];
    // 处理表单数据
    var data = {};
    data.favorite = true;
    data.house_id = house_id;
    // 向后端发送请求
    $.ajax({
        url: "/api/v1.0/houses/favorite",
        type: "post",
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType: "json",
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        success: function (resp) {
            if (resp.code == "4101") {
                // 用户未登录
                location.href = "/login.html";
            } else if (resp.code == "0") {
                $(".swiper-container").html(template("house-image-tmpl", {
                    img_urls: resp.data.house.img_urls,
                    price: resp.data.house.price
                }));
                $(".detail-con").html(template("house-detail-tmpl", {house: resp.data.house}));

                // resp.user_id为访问页面用户,resp.data.user_id为房东
                if (resp.data.user_id != resp.data.house.user_id) {
                    $(".book-house").attr("href", "/booking.html?hid=" + resp.data.house.hid);
                    $(".book-house").show();
                }
                var mySwiper = new Swiper('.swiper-container', {
                    loop: true,
                    autoplay: 2000,
                    autoplayDisableOnInteraction: false,
                    pagination: '.swiper-pagination',
                    paginationType: 'fraction'
                });
            }
        }
    });
}

function removeFavorite() {
    var queryData = decodeQuery();
    var house_id = queryData["id"];
    // 处理表单数据
    var data = {};
    data.favorite = false;
    data.house_id = house_id;
    // 向后端发送请求
    $.ajax({
        url: "/api/v1.0/houses/favorite",
        type: "post",
        contentType: "application/json",
        data: JSON.stringify(data),
        dataType: "json",
        headers: {
            "X-CSRFToken": getCookie("csrf_token")
        },
        success: function (resp) {
            if (resp.code == "4101") {
                // 用户未登录
                location.href = "/login.html";
            } else if (resp.code == "0") {
                $(".swiper-container").html(template("house-image-tmpl", {
                    img_urls: resp.data.house.img_urls,
                    price: resp.data.house.price
                }));
                $(".detail-con").html(template("house-detail-tmpl", {house: resp.data.house}));

                // resp.user_id为访问页面用户,resp.data.user_id为房东
                if (resp.data.user_id != resp.data.house.user_id) {
                    $(".book-house").attr("href", "/booking.html?hid=" + resp.data.house.hid);
                    $(".book-house").show();
                }
                var mySwiper = new Swiper('.swiper-container', {
                    loop: true,
                    autoplay: 2000,
                    autoplayDisableOnInteraction: false,
                    pagination: '.swiper-pagination',
                    paginationType: 'fraction'
                });
            }
        }
    });
}
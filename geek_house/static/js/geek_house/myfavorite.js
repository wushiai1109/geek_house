$(document).ready(function () {
    $.get("/api/v1.0/users/auth", function (resp) {
        if ("4101" == resp.code) {
            // 用户未登录
            location.href = "/login.html";
        } else if ("0" == resp.code) {
            $.get("/api/v1.0/user/favorite", function (resp) {
                if ("0" == resp.code) {
                    $("#houses-list").html(template("houses-list-tmpl", {houses: resp.data.houses}));
                } else {
                    $("#houses-list").html(template("houses-list-tmpl", {houses: []}));
                }
            });
        }
    });
})
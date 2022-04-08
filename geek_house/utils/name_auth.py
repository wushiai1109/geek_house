# -*- coding: utf-8 -*-
from __future__ import print_function

import base64
import hashlib
import hmac
import json
import ssl
from datetime import datetime

try:
    from urllib import urlencode
    from urllib2 import Request, urlopen
except ImportError:
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen


def name_auth(name, idcard):
    # 云市场分配的密钥Id
    secretId = "AKIDAVbajjzwz7H790tadwscbk5o5x97wy40iuq"
    # 云市场分配的密钥Key
    secretKey = "8saw02j1Lhc94hr1vlO027ZB2vgpx5ANRloc2RG"
    source = "market"

    # 签名
    time = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    signStr = "x-date: %s\nx-source: %s" % (time, source)
    sign = base64.b64encode(hmac.new(secretKey.encode('utf-8'), signStr.encode('utf-8'), hashlib.sha1).digest())
    auth = 'hmac id="%s", algorithm="hmac-sha1", headers="x-date x-source", signature="%s"' % (
        secretId, sign.decode('utf-8'))

    # 请求方法
    method = 'GET'
    # 请求头
    headers = {
        'X-Source': source,
        'X-Date': time,
        'Authorization': auth,
    }
    # 查询参数
    queryParams = {
        "idcard": idcard,
        "name": name}
    # body参数（POST方法下存在）
    bodyParams = {
    }
    # url参数拼接
    url = 'https://service-ig2xnu0f-1255468759.ap-shanghai.apigateway.myqcloud.com/release/idcard'
    if len(queryParams.keys()) > 0:
        url = url + '?' + urlencode(queryParams)

    try:
        request = Request(url, headers=headers)
        request.get_method = lambda: method
        if method in ('POST', 'PUT', 'PATCH'):
            request.data = urlencode(bodyParams).encode('utf-8')
            request.add_header('Content-Type', 'application/x-www-form-urlencoded')
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        response = urlopen(request, context=ctx)
        content = response.read()
        content = content.decode('utf-8')
        content = content.replace(" ", "")
        content = content.replace("\n", "")
        if content:
            content = json.dumps(content)
            content = json.loads(content)
            showapi_res_body = json.loads(content)["showapi_res_body"]
            showapi_res_body = json.dumps(showapi_res_body)
            showapi_res_body = json.loads(showapi_res_body)
            return showapi_res_body["ret_code"]
    except Exception as e:
        return -1

# if __name__ == "__main__":
#     res = name_auth("", "")
#     print(res)

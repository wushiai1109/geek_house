from ronglian_sms_sdk import SmsSDK
import json

# accId = '容联云通讯分配的主账号ID'
accId = '8aaf0708780055cd0178ac5c70ca3ff2'
# accToken = '容联云通讯分配的主账号TOKEN'
accToken = '8041e928499d47fe8008c58861b4ad21'
# appId = '容联云通讯分配的应用ID'
appId = '8aaf0708780055cd0178ac5c71d93ff9'


# demo
def send_message1():
    sdk = SmsSDK(accId, accToken, appId)
    # tid = '容联云通讯创建的模板'
    tid = '1'
    # mobile = '手机号1,手机号2'
    mobile = '18723746541'
    # datas = ('变量1', '变量2')
    datas = ('9989', '5')
    resp = sdk.sendMessage(tid, mobile, datas)
    print(resp)


# send_message()


# 单例模式
class SendMessageUtil(object):
    """自己封装的发送短信的辅助类"""
    # 用来保存对象的类属性
    instance = None

    def __new__(cls):
        if cls.instance is None:
            obj = super(SendMessageUtil, cls).__new__(cls)
            # 初始化SDK
            obj.sdk = SmsSDK(accId, accToken, appId)
            cls.instance = obj
        return cls.instance

    def send_message(self, tid, mobile, datas):
        result = self.sdk.sendMessage(tid, mobile, datas)
        status_code = json.loads(result).get("statusCode")
        # if status_code == "000000" or status_code == "112310":  # 测试可用
        if status_code == "000000":
            # 表示发送短信成功
            return 0
        else:
            # 发送失败
            return -1

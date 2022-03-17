from ronglian_sms_sdk import SmsSDK

# accId = '容联云通讯分配的主账号ID'
accId = '8aaf0708780055cd0178ac5c70ca3ff2'
# accToken = '容联云通讯分配的主账号TOKEN'
accToken = '8041e928499d47fe8008c58861b4ad21'
# appId = '容联云通讯分配的应用ID'
appId = '8aaf0708780055cd0178ac5c71d93ff9'


# demo
def send_message():
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
if __name__ == '__main__':
    send_message()

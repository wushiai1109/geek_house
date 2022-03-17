# -*- coding=utf-8
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging

# 正常情况日志级别使用INFO，需要定位时可以修改为DEBUG，此时SDK会打印和服务端的通信信息
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# 1. 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在CosConfig中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
secret_id = 'AKIDXu1rTpukKehTxB8oDLCm57sLXS7VbQzH'  # 替换为用户的 SecretId，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
secret_key = '4rNcaGfneEXZKnzuXtymJYWDdmeFYbQy'  # 替换为用户的 SecretKey，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
region = 'ap-chongqing'  # 替换为用户的 region，已创建桶归属的region可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
# COS支持的所有region列表参见https://cloud.tencent.com/document/product/436/6224
token = None  # 如果使用永久密钥不需要填入token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见https://cloud.tencent.com/document/product/436/14048
scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
client = CosS3Client(config)

#### 文件流简单上传（不支持超过5G的文件，推荐使用下方高级上传接口）
# 强烈建议您以二进制模式(binary mode)打开文件,否则可能会导致错误
# with open('1.png', 'rb') as fp:
#     response = client.put_object(
#         Bucket='geek-home-1259745853',
#         Body=fp,
#         Key='1.png',
#         StorageClass='STANDARD',
#         EnableMD5=False
#     )
# print(response['ETag'])

#### 字节流简单上传
# response = client.put_object(
#     Bucket='geek-home-1259745853',
#     Body=b'bytes',
#     Key='1.png',
#     EnableMD5=False
# )
# print(response['ETag'])


#### chunk 简单上传
# import requests
# stream = requests.get('https://cloud.tencent.com/document/product/436/7778')
#
# # 网络流将以 Transfer-Encoding:chunked 的方式传输到 COS
# response = client.put_object(
#     Bucket='geek-home-1259745853',
#     Body=stream,
#     Key='1.png'
# )
# print(response['ETag'])

#### 高级上传接口（推荐）
# 根据文件大小自动选择简单上传或分块上传，分块上传具备断点续传功能。
response = client.upload_file(
    Bucket='geek-home-1259745853',
    LocalFilePath='1.png',
    Key='1.png',
    PartSize=1,
    MAXThread=10,
    EnableMD5=False
)
print(response['ETag'])

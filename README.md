需要申请一个网址，可以使用cpolar内网穿透，把端口号设置成main方法中的端口号就行

[SD下载链接]()（近期内上传）

[controlNet下载链接](https://pan.baidu.com/s/1ww_jkK9BAGKAxjBYcVaKRQ?pwd=rajn)

需要注册一个azure的账户，[链接](https://learn.microsoft.com/zh-cn/azure/storage/blobs/storage-quickstart-blobs-portal)

myaccount：你的Azure存储帐户的名称

AccountKey：与你的Azure存储帐户关联的密钥。

EndpointSuffix：Azure存储的服务域名后缀。通常为core.windows.net。

{

AZURE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=myaccountkey==;EndpointSuffix=core.windows.net
"

AZURE_CONTAINER_NAME = "自己设置的容器名称"

}

创建环境
conda create --name SDweb python

安装执行环境
pip install -r requirements.txt

pycharm运行即可

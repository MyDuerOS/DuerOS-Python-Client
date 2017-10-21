# DuerOS-Python-Client使用说明
## 运行依赖
* gstreamer1.0
* gstreamer1.0-plugins-good
* gstreamer1.0-plugins-ugly
* python-gi
* python-gst
* gir1.2-gstreamer-1.0
## 测试环境
* Ubuntu 16.04
* Python 2.7.12
## 使用说明
### 项目获取
通过git下载代码到本地

    # git clone https://github.com/MyDuerOS/DuerOS-Python-Client.git

### 认证授权
在DuerOS-Python-Client目录下执行
 
    # ./auth.sh

### 通过[Enter]键触发唤醒状态
在DuerOS-Python-Client目录下执行

    # ./enter_trigger_start.sh

然后，每次单击[Enter]键后进行语音输入
### 通过[小度小度]触发唤醒状态
在DuerOS-Python-Client目录下执行(暂时该功能还不支持)

    # ./wakeup_trigger_start.sh
然后，每次通过[小度小度]进行唤醒，然后，进行语音输入

 
## 代码结构

DuerOS-Python-Client代码结构如下图所示，

![代码结构](./readme_resources/代码结构.png)

其中，

*DuerOS-Python-Client:项目根目录*

* DuerOS-Python-Client/auth.sh:认证授权脚本
* DuerOS-Python-Client/enter_trigger_start.sh:[Enter]按键触发唤醒脚本
* DuerOS-Python-Client/wakeup_tirgger_start.sh:[小度小度]触发唤醒脚本

*DuerOS-Python-Client/app:应用目录*

* DuerOS-Python-Client/app/auth.py:认证授权实现模块
* DuerOS-Python-Client/app/enter_trigger_main.py:[Enter]按键触发唤醒实现模块
* DuerOS-Python-Client/app/wakeup_tirgger_main.py:[小度小度]触发唤醒实现模块
* DuerOS-Python-Client/app/framework:平台相关目录
* DuerOS-Python-Client/app/framework/mic.py:录音模块(基于pyaudio)
* DuerOS-Python-Client/app/framework/player.py:播放模块(基于GStreamer)
* DuerOS-Python-Client/app/snowboy:snowboy唤醒引擎

*DuerOS-Python-Client/sdk:dueros sdk目录*

* DuerOS-Python-Client/sdk/auth.py:授权相关实现
* DuerOS-Python-Client/sdk/dueros_core.py:dueros交互实现
* DuerOS-Python-Client/sdk/interface:端能力接口实现

## SDK接口说明
### 授权模块(sdk/auth)
#### 授权接口
用户通过授权接口完成基于OAuth2.0的认证授权流程

    def auth_request(client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
    '''
    发起认证
    :param client_id:开发者注册信息
    :param client_secret: 开发者注册信息
    :return:
    '''

### DuerOS核心模块(sdk/dueros_core)
#### directive监听注册
通过监听注册接口，用户可以获得云端下发的directive内容

        def set_directive_listener(self, listener):
        '''
        directive监听器设置
        :param listener: directive监听器
        :return:
        '''

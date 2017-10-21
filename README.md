DuerOS Python 版本客户端(app+sdk)，使用百度的DCS服务
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

## 认证授权
        # ./auth.sh
## 按键[Enter]触发运行
        # ./enter_trigger_start.sh       
## 唤醒词[小度小度]触发运行
        ＃ ./wakeup_trigger_start.sh

## 唤醒模型更新
更换app/snowboy/xiaoduxiaodu.pmdl文件(当前的唤醒模型因为训练样板较少，唤醒率较低)

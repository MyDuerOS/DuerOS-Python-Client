# -*- coding: utf-8 -*-

"""
通过[小度小度]触发进入唤醒状态

"""
import threading
import time

try:
    import Queue as queue
except ImportError:
    import queueg

import logging
import app.app_config as app_config

from sdk.dueros_core import DuerOS
from app.framework.player import Player
from app.framework.mic import Audio
from app.snowboy import snowboydecoder
from app.utils.prompt_tone import PromptTone

logging.basicConfig(level=app_config.LOGGER_LEVEL)


class SnowBoy(object):
    '''
    基于SnowBoy的唤醒类
    '''

    def __init__(self, model):
        '''
        SnowBoy初始化
        :param model:唤醒词训练模型
        '''
        self.calback = None
        self.detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5, audio_gain=1)

    def feed_data(self, data):
        '''
        唤醒引擎语音数据输入
        :param data: 录音pcm数据流
        :return:
        '''
        self.detector.feed_data(data)

    def set_callback(self, callback):
        '''
        唤醒状态回调
        :param callback:唤醒状态回调函数
        :return:
        '''
        if not callable(callback):
            raise ValueError('注册回调失败[参数不可调用]！')

        self.calback = callback

    def start(self):
        '''
        唤醒引擎启动
        :return:
        '''
        thread = threading.Thread(target=self.__run)
        thread.daemon = True
        thread.start()

    def stop(self):
        '''
        唤醒引擎关闭
        :return:
        '''
        self.detector.terminate()

    def __run(self):
        '''
        唤醒检测线程实体
        :return:
        '''
        self.detector.start(self.calback)


class WakeupEngine(object):
    '''
    唤醒引擎(平台无关)
    '''

    def __init__(self):
        self.queue = queue.Queue()

        self.sinks = []
        self.callback = None

        self.done = False

    def set_wakeup_detector(self, detector):
        '''
        设置唤醒引擎
        :param detector:唤醒引擎（如SnowBoy）
        :return:
        '''
        if hasattr(detector, 'feed_data') and callable(detector.feed_data):
            self.wakeup_detector = detector
        else:
            raise ValueError('唤醒引擎设置失败[不存在可调用的feed_data方法]！')

    def put(self, data):
        '''
        录音数据缓存
        :param data:录音pcm流
        :return:
        '''
        self.queue.put(data)

    def start(self):
        '''
        唤醒引擎启动
        :return:
        '''
        self.done = False
        thread = threading.Thread(target=self.__run)
        thread.daemon = True
        thread.start()

    def stop(self):
        '''
        唤醒引擎关闭
        :return:
        '''
        self.done = True

    def link(self, sink):
        '''
        连接DuerOS核心实现模块
        :param sink:DuerOS核心实现模块
        :return:
        '''
        if hasattr(sink, 'put') and callable(sink.put):
            self.sinks.append(sink)
        else:
            raise ValueError('link注册对象无put方法')

    def unlink(self, sink):
        '''
        移除DuerOS核心实现模块
        :param sink: DuerOS核心实现模块
        :return:
        '''
        self.sinks.remove(sink)

    def __run(self):
        '''
        唤醒引擎线程实体
        :return:
        '''
        while not self.done:
            chunk = self.queue.get()
            self.wakeup_detector.feed_data(chunk)

            for sink in self.sinks:
                sink.put(chunk)


def directive_listener(directive_content):
    '''
    云端下发directive监听器
    :param directive_content:云端下发directive内容
    :return:
    '''
    content = u'云端下发directive:%s' % (directive_content)
    logging.info(content)


def main():
    # 创建录音设备(平台相关)
    audio = Audio()
    # 创建唤醒引擎
    wakeup_engine = WakeupEngine()
    # 创建播放器(平台相关)
    player = Player()
    # 创建duerOS核心处理模块
    dueros = DuerOS(player)
    dueros.set_directive_listener(directive_listener)

    # [小度小度] SnowBoy唤醒引擎
    model = 'app/snowboy/xiaoduxiaodu_all_10022017.umdl'
    # SnowBoy唤醒引擎实体
    snowboy = SnowBoy(model)

    audio.link(wakeup_engine)
    wakeup_engine.link(dueros)
    wakeup_engine.set_wakeup_detector(snowboy)

    prompt_tone_player = PromptTone()

    def wakeup():
        '''
        唤醒回调
        :return:
        '''
        print '[小度]已唤醒,我能为你做些什么..........'
        # 唤醒态提示音
        prompt_tone_player.play()
        dueros.listen()

    snowboy.set_callback(wakeup)

    dueros.start()
    wakeup_engine.start()
    snowboy.start()
    audio.start()

    print '请说[小度小度]来唤醒我.......'

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    dueros.stop()
    wakeup_engine.stop()
    audio.stop()
    snowboy.stop()


if __name__ == '__main__':
    main()

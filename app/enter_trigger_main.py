# -*- coding: utf-8 -*-
'''
通过输入[Enter]触发唤醒状态
'''
import logging
from sdk.dueros_core import DuerOS

from framework.mic import Audio
from framework.player import Player

logging.basicConfig(level=logging.DEBUG)


def directive_listener(directive_content):
    '''
    云端下发directive监听器
    :param directive_content:云端下发directive内容
    :return:
    '''
    logging.info('*******directive content start*******')
    logging.info(directive_content)
    logging.info('*******directive content end*********')


class DuerOSStateListner(object):
    '''
    DuerOS状态监听类
    '''

    def __init__(self):
        pass

    def on_listening(self):
        '''
        监听状态回调
        :return:
        '''
        logging.info('[DuerOS状态]正在倾听..........')

    def on_thinking(self):
        '''
        语义理解状态回调
        :return:
        '''
        logging.info('[DuerOS状态]正在思考.........')

    def on_speaking(self):
        '''
        播放状态回调
        :return:
        '''
        logging.info('[DuerOS状态]正在播放........')

    def on_finished(self):
        '''
        处理结束状态回调
        :return:
        '''
        logging.info('[DuerOS状态]结束')


def main():
    # 创建录音设备（平台相关）
    audio = Audio()
    # 创建播放器（平台相关）
    player = Player()

    dueros = DuerOS(player)
    dueros.set_directive_listener(directive_listener)
    dueros_status_listener = DuerOSStateListner()
    dueros.set_state_listner(dueros_status_listener)

    audio.link(dueros)

    dueros.start()
    audio.start()

    while True:
        try:
            try:
                print '\n'
                input('单击[Enter]建，然后发起对话\n')
            except SyntaxError:
                pass

            dueros.listen()
        except KeyboardInterrupt:
            break

    dueros.stop()
    audio.stop()


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
'''
通过输入[Enter]触发唤醒状态
'''
from sdk.dueros_core import DuerOS

from framework.mic import Audio
from framework.player import Player


def directive_listener(directive_content):
    '''
    云端下发directive监听器
    :param directive_content:云端下发directive内容
    :return:
    '''
    print '*******directive content start*******'
    print directive_content
    print '*******directive content end*********'


def main():
    # 创建录音设备（平台相关）
    audio = Audio()
    # 创建播放器（平台相关）
    player = Player()

    dueros = DuerOS(player)
    dueros.register_directive_callback(directive_listener)

    audio.link(dueros)

    dueros.start()
    audio.start()

    while True:
        try:
            try:
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

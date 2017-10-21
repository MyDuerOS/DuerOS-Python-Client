# -*- coding: utf-8 -*-
'''
通过输入[Enter]触发唤醒状态
'''
import logging
from sdk.dueros_core import DuerOS

from app.framework.mic import Audio
from app.framework.player import Player
from app.utils.prompt_tone import PromptTone

logging.basicConfig(level=logging.INFO)


def directive_listener(directive_content):
    '''
    云端下发directive监听器
    :param directive_content:云端下发directive内容
    :return:
    '''
    content = u'云端下发directive:%s' % (directive_content)
    logging.info(content)


def main():
    # 创建录音设备（平台相关）
    audio = Audio()
    # 创建播放器（平台相关）
    player = Player()

    dueros = DuerOS(player)
    dueros.set_directive_listener(directive_listener)

    audio.link(dueros)

    dueros.start()
    audio.start()

    prompt_tone_player = PromptTone()

    while True:
        try:
            try:
                print '\n'
                input('单击[Enter]建，然后发起对话\n')
            except SyntaxError:
                pass
            # 唤醒态提示音
            prompt_tone_player.play()
            dueros.listen()
        except KeyboardInterrupt:
            break

    dueros.stop()
    audio.stop()


if __name__ == '__main__':
    main()

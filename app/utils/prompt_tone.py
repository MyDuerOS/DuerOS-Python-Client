# -*- coding: utf-8 -*-
import os
from app.framework.player import Player


class PromptTone(object):
    '''
    提示音播放类(用于唤醒态提示)
    '''

    def __init__(self):
        self.player = Player()
        resource = os.path.realpath(os.path.join(os.path.dirname(__file__), '../resources/du.mp3'))
        self.resource_uri = 'file://{}'.format(resource)

    def play(self):
        '''
        提示音播放
        :return:
        '''
        self.player.play(self.resource_uri)

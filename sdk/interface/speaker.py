# -*- coding: utf-8 -*-
'''
扬声器控制模块
参考：http://open.duer.baidu.com/doc/dueros-conversational-service/device-interface/speaker-controller_markdown
'''


class Speaker(object):
    '''
    扬声器控制类
    '''

    def __init__(self, event_queue):
        '''
        类初始化
        :param event_queue:
        '''
        self.namespace = 'ai.dueros.device_interface.speaker_controller'

    def set_volume(self):
        '''
        音量设置(云端directive　name方法)
        :return:
        '''
        pass

    def adjust_volume(self):
        '''
        音量调整(云端directive　name方法)
        :return:
        '''
        pass

    def set_mute(self):
        '''
        设置静音(云端directive　name方法)
        :return:
        '''
        pass

    def __volume_changed(self):
        '''
        音量改变事件上报
        :return:
        '''
        pass

    def __mute_changed(self):
        '''
        静音状态改变事件上报
        :return:
        '''
        pass

    @property
    def context(self):
        '''
        获取模块上下文(模块状态)
        :return:
        '''
        return {
            "header": {
                "namespace": self.namespace,
                "name": "VolumeState"
            },
            "payload": {
                "volume": 50,
                "muted": False
            }
        }

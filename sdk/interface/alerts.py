# -*- coding: utf-8 -*-

"""
Alert模块
参考：http://open.duer.baidu.com/doc/dueros-conversational-service/device-interface/alerts_markdown
"""

import os
import datetime
import dateutil.parser
from threading import Timer
import uuid


class Alerts(object):
    '''
    Alert类
    '''
    STATES = {'IDLE', 'FOREGROUND', 'BACKGROUND'}

    def __init__(self, dueros, player):
        '''
        类初始化
        :param dueros:DuerOS核心处理模块
        :param player: 播放器
        '''
        self.namespace = 'ai.dueros.device_interface.alerts'
        self.dueros = dueros
        self.player = player

        self.player.add_callback('eos', self.stop)
        self.player.add_callback('error', self.stop)

        alarm = os.path.realpath(os.path.join(os.path.dirname(__file__), '../resources/alarm.wav'))
        self.alarm_uri = 'file://{}'.format(alarm)

        self.all_alerts = {}
        self.active_alerts = {}

    def stop(self):
        """
        停止所有激活的Alert
        """
        for token in self.active_alerts.keys():
            self.__alert_stopped(token)

        self.active_alerts = {}

    def set_alert(self, directive):
        '''
        设置闹钟(云端directive　name方法)
        :param directive:云端下发的directive
        :return:
        '''
        payload = directive['payload']
        token = payload['token']
        scheduled_time = dateutil.parser.parse(payload['scheduledTime'])

        # Update the alert
        if token in self.all_alerts:
            pass

        self.all_alerts[token] = payload

        interval = scheduled_time - datetime.datetime.now(scheduled_time.tzinfo)
        Timer(interval.seconds, self.__start_alert, (token,)).start()

        self.__set_alert_succeeded(token)

    def delete_alert(self, directive):
        '''
        删除闹钟(云端directive　name方法)
        :param directive: 云端下发的directive
        :return:
        '''
        token = directive['payload']['token']

        if token in self.active_alerts:
            self.__alert_stopped(token)

        if token in self.all_alerts:
            del self.all_alerts[token]

        self.__delete_alert_succeeded(token)

    def __start_alert(self, token):
        '''
        开始响铃
        :param self:
        :param token:
        :return:
        '''
        if token in self.all_alerts:
            self.__alert_started(token)

            # TODO: repeat play alarm until user stops it or timeout
            self.player.play(self.alarm_uri)

            # {
            #     "directive": {
            #         "header": {
            #             "namespace": "Alerts",
            #             "name": "SetAlert",
            #             "messageId": "{{STRING}}",
            #             "dialogRequestId": "{{STRING}}"
            #         },
            #         "payload": {
            #             "token": "{{STRING}}",
            #             "type": "{{STRING}}",
            #             "scheduledTime": "2017-08-07T09:02:58+0000",
            #         }
            #     }
            # }

    def __set_alert_succeeded(self, token):
        '''
        闹铃设置成功事件上报
        :param token:
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "SetAlertSucceeded",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.dueros.send_event(event)

    def __set_alert_failed(self, token):
        '''
        闹铃设置失败事件上报
        :param token:
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "SetAlertFailed",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.dueros.send_event(event)

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "Alerts",
    #             "name": "DeleteAlert",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "token": "{{STRING}}"
    #         }
    #     }
    # }

    def __delete_alert_succeeded(self, token):
        '''
        删除闹铃成功事件上报
        :param token:
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "DeleteAlertSucceeded",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.dueros.send_event(event)

    def __delete_alert_failed(self, token):
        '''
        删除闹铃失败事件上传
        :param token:
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "DeleteAlertFailed",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.dueros.send_event(event)

    def __alert_started(self, token):
        '''
        响铃开始事件上报
        :param token:
        :return:
        '''
        self.active_alerts[token] = self.all_alerts[token]

        event = {
            "header": {
                "namespace": self.namespace,
                "name": "AlertStarted",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.dueros.send_event(event)

    def __alert_stopped(self, token):
        '''
        响铃结束事件上报
        :param token:
        :return:
        '''
        if token in self.active_alerts:
            del self.active_alerts[token]

        if token in self.all_alerts:
            del self.all_alerts[token]

        event = {
            "header": {
                "namespace": self.namespace,
                "name": "AlertStopped",
                "messageId": "{STRING}"
            },
            "payload": {
                "token": token
            }
        }

        self.dueros.send_event(event)

    def __alert_entered_foreground(self, token):
        '''
        响铃进入前台事件上报
        :param token:
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "AlertEnteredForeground",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.dueros.send_event(event)

    def __alert_entered_background(self, token):
        '''
        响铃进入后台事件上报
        :param token:
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "AlertEnteredBackground",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": token
            }
        }

        self.dueros.send_event(event)

    @property
    def context(self):
        '''
        获取模块上下文(模块状态)
        :return:
        '''
        return {
            "header": {
                "namespace": self.namespace,
                "name": "AlertsState"
            },
            "payload": {
                "allAlerts": list(self.all_alerts.values()),
                "activeAlerts": list(self.active_alerts.values())
            }
        }

# -*- coding: utf-8 -*-

"""http://open.duer.baidu.com/doc/dueros-conversational-service/device-interface/alerts_markdown"""

import os
import datetime
import dateutil.parser
from threading import Timer
import uuid

from dueros.player import Player


class Alerts(object):
    STATES = {'IDLE', 'FOREGROUND', 'BACKGROUND'}

    def __init__(self, dueros):
        self.namespace='ai.dueros.device_interface.alerts'
        self.dueros = dueros
        self.player = Player()

        self.player.add_callback('eos', self.stop)
        self.player.add_callback('error', self.stop)

        alarm = os.path.realpath(os.path.join(os.path.dirname(__file__), '../resources/alarm.mp3'))
        self.alarm_uri = 'file://{}'.format(alarm)

        self.all_alerts = {}
        self.active_alerts = {}

    def stop(self):
        """
        Stop all active alerts
        """
        for token in self.active_alerts.keys():
            self.AlertStopped(token)

        self.active_alerts = {}

    def _start_alert(self, token):
        if token in self.all_alerts:
            self.AlertStarted(token)

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
    def SetAlert(self, directive):
        payload = directive['payload']
        token = payload['token']
        scheduled_time = dateutil.parser.parse(payload['scheduledTime'])

        # Update the alert
        if token in self.all_alerts:
            pass

        self.all_alerts[token] = payload

        interval = scheduled_time - datetime.datetime.now(scheduled_time.tzinfo)
        Timer(interval.seconds, self._start_alert, (token,)).start()

        self.SetAlertSucceeded(token)

    def SetAlertSucceeded(self, token):
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

    def SetAlertFailed(self, token):
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
    def DeleteAlert(self, directive):
        token = directive['payload']['token']

        if token in self.active_alerts:
            self.AlertStopped(token)

        if token in self.all_alerts:
            del self.all_alerts[token]

        self.DeleteAlertSucceeded(token)

    def DeleteAlertSucceeded(self, token):
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

    def DeleteAlertFailed(self, token):
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

    def AlertStarted(self, token):
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

    def AlertStopped(self, token):
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

    def AlertEnteredForeground(self, token):
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

    def AlertEnteredBackground(self, token):
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

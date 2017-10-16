import uuid
import datetime


class System(object):
    def __init__(self, dueros):
        self.namespace='ai.dueros.device_interface.system'
        self.dueros = dueros

    def SynchronizeState(self):
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "SynchronizeState",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
            }
        }

        self.dueros.send_event(event)

    def UserInactivityReport(self):
        inactive_time = datetime.datetime.utcnow() - self.dueros.last_activity

        event = {
            "header": {
                "namespace": self.namespace,
                "name": "UserInactivityReport",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "inactiveTimeInSeconds": inactive_time.seconds
            }

        }

        self.dueros.send_event(event)

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "System",
    #             "name": "ResetUserInactivity",
    #             "messageId": "{{STRING}}"
    #         },
    #         "payload": {
    #         }
    #     }
    # }
    def ResetUserInactivity(self, directive):
        self.dueros.last_activity = datetime.datetime.utcnow()

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "System",
    #             "name": "SetEndpoint",
    #             "messageId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "endpoint": "{{STRING}}"
    #         }
    #     }
    # }
    def SetEndpoint(self, directive):
        pass

    def ExceptionEncountered(self):
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "ExceptionEncountered",
                "messageId": "{{STRING}}"
            },
            "payload": {
                "unparsedDirective": "{{STRING}}",
                "error": {
                    "type": "{{STRING}}",
                    "message": "{{STRING}}"
                }
            }
        }
        self.dueros.send_event(event)

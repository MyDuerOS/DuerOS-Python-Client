# -*- coding: utf-8 -*-
'''
系统模块
参考：http://open.duer.baidu.com/doc/dueros-conversational-service/device-interface/system_markdown
'''
import uuid
import datetime


class System(object):
    '''
    系统控制类
    '''

    def __init__(self, dueros):
        '''
        类初始化
        :param dueros:DuerOS核心模块实例
        '''
        self.namespace = 'ai.dueros.device_interface.system'
        self.dueros = dueros

    def reset_user_inactivity(self, directive):
        '''
        重置“用户最近一次交互”的时间点为当前时间(云端directive　name方法)
        :param directive:云端下发directive
        :return:
        '''
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

    def set_endpoint(self, directive):
        '''
        设置服务端接入地址，重置连接(云端directive　name方法)
        :param directive:云端下发directive
        :return:
        '''
        pass

    def throw_exception(self, directive):
        '''
        当设备端发送的请求格式不正确、登录的认证信息过期等错误情况发生时，服务端会返回ThrowException指令给设备端
        (云端directive　name方法)
        :param directive: 云端下发directive
        :return:
        '''
        pass

    def synchronize_state(self):
        '''
        SynchronizeState状态上报(dueros_core中会使用)
        :return:
        '''
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

    def __user_Inactivity_report(self):
        '''
        UserInactivityReport状态上报
        :return:
        '''
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


    def __exception_encountered(self):
        '''
        ExceptionEncountered状态上报
        :return:
        '''
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

# coding:utf-8
from app.framework.player.aec_player.ipc_clinet import IpcClient
from app.framework.player.aec_player.process_message import ProcessMessage
import app.framework.player.aec_player.common_params as common_params
class Player(object):
    def __init__(self):
        self.ipc_client=IpcClient()
        self.ipc_client.add_listener(self.__ipc_listener)
        self.call_table = {}
    def play(self, url):
        # msg = ProcessMessage()
        # msg.type = common_params.PROCESS_MESSAGE_TPYE_AUDIO_PLAY
        # msg.set_str_params(common_params.ID, '1160253209')
        # msg.set_str_params(common_params.LOGID, '651d0597cc0e4e52a6f017a932509bc7')
        # msg.set_str_params(common_params.MESSAGE_ID, 'YXVkaW9fbXVzaWMrMTUxMDEzMTQxOV82MjlmcDEycGM=')
        # msg.set_str_params(common_params.PLAY_BEHAVIOR, 'REPLACE_ALL')
        # msg.set_str_params(common_params.TOKEN, 'YXVkaW9fbXVzaWMrMTE2MDI1MzIwOQ==')
        # msg.set_str_params(common_params.URL, url)
        # msg.set_str_params(common_params.FORMAT, 'AUDIO_MPEG')
        # msg.set_int_params(common_params.OFFSET_MS, 0)
        # msg.set_int_params(common_params.PROCESS_REPORT_INTERVAL_MS, 15000)

        msg = ProcessMessage()
        msg.type = common_params.PROCESS_MESSAGE_TPYE_AUDIO_PLAY
        msg.set_str_params(common_params.ID, '0')
        msg.set_str_params(common_params.LOGID, '0')
        msg.set_str_params(common_params.MESSAGE_ID, '0')
        msg.set_str_params(common_params.PLAY_BEHAVIOR, 'REPLACE_ALL')
        msg.set_str_params(common_params.TOKEN, '0')
        msg.set_str_params(common_params.URL, url)
        msg.set_str_params(common_params.FORMAT, 'AUDIO_MPEG')
        msg.set_int_params(common_params.OFFSET_MS, 0)
        msg.set_int_params(common_params.PROCESS_REPORT_INTERVAL_MS, 15000)

        self.ipc_client.send(msg)

    def stop(self):
        msg = ProcessMessage()
        msg.type = common_params.PROCESS_MESSAGE_TPYE_AUDIO_STOP
        self.ipc_client.send(msg)

    def pause(self):
        msg = ProcessMessage()
        msg.type = common_params.PROCESS_MESSAGE_TPYE_AUDIO_STOP
        self.ipc_client.send(msg)

    def resume(self):
        msg = ProcessMessage()
        msg.type = common_params.PROCESS_MESSAGE_TPYE_RESUME
        self.ipc_client.send(msg)

    def add_callback(self, name, callback):
        print "add a callback for :", name
        self.call_table[name] = callback

    def __ipc_listener(self, msg):
        print "received msg type = ", msg.type
        callbackfunc = self.call_table[msg.type]
        if (callbackfunc and callable(callbackfunc)):
            callbackfunc()

    @property
    def duration(self):
        pass

    @property
    def position(self):
        pass

    @property
    def state(self):
        pass





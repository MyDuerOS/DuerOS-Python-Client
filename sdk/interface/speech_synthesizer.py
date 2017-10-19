# -*- coding: utf-8 -*-
'''
语音输出模块(TTS)
参考:http://open.duer.baidu.com/doc/dueros-conversational-service/device-interface/voice-output_markdown
'''
import os
import tempfile
import threading
import uuid


class SpeechSynthesizer(object):
    '''
    语音输出模块功能类
    '''
    STATES = {'PLAYING', 'FINISHED'}

    def __init__(self, dueros, player):
        '''
        类初始化
        :param dueros:DuerOS核心模块实例
        :param player: 播放器实例
        '''
        self.namespace = 'ai.dueros.device_interface.voice_output'
        self.dueros = dueros
        self.token = ''
        self.state = 'FINISHED'
        self.finished = threading.Event()

        self.player = player
        self.player.add_callback('eos', self.__speech_finished)
        self.player.add_callback('error', self.__speech_finished)

    def stop(self):
        '''
        停止播放
        :return:
        '''
        self.finished.set()
        self.player.stop()
        self.state = 'FINISHED'

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "SpeechSynthesizer",
    #             "name": "Speak",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "url": "{{STRING}}",
    #             "format": "AUDIO_MPEG",
    #             "token": "{{STRING}}"
    #         }
    #     }
    # }
    # Content-Type: application/octet-stream
    # Content-ID: {{Audio Item CID}}
    # {{BINARY AUDIO ATTACHMENT}}
    def speak(self, directive):
        '''
        播放TTS(云端directive　name方法)
        :param directive: 云端下发directive
        :return:
        '''
        # directive from dueros may not have the dialogRequestId
        if 'dialogRequestId' in directive['header']:
            dialog_request_id = directive['header']['dialogRequestId']
            if self.dueros.speech_recognizer.dialog_request_id != dialog_request_id:
                return

        self.token = directive['payload']['token']
        url = directive['payload']['url']
        if url.startswith('cid:'):
            mp3_file = os.path.join(tempfile.gettempdir(), url[4:] + '.mp3')
            if os.path.isfile(mp3_file):
                self.finished.clear()
                # os.system('mpv "{}"'.format(mp3_file))
                self.player.play('file://{}'.format(mp3_file))
                self.__speech_started()

                self.dueros.state_listener.on_speaking()

                # will be set at SpeechFinished() if the player reaches the End Of Stream or gets a error
                self.finished.wait()

                os.system('rm -rf "{}"'.format(mp3_file))

    def __speech_started(self):
        '''
        speech开始状态上报
        :return:
        '''
        self.state = 'PLAYING'
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "SpeechStarted",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token
            }
        }
        self.dueros.send_event(event)

    def __speech_finished(self):
        self.dueros.state_listener.on_finished()

        self.finished.set()
        self.state = 'FINISHED'
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "SpeechFinished",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token
            }
        }
        self.dueros.send_event(event)

    @property
    def context(self):
        '''
        获取模块上下文(模块状态)
        :return:
        '''
        offset = self.player.position if self.state == 'PLAYING' else 0

        return {
            "header": {
                "namespace": self.namespace,
                "name": "SpeechState"
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": offset,
                "playerActivity": self.state
            }
        }

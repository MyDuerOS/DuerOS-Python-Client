# -*- coding: utf-8 -*-

"""
语音识别功能模块(语音输入)
参考：http://open.duer.baidu.com/doc/dueros-conversational-service/device-interface/voice-input_markdown
"""

import logging
import uuid

try:
    import Queue as queue
except ImportError:
    import queue

import sdk.sdk_config as sdk_config

logging.basicConfig(level=sdk_config.LOGGER_LEVEL)
logger = logging.getLogger('SpeechRecognizer')


class SpeechRecognizer(object):
    '''
    语音识别类(语音输入)
    '''
    STATES = {'IDLE', 'RECOGNIZING', 'BUSY', 'EXPECTING SPEECH'}
    PROFILES = {'CLOSE_TALK', 'NEAR_FIELD', 'FAR_FIELD'}
    PRESS_AND_HOLD = {'type': 'PRESS_AND_HOLD', 'payload': {}}
    TAP = {'type': 'TAP', 'payload': {}}

    def __init__(self, dueros):
        '''
        类初始化
        :param dueros:DuerOS核心实现模块实例
        '''
        self.namespace = 'ai.dueros.device_interface.voice_input'
        self.dueros = dueros
        self.profile = 'NEAR_FIELD'

        self.dialog_request_id = ''

        self.listening = False
        self.audio_queue = queue.Queue()

    def put(self, audio):
        """
        语音pcm输入
        :param audio: S16_LE format, sample rate 16000 bps audio data
        :return: None
        """
        if self.listening:
            self.audio_queue.put(audio)

    def recognize(self, dialog=None, timeout=10000):
        """
        语音识别
        :param dialog:会话ID
        :param timeout:超时时间(单位毫秒)
        :return:
        """

        if self.listening:
            return

        self.audio_queue.queue.clear()
        self.listening = True

        self.dueros.state_listener.on_listening()

        def on_finished():
            self.dueros.state_listener.on_finished()

            if self.dueros.audio_player.state == 'PAUSED':
                self.dueros.audio_player.resume()

        # Stop playing if Xiaoduxiaodu is speaking or AudioPlayer is playing
        if self.dueros.speech_synthesizer.state == 'PLAYING':
            self.dueros.speech_synthesizer.stop()
        elif self.dueros.audio_player.state == 'PLAYING':
            self.dueros.audio_player.pause()

        self.dialog_request_id = dialog if dialog else uuid.uuid4().hex

        event = {
            "header": {
                "namespace": self.namespace,
                "name": "ListenStarted",
                "messageId": uuid.uuid4().hex,
                "dialogRequestId": self.dialog_request_id
            },
            "payload": {
                "profile": self.profile,
                "format": "AUDIO_L16_RATE_16000_CHANNELS_1",
            }
        }

        def gen():
            time_elapsed = 0
            while self.listening or time_elapsed >= timeout:
                try:
                    chunk = self.audio_queue.get(timeout=1.0)
                except queue.Empty:
                    break

                yield chunk
                time_elapsed += 10  # 10 ms chunk

            self.listening = False
            self.dueros.state_listener.on_thinking()

        self.dueros.send_event(event, listener=on_finished, attachment=gen())

    # {
    #   "directive": {
    #         "header": {
    #             "namespace": "SpeechRecognizer",
    #             "name": "StopCapture",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #         }
    #     }
    # }
    def stop_listen(self, directive):
        '''
        停止录音监听(云端directive　name方法)
        :param directive: 云端下发的directive
        :return:
        '''
        self.listening = False
        logger.info('StopCapture')

    # {
    #   "directive": {
    #     "header": {
    #       "namespace": "SpeechRecognizer",
    #       "name": "ExpectSpeech",
    #       "messageId": "{{STRING}}",
    #       "dialogRequestId": "{{STRING}}"
    #     },
    #     "payload": {
    #       "timeoutInMilliseconds": {{LONG}},
    #       "initiator": "{{STRING}}"
    #     }
    #   }
    # }
    def listen(self, directive):
        '''
        启动录音监听(云端directive name方法)
        :param directive: 云端下发的directive
        :return:
        '''
        dialog = directive['header']['dialogRequestId']
        timeout = directive['payload']['timeoutInMilliseconds']

        self.recognize(dialog=dialog, timeout=timeout)

    def expect_speech_timeout(self):
        '''
        超时时间上报
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "ExpectSpeechTimedOut",
                "messageId": uuid.uuid4().hex,
            },
            "payload": {}
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
                "name": "ListenStarted"
            },
            "payload": {
                "wakeword": "xiaoduxiaodu"
            }
        }

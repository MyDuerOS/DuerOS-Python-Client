# -*- coding: utf-8 -*-

"""http://open.duer.baidu.com/doc/dueros-conversational-service/device-interface/voice-input_markdown"""

import logging
import uuid

try:
    import Queue as queue
except ImportError:
    import queue

logger = logging.getLogger('SpeechRecognizer')


class SpeechRecognizer(object):
    STATES = {'IDLE', 'RECOGNIZING', 'BUSY', 'EXPECTING SPEECH'}
    PROFILES = {'CLOSE_TALK', 'NEAR_FIELD', 'FAR_FIELD'}
    PRESS_AND_HOLD = {'type': 'PRESS_AND_HOLD', 'payload': {}}
    TAP = {'type': 'TAP', 'payload': {}}

    def __init__(self, dueros):
        self.namespace='ai.dueros.device_interface.voice_input'
        self.dueros = dueros
        self.profile = 'NEAR_FIELD'

        self.dialog_request_id = ''

        self.listening = False
        self.audio_queue = queue.Queue()

    def put(self, audio):
        """
        Put audio into queue when listening
        :param audio: S16_LE format, sample rate 16000 bps audio data
        :return: None
        """
        if self.listening:
            self.audio_queue.put(audio)

    def Recognize(self, dialog=None, initiator=None, timeout=10000):
        """
        recognize
        :param dialog:
        :param initiator:
        :param timeout:
        :return:
        """

        if self.listening:
            return

        self.audio_queue.queue.clear()
        self.listening = True

        self.dueros.state_listener.on_listening()

        def on_finished():
            self.dueros.state_listener.on_finished()

            if self.dueros.AudioPlayer.state == 'PAUSED':
                self.dueros.AudioPlayer.resume()

        # Stop playing if Xiaoduxiaodu is speaking or AudioPlayer is playing
        if self.dueros.SpeechSynthesizer.state == 'PLAYING':
            self.dueros.SpeechSynthesizer.stop()
        elif self.dueros.AudioPlayer.state == 'PLAYING':
            self.dueros.AudioPlayer.pause()

        self.dialog_request_id = dialog if dialog else uuid.uuid4().hex

        # TODO: set initiator properly
        if initiator is None:
            initiator = self.TAP

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
                'initiator': initiator
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
    def StopListen(self, directive):
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
    def Listen(self, directive):
        dialog = directive['header']['dialogRequestId']
        timeout = directive['payload']['timeoutInMilliseconds']

        initiator = None
        if 'initiator' in directive['payload']:
            initiator = directive['payload']['initiator']

        self.Recognize(dialog=dialog, initiator=initiator, timeout=timeout)

    def ExpectSpeechTimedOut(self):
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
        return {
            "header": {
                "namespace": self.namespace,
                "name": "ListenStarted"
            },
            "payload": {
                "wakeword": "xiaoduxiaodu"
            }
        }

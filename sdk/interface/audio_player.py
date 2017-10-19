# -*- coding: utf-8 -*-

"""
音乐播放模块
参考：http://open.duer.baidu.com/doc/dueros-conversational-service/device-interface/audio-player_markdown
"""

import os
import tempfile
import uuid


class AudioPlayer(object):
    '''
    音乐播放类
    '''
    STATES = {'IDLE', 'PLAYING', 'STOPPED', 'PAUSED', 'BUFFER_UNDERRUN', 'FINISHED'}

    def __init__(self, dueros, player):
        '''
        类初始化
        :param dueros:DuerOS核心模块实例
        :param player: 播放器实例（平台相关）
        '''
        self.namespace = 'ai.dueros.device_interface.audio_player'
        self.dueros = dueros
        self.token = ''
        self.state = 'IDLE'

        self.player = player
        self.player.add_callback('eos', self.__playback_finished)
        self.player.add_callback('error', self.__playback_failed)

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "AudioPlayer",
    #             "name": "Play",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "playBehavior": "{{STRING}}",
    #             "audioItem": {
    #                 "audioItemId": "{{STRING}}",
    #                 "stream": {
    #                     "url": "{{STRING}}",
    #                     "streamFormat": "AUDIO_MPEG"
    #                     "offsetInMilliseconds": {{LONG}},
    #                     "expiryTime": "{{STRING}}",
    #                     "progressReport": {
    #                         "progressReportDelayInMilliseconds": {{LONG}},
    #                         "progressReportIntervalInMilliseconds": {{LONG}}
    #                     },
    #                     "token": "{{STRING}}",
    #                     "expectedPreviousToken": "{{STRING}}"
    #                 }
    #             }
    #         }
    #     }
    # }
    def pause(self):
        '''
        暂停播放
        :return:
        '''
        self.player.pause()
        self.__playback_paused()

    def resume(self):
        '''
        恢复播放
        :return:
        '''
        self.player.resume()
        self.__playback_resumed()

    def play(self, directive):
        '''
        播放(云端directive name方法)
        :param directive:云端下发directive
        :return:
        '''
        behavior = directive['payload']['playBehavior']
        self.token = directive['payload']['audioItem']['stream']['token']
        audio_url = directive['payload']['audioItem']['stream']['url']
        if audio_url.startswith('cid:'):
            mp3_file = os.path.join(tempfile.gettempdir(), audio_url[4:] + '.mp3')
            if os.path.isfile(mp3_file):
                # os.system('mpv "{}"'.format(mp3_file))
                # os.system('rm -rf "{}"'.format(mp3_file))
                self.player.play('file://{}'.format(mp3_file))
                self.__playback_started()
        else:
            # os.system('mpv {}'.format(audio_url))
            self.player.play(audio_url)
            self.__playback_started()

    def stop(self, directive):
        '''
        停止(云端directive name方法)
        :param directive: 云端下发directive
        :return:
        '''
        self.player.stop()
        self.__playback_stopped()

    def clear_queue(self, directive):
        '''
        播放队列清除(云端directive name方法)
        :param directive: 云端下发directive
        :return:
        '''
        self.__playback_queue_cleared()
        behavior = directive['payload']['clearBehavior']
        if behavior == 'CLEAR_ALL':
            self.player.stop()
        elif behavior == 'CLEAR_ENQUEUED':
            pass

    def __playback_started(self):
        '''
        开始播放状态上报
        :return:
        '''
        self.state = 'PLAYING'

        event = {
            "header": {
                "namespace": self.namespace,
                "name": "PlaybackStarted",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.dueros.send_event(event)

    def __playback_nearly_finished(self):
        '''
        播放即将结束状态上报
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "PlaybackNearlyFinished",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.dueros.send_event(event)

    def __playback_finished(self):
        '''
        播放结束事件上报
        :return:
        '''
        self.state = 'FINISHED'

        event = {
            "header": {
                "namespace": self.namespace,
                "name": "PlaybackFinished",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.dueros.send_event(event)

    def __playback_failed(self):
        '''
        播放失败
        :return:
        '''
        self.state = 'STOPPED'

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "AudioPlayer",
    #             "name": "Stop",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #         }
    #     }
    # }

    def __playback_stopped(self):
        '''
        播放结束状态上报
        :return:
        '''
        self.state = 'STOPPED'
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "PlaybackStopped",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.dueros.send_event(event)

    def __playback_paused(self):
        '''
        播放暂停状态上报
        :return:
        '''
        self.state = 'PAUSED'
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "PlaybackPaused",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.dueros.send_event(event)

    def __playback_resumed(self):
        '''
        播放恢复状态上报
        :return:
        '''
        self.state = 'PLAYING'
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "PlaybackResumed",
                "messageId": uuid.uuid4().hex
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": self.player.position
            }
        }
        self.dueros.send_event(event)

    # {
    #     "directive": {
    #         "header": {
    #             "namespace": "AudioPlayer",
    #             "name": "ClearQueue",
    #             "messageId": "{{STRING}}",
    #             "dialogRequestId": "{{STRING}}"
    #         },
    #         "payload": {
    #             "clearBehavior": "{{STRING}}"
    #         }
    #     }
    # }

    def __playback_queue_cleared(self):
        '''
        播放队列数据清除事件上报
        :return:
        '''
        event = {
            "header": {
                "namespace": self.namespace,
                "name": "PlaybackQueueCleared",
                "messageId": uuid.uuid4().hex
            },
            "payload": {}
        }
        self.dueros.send_event(event)

    def __progress_report_delay_elapsed(self):
        '''
        ProgressReportDelayElapsed事件上报
        :return:
        '''
        pass

    def __progress_report_interval_elapsed(self):
        '''
        ProgressReportIntervalElapsed事件上报
        :return:
        '''
        pass

    def __playback_stutter_started(self):
        '''
        PlaybackStutterStarted事件上报
        :return:
        '''
        pass

    def __playback_stutter_finished(self):
        '''
        PlaybackStutterFinished事件上报
        :return:
        '''
        pass

    def __stream_metadata_extracted(self):
        '''
        StreamMetadataExtracted事件上报
        :return:
        '''
        pass

    @property
    def context(self):
        '''
        获取模块上下文(模块状态)
        :return:
        '''
        if self.state != 'PLAYING':
            offset = 0
        else:
            offset = self.player.position

        return {
            "header": {
                "namespace": self.namespace,
                "name": "PlaybackState"
            },
            "payload": {
                "token": self.token,
                "offsetInMilliseconds": offset,
                "playerActivity": self.state
            }
        }

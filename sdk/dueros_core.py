# -*- coding: utf-8 -*-
'''
DuerOS服务核心模块
'''

import cgi
import io
import json
import logging
import os
import sys
import tempfile
import uuid

import requests

try:
    import Queue as queue
except ImportError:
    import queue
import threading
import datetime

import hyper

import sdk.configurate
import sdk.sdk_config as sdk_config

from sdk.interface.alerts import Alerts
from sdk.interface.audio_player import AudioPlayer
from sdk.interface.speaker import Speaker
from sdk.interface.speech_recognizer import SpeechRecognizer
from sdk.interface.speech_synthesizer import SpeechSynthesizer
from sdk.interface.system import System

logging.basicConfig(level=sdk_config.LOGGER_LEVEL)
logger = logging.getLogger(__name__)


class DuerOSStateListner(object):
    '''
    DuerOS状态监听类
    '''

    def __init__(self):
        pass

    def on_listening(self):
        '''
        监听状态回调
        :return:
        '''
        logging.info('[DuerOS状态]正在倾听..........')

    def on_thinking(self):
        '''
        语义理解状态回调
        :return:
        '''
        logging.info('[DuerOS状态]正在思考.........')

    def on_speaking(self):
        '''
        播放状态回调
        :return:
        '''
        logging.info('[DuerOS状态]正在播放........')

    def on_finished(self):
        '''
        处理结束状态回调
        :return:
        '''
        logging.info('[DuerOS状态]结束')


class DuerOS(object):
    '''
    DuerOS核心模块类，实现功能包括:
        录音数据上传
        本地状态上报
        长链接建立与维护(Ping)
        Directive下发
    '''

    def __init__(self, player):
        '''
        类初始化
        :param player:播放器
        '''
        self.event_queue = queue.Queue()
        self.speech_recognizer = SpeechRecognizer(self)
        self.speech_synthesizer = SpeechSynthesizer(self, player)
        self.audio_player = AudioPlayer(self, player)
        self.speaker = Speaker(self)
        self.alerts = Alerts(self, player)
        self.system = System(self)

        self.state_listener = DuerOSStateListner()

        # handle audio to speech recognizer
        self.put = self.speech_recognizer.put

        # listen() will trigger SpeechRecognizer's Recognize event
        # self.listen = self.speech_recognizer.recognize

        self.done = False

        self.requests = requests.Session()

        self.__config = sdk.configurate.load()

        self.__config['host_url'] = 'dueros-h2.baidu.com'

        self.__config['api'] = 'dcs/v1'
        self.__config['refresh_url'] = 'https://openapi.baidu.com/oauth/2.0/token'

        self.last_activity = datetime.datetime.utcnow()
        self.__ping_time = None

        self.directive_listener = None

    def set_directive_listener(self, listener):
        '''
        directive监听器设置
        :param listener: directive监听器
        :return:
        '''
        if callable(listener):
            self.directive_listener = listener
        else:
            raise ValueError('directive监听器注册失败[参数不可回调]！')

    def start(self):
        '''
        DuerOS模块启动
        :return:
        '''
        self.done = False

        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()

    def stop(self):
        '''
        DuerOS模块停止
        :return:
        '''
        self.done = True

    def listen(self):
        '''
        DuerOS进入语音识别状态
        :return:
        '''
        self.speech_recognizer.recognize()

    def send_event(self, event, listener=None, attachment=None):
        '''
        状态上报
        :param event:上传状态
        :param listener:VAD检测回调[云端识别语音输入结束]
        :param attachment:录音数据
        :return:
        '''
        self.event_queue.put((event, listener, attachment))

    def run(self):
        '''
        DuerOS线程实体
        :return:
        '''
        while not self.done:
            try:
                self.__run()
            except AttributeError as e:
                logger.exception(e)
                continue
            except hyper.http20.exceptions.StreamResetError as e:
                logger.exception(e)
                continue
            except ValueError as e:
                logging.exception(e)
                # failed to get an access token, exit
                sys.exit(1)
            except Exception as e:
                logging.exception(e)
                continue

    def __run(self):
        '''
        run方法实现
        :return:
        '''
        conn = hyper.HTTP20Connection('{}:443'.format(self.__config['host_url']), force_proto='h2')

        headers = {'authorization': 'Bearer {}'.format(self.token)}
        if 'dueros-device-id' in self.__config:
            headers['dueros-device-id'] = self.__config['dueros-device-id']

        downchannel_id = conn.request('GET', '/{}/directives'.format(self.__config['api']), headers=headers)
        downchannel_response = conn.get_response(downchannel_id)

        if downchannel_response.status != 200:
            raise ValueError("/directive requests returned {}".format(downchannel_response.status))

        ctype, pdict = cgi.parse_header(downchannel_response.headers['content-type'][0].decode('utf-8'))
        downchannel_boundary = '--{}'.format(pdict['boundary']).encode('utf-8')
        downchannel = conn.streams[downchannel_id]
        downchannel_buffer = io.BytesIO()
        eventchannel_boundary = 'baidu-voice-engine'

        # ping every 5 minutes (60 seconds early for latency) to maintain the connection
        self.__ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)

        self.event_queue.queue.clear()

        self.system.synchronize_state()

        while not self.done:
            # logger.info("Waiting for event to send to AVS")
            # logger.info("Connection socket can_read %s", conn._sock.can_read)
            try:
                event, listener, attachment = self.event_queue.get(timeout=0.25)
            except queue.Empty:
                event = None

            # we want to avoid blocking if the data wasn't for stream downchannel
            while conn._sock.can_read:
                conn._single_read()

            while downchannel.data:
                framebytes = downchannel._read_one_frame()
                self.__read_response(framebytes, downchannel_boundary, downchannel_buffer)

            if event is None:
                self.__ping(conn)
                continue

            headers = {
                ':method': 'POST',
                ':scheme': 'https',
                ':path': '/{}/events'.format(self.__config['api']),
                'authorization': 'Bearer {}'.format(self.token),
                'content-type': 'multipart/form-data; boundary={}'.format(eventchannel_boundary)
            }
            if 'dueros-device-id' in self.__config:
                headers['dueros-device-id'] = self.__config['dueros-device-id']

            stream_id = conn.putrequest(headers[':method'], headers[':path'])
            default_headers = (':method', ':scheme', ':authority', ':path')
            for name, value in headers.items():
                is_default = name in default_headers
                conn.putheader(name, value, stream_id, replace=is_default)
            conn.endheaders(final=False, stream_id=stream_id)

            metadata = {
                'clientContext': self.context,
                'event': event
            }
            logger.debug('metadata: {}'.format(json.dumps(metadata, indent=4)))

            json_part = '--{}\r\n'.format(eventchannel_boundary)
            json_part += 'Content-Disposition: form-data; name="metadata"\r\n'
            json_part += 'Content-Type: application/json; charset=UTF-8\r\n\r\n'
            json_part += json.dumps(metadata)

            conn.send(json_part.encode('utf-8'), final=False, stream_id=stream_id)

            if attachment:
                attachment_header = '\r\n--{}\r\n'.format(eventchannel_boundary)
                attachment_header += 'Content-Disposition: form-data; name="audio"\r\n'
                attachment_header += 'Content-Type: application/octet-stream\r\n\r\n'
                conn.send(attachment_header.encode('utf-8'), final=False, stream_id=stream_id)

                # AVS_AUDIO_CHUNK_PREFERENCE = 320
                for chunk in attachment:
                    conn.send(chunk, final=False, stream_id=stream_id)
                    # print '===============send(attachment.chunk)'

                    # check if StopCapture directive is received
                    while conn._sock.can_read:
                        conn._single_read()

                    while downchannel.data:
                        framebytes = downchannel._read_one_frame()
                        self.__read_response(framebytes, downchannel_boundary, downchannel_buffer)

                self.last_activity = datetime.datetime.utcnow()

            end_part = '\r\n--{}--'.format(eventchannel_boundary)
            conn.send(end_part.encode('utf-8'), final=True, stream_id=stream_id)

            logger.info("wait for response")
            resp = conn.get_response(stream_id)
            logger.info("status code: %s", resp.status)

            if resp.status == 200:
                self.__read_response(resp)
            elif resp.status == 204:
                pass
            else:
                logger.warning(resp.headers)
                logger.warning(resp.read())

            if listener and callable(listener):
                listener()

    def __read_response(self, response, boundary=None, buffer=None):
        '''
        云端回复数据读取解析
        :param response:包含http header信息
        :param boundary:multipart boundary
        :param buffer:包含http body数据
        :return:
        '''
        if boundary:
            endboundary = boundary + b"--"
        else:
            ctype, pdict = cgi.parse_header(
                response.headers['content-type'][0].decode('utf-8'))
            boundary = "--{}".format(pdict['boundary']).encode('utf-8')
            endboundary = "--{}--".format(pdict['boundary']).encode('utf-8')

        on_boundary = False
        in_header = False
        in_payload = False
        first_payload_block = False
        content_type = None
        content_id = None

        def iter_lines(response, delimiter=None):
            pending = None
            for chunk in response.read_chunked():
                # logger.debug("Chunk size is {}".format(len(chunk)))
                if pending is not None:
                    chunk = pending + chunk
                if delimiter:
                    lines = chunk.split(delimiter)
                else:
                    lines = chunk.splitlines()

                if lines and lines[-1] and chunk and lines[-1][-1] == chunk[-1]:
                    pending = lines.pop()
                else:
                    pending = None

                for line in lines:
                    yield line

            if pending is not None:
                yield pending

        # cache them up to execute after we've downloaded any binary attachments
        # so that they have the content available
        directives = []
        if isinstance(response, bytes):
            buffer.seek(0)
            lines = (buffer.read() + response).split(b"\r\n")
            buffer.flush()
        else:
            lines = iter_lines(response, delimiter=b"\r\n")
        for line in lines:
            # logger.debug("iter_line is {}...".format(repr(line)[0:30]))
            if line == boundary or line == endboundary:
                # logger.debug("Newly on boundary")
                on_boundary = True
                if in_payload:
                    in_payload = False
                    if content_type == "application/json":
                        logger.info("Finished downloading JSON")
                        utf8_payload = payload.getvalue().decode('utf-8')
                        if utf8_payload:
                            json_payload = json.loads(utf8_payload)
                            logger.debug(json_payload)
                            if 'directive' in json_payload:
                                directives.append(json_payload['directive'])
                    else:
                        logger.info("Finished downloading {} which is {}".format(content_type, content_id))
                        payload.seek(0)
                        # TODO, start to stream this to speakers as soon as we start getting bytes
                        # strip < and >
                        content_id = content_id[1:-1]
                        with open(os.path.join(tempfile.gettempdir(), '{}.mp3'.format(content_id)), 'wb') as f:
                            f.write(payload.read())

                        logger.info('write audio to {}.mp3'.format(content_id))

                continue
            elif on_boundary:
                # logger.debug("Now in header")
                on_boundary = False
                in_header = True
            elif in_header and line == b"":
                # logger.debug("Found end of header")
                in_header = False
                in_payload = True
                first_payload_block = True
                payload = io.BytesIO()
                continue

            if in_header:
                # logger.debug(repr(line))
                if len(line) > 1:
                    header, value = line.decode('utf-8').split(":", 1)
                    ctype, pdict = cgi.parse_header(value)
                    if header.lower() == "content-type":
                        content_type = ctype
                    if header.lower() == "content-id":
                        content_id = ctype

            if in_payload:
                # add back the bytes that our iter_lines consumed
                logger.info("Found %s bytes of %s %s, first_payload_block=%s",
                            len(line), content_id, content_type, first_payload_block)
                if first_payload_block:
                    first_payload_block = False
                else:
                    payload.write(b"\r\n")
                # TODO write this to a queue.Queue in self._content_cache[content_id]
                # so that other threads can start to play it right away
                payload.write(line)

        if buffer is not None:
            if in_payload:
                logger.info(
                    "Didn't see an entire directive, buffering to put at top of next frame")
                buffer.write(payload.read())
            else:
                buffer.write(boundary)
                buffer.write(b"\r\n")

        for directive in directives:
            self.__handle_directive(directive)

    def __handle_directive(self, directive):
        '''
        directive处理
        :param directive:
        :return:
        '''
        if 'directive_listener' in dir(self):
            self.directive_listener(directive)

        logger.debug(json.dumps(directive, indent=4))
        try:
            namespace = directive['header']['namespace']

            namespace = self.__namespace_convert(namespace)
            if not namespace:
                return

            name = directive['header']['name']
            name = self.__name_convert(name)
            if hasattr(self, namespace):
                interface = getattr(self, namespace)
                directive_func = getattr(interface, name, None)
                if directive_func:
                    directive_func(directive)
                else:
                    logger.info('{}.{} is not implemented yet'.format(namespace, name))
            else:
                logger.info('{} is not implemented yet'.format(namespace))

        except KeyError as e:
            logger.exception(e)
        except Exception as e:
            logger.exception(e)

    def __ping(self, connection):
        '''
        长链接维护,ping操作
        :param connection:链接句柄
        :return:
        '''
        if datetime.datetime.utcnow() >= self.__ping_time:
            # ping_stream_id = connection.request('GET', '/ping',
            #                                     headers={'authorization': 'Bearer {}'.format(self.token)})
            # resp = connection.get_response(ping_stream_id)
            # if resp.status != 200 and resp.status != 204:
            #     logger.warning(resp.read())
            #     raise ValueError("/ping requests returned {}".format(resp.status))

            connection.ping(uuid.uuid4().hex[:8])

            logger.debug('ping at {}'.format(datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S %Y")))

            # ping every 5 minutes (60 seconds early for latency) to maintain the connection
            self.__ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)

    @property
    def context(self):
        '''
        模块当前上下文(当前状态集合)
        :return:
        '''
        return [self.speech_synthesizer.context, self.speaker.context, self.audio_player.context, self.alerts.context]

    @property
    def token(self):
        '''
        token获取
        :return:
        '''
        date_format = "%a %b %d %H:%M:%S %Y"

        if 'access_token' in self.__config:
            if 'expiry' in self.__config:
                expiry = datetime.datetime.strptime(self.__config['expiry'], date_format)
                # refresh 60 seconds early to avoid chance of using expired access_token
                if (datetime.datetime.utcnow() - expiry) > datetime.timedelta(seconds=60):
                    logger.info("Refreshing access_token")
                else:
                    return self.__config['access_token']

        payload = {
            'client_id': self.__config['client_id'],
            'client_secret': self.__config['client_secret'],
            'grant_type': 'refresh_token',
            'refresh_token': self.__config['refresh_token']
        }

        response = None

        # try to request an access token 3 times
        for i in range(3):
            try:
                response = self.requests.post(self.__config['refresh_url'], data=payload)
                if response.status_code != 200:
                    logger.warning(response.text)
                else:
                    break
            except Exception as e:
                logger.exception(e)
                continue

        if (response is None) or (not hasattr(response, 'status_code')) or response.status_code != 200:
            raise ValueError("refresh token request returned {}".format(response.status))

        config = response.json()
        self.__config['access_token'] = config['access_token']

        expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=config['expires_in'])
        self.__config['expiry'] = expiry_time.strftime(date_format)
        logger.debug(json.dumps(self.__config, indent=4))

        sdk.configurate.save(self.__config, configfile=self._configfile)

        return self.__config['access_token']

    def __namespace_convert(self, namespace):
        '''
        将namespace字段内容与interface中的模块进行一一对应
        :param namespace: directive中namespace字段
        :return:
        '''
        if namespace == 'ai.dueros.device_interface.voice_output':
            return 'speech_synthesizer'
        elif namespace == 'ai.dueros.device_interface.voice_input':
            return 'speech_recognizer'
        elif namespace == 'ai.dueros.device_interface.alerts':
            return 'alerts'
        elif namespace == 'ai.dueros.device_interface.audio_player':
            return 'audio_player'
        elif namespace == 'ai.dueros.device_interface.speaker_controller':
            return 'speaker'
        elif namespace == 'ai.dueros.device_interface.system':
            return 'system'
        else:
            return None

    def __name_convert(self, name):
        '''
        将name字段内容与interface中的模块方法进行一一对应
        :param name: directive中name字段
        :return:
        '''
        # 语音输入模块[speech_recognizer]
        if name == 'StopListen':
            return 'stop_listen'
        elif name == 'Listen':
            return 'listen'
        # 语音输出模块[speech_synthesizer]
        elif name == 'Speak':
            return 'speak'
        # 扬声器控制模块[speaker]
        elif name == 'SetVolume':
            return 'set_volume'
        elif name == 'AdjustVolume':
            return 'adjust_volume'
        elif name == 'SetMute':
            return 'set_mute'
        # 音频播放器模块[audio_player]
        elif name == 'Play':
            return 'play'
        elif name == 'Stop':
            return 'stop'
        elif name == 'ClearQueue':
            return 'clear_queue'
        # 播放控制[playback_controller]
        # 闹钟模块[alerts]
        elif name == 'SetAlert':
            return 'set_alert'
        elif name == 'DeleteAlert':
            return 'delete_alert'
        # 屏幕展示模块[screen_display]
        elif name == 'HtmlView':
            return 'html_view'
        # 系统模块
        elif name == 'ResetUserInactivity':
            return 'reset_user_inactivity'
        elif name == 'SetEndpoint':
            return 'set_end_point'
        elif name == 'ThrowException':
            return 'throw_exception'

# -*- coding: utf-8 -*-


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

from dueros.interface.alerts import Alerts
from dueros.interface.audio_player import AudioPlayer
from dueros.interface.speaker import Speaker
from dueros.interface.speech_recognizer import SpeechRecognizer
from dueros.interface.speech_synthesizer import SpeechSynthesizer
from dueros.interface.system import System
import dueros.config

logger = logging.getLogger(__name__)


class DuerOSStateListner(object):
    def __init__(self):
        pass

    def on_listening(self):
        logger.debug('on_listening')

    def on_thinking(self):
        logger.debug('on_thinking')

    def on_speaking(self):
        logger.debug('on_speaking')

    def on_finished(self):
        logger.debug('on_finished')


class DuerOS(object):
    def __init__(self, config=None):
        self.event_queue = queue.Queue()
        self.SpeechRecognizer = SpeechRecognizer(self)
        self.SpeechSynthesizer = SpeechSynthesizer(self)
        self.AudioPlayer = AudioPlayer(self)
        self.Speaker = Speaker(self)
        self.Alerts = Alerts(self)
        self.System = System(self)

        self.state_listener = DuerOSStateListner()

        # handle audio to speech recognizer
        self.put = self.SpeechRecognizer.put

        # listen() will trigger SpeechRecognizer's Recognize event
        self.listen = self.SpeechRecognizer.Recognize

        self.done = False

        self.requests = requests.Session()

        self._configfile = config
        self._config = dueros.config.load(configfile=config)

        if self._config['host_url'] == 'dueros-h2.baidu.com':
            self._config['api'] = 'dcs/v1'
            self._config['refresh_url'] = 'https://openapi.baidu.com/oauth/2.0/token'

        self.last_activity = datetime.datetime.utcnow()
        self._ping_time = None

    def set_state_listner(self, listner):
        self.state_listener = listner

    def start(self):
        self.done = False

        t = threading.Thread(target=self.run)
        t.daemon = True
        t.start()

    def stop(self):
        self.done = True

    def send_event(self, event, listener=None, attachment=None):
        self.event_queue.put((event, listener, attachment))

    def run(self):
        while not self.done:
            try:
                self._run()
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

    def _run(self):
        conn = hyper.HTTP20Connection('{}:443'.format(self._config['host_url']), force_proto='h2')

        headers = {'authorization': 'Bearer {}'.format(self.token)}
        if 'dueros-device-id' in self._config:
            print '=================run::dueros-device-id={}'.format(self._config['dueros-device-id'])
            headers['dueros-device-id'] = self._config['dueros-device-id']

        downchannel_id = conn.request('GET', '/{}/directives'.format(self._config['api']), headers=headers)
        downchannel_response = conn.get_response(downchannel_id)

        print '===========downchannel_response.status=', downchannel_response.status

        if downchannel_response.status != 200:
            raise ValueError("/directive requests returned {}".format(downchannel_response.status))

        ctype, pdict = cgi.parse_header(downchannel_response.headers['content-type'][0].decode('utf-8'))
        downchannel_boundary = '--{}'.format(pdict['boundary']).encode('utf-8')
        downchannel = conn.streams[downchannel_id]
        downchannel_buffer = io.BytesIO()
        eventchannel_boundary = 'baidu-voice-engine'

        # ping every 5 minutes (60 seconds early for latency) to maintain the connection
        self._ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)

        self.event_queue.queue.clear()

        self.System.SynchronizeState()

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
                self._read_response(
                    framebytes, downchannel_boundary, downchannel_buffer)

            if event is None:
                self._ping(conn)
                continue

            headers = {
                ':method': 'POST',
                ':scheme': 'https',
                ':path': '/{}/events'.format(self._config['api']),
                'authorization': 'Bearer {}'.format(self.token),
                'content-type': 'multipart/form-data; boundary={}'.format(eventchannel_boundary)
            }
            if 'dueros-device-id' in self._config:
                headers['dueros-device-id'] = self._config['dueros-device-id']

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
                        self._read_response(framebytes, downchannel_boundary, downchannel_buffer)

                self.last_activity = datetime.datetime.utcnow()

            end_part = '\r\n--{}--'.format(eventchannel_boundary)
            conn.send(end_part.encode('utf-8'), final=True, stream_id=stream_id)

            logger.info("wait for response")
            resp = conn.get_response(stream_id)
            logger.info("status code: %s", resp.status)

            if resp.status == 200:
                self._read_response(resp)
            elif resp.status == 204:
                pass
            else:
                logger.warning(resp.headers)
                logger.warning(resp.read())

            if listener and callable(listener):
                listener()

    def _read_response(self, response, boundary=None, buffer=None):
        print '=============_read_response()'
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
            self._handle_directive(directive)

    def _handle_directive(self, directive):
        print '============directive:', directive
        logger.debug(json.dumps(directive, indent=4))
        try:
            namespace = directive['header']['namespace']

            namespace = self.__namespace_convert(namespace)
            if not namespace:
                return

            name = directive['header']['name']
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

    def _ping(self, connection):
        if datetime.datetime.utcnow() >= self._ping_time:
            # ping_stream_id = connection.request('GET', '/ping',
            #                                     headers={'authorization': 'Bearer {}'.format(self.token)})
            # resp = connection.get_response(ping_stream_id)
            # if resp.status != 200 and resp.status != 204:
            #     logger.warning(resp.read())
            #     raise ValueError("/ping requests returned {}".format(resp.status))

            connection.ping(uuid.uuid4().hex[:8])

            logger.debug('ping at {}'.format(datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S %Y")))

            # ping every 5 minutes (60 seconds early for latency) to maintain the connection
            self._ping_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=240)

    @property
    def context(self):
        # return [self.SpeechRecognizer.context, self.SpeechSynthesizer.context,
        #                    self.AudioPlayer.context, self.Speaker.context, self.Alerts.context]
        return [self.SpeechSynthesizer.context, self.Speaker.context, self.AudioPlayer.context, self.Alerts.context]

    @property
    def token(self):
        date_format = "%a %b %d %H:%M:%S %Y"

        if 'access_token' in self._config:
            if 'expiry' in self._config:
                expiry = datetime.datetime.strptime(self._config['expiry'], date_format)
                # refresh 60 seconds early to avoid chance of using expired access_token
                if (datetime.datetime.utcnow() - expiry) > datetime.timedelta(seconds=60):
                    logger.info("Refreshing access_token")
                else:
                    return self._config['access_token']

        payload = {
            'client_id': self._config['client_id'],
            'client_secret': self._config['client_secret'],
            'grant_type': 'refresh_token',
            'refresh_token': self._config['refresh_token']
        }

        response = None

        # try to request an access token 3 times
        for i in range(3):
            try:
                response = self.requests.post(self._config['refresh_url'], data=payload)
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
        self._config['access_token'] = config['access_token']

        expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=config['expires_in'])
        self._config['expiry'] = expiry_time.strftime(date_format)
        logger.debug(json.dumps(self._config, indent=4))

        dueros.config.save(self._config, configfile=self._configfile)

        return self._config['access_token']

    def __namespace_convert(self, namespace):
        if namespace == 'ai.dueros.device_interface.voice_output':
            return 'SpeechSynthesizer'
        elif namespace == 'ai.dueros.device_interface.voice_input':
            return 'SpeechRecognizer'
        elif namespace == 'ai.dueros.device_interface.alerts':
            return 'Alerts'
        elif namespace == 'ai.dueros.device_interface.audio_player':
            return 'AudioPlayer'
        elif namespace == 'ai.dueros.device_interface.speaker_controller':
            return 'Speaker'
        elif namespace == 'ai.dueros.device_interface.system':
            return 'System'
        elif:
            return None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def main():
    import sys
    from dueros.mic import Audio

    logging.basicConfig(level=logging.DEBUG)

    config = None if len(sys.argv) < 2 else sys.argv[1]

    audio = Audio()
    dueros = DuerOS(config)

    audio.link(dueros)

    dueros.start()
    audio.start()

    while True:
        try:
            try:
                input('press ENTER to talk\n')
            except SyntaxError:
                pass

            dueros.listen()
        except KeyboardInterrupt:
            break

    dueros.stop()
    audio.stop()


if __name__ == '__main__':
    main()

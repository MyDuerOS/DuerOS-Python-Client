# -*- coding: utf-8 -*-

"""
Hands-free DuerOS with respeaker using Snowboy to search keyword

"""

import sys
import threading
import time

try:
    import Queue as queue
except ImportError:
    import queueg

import logging

logger = logging.getLogger(__file__)


class SnowBoy(object):
    def __init__(self):
        from app.snowboy import snowboydecoder
        model = 'dueros/snowboy/xiaoduxiaodu.pmdl'
        self.detector = snowboydecoder.HotwordDetector(model, sensitivity=0.5, audio_gain=1)

    def feed_data(self, data):
        self.detector.feed_data(data)

    def set_callback(self, callback):
        self.__calback = callback

    def run(self):
        self.detector.start(self.__calback)

    def start(self):
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.detector.terminate()


class KWS(object):
    def __init__(self):
        self.queue = queue.Queue()

        self.sinks = []
        self._callback = None

        self.done = False

    def set_wakeup_detector(self, detector):
        self.wakeup_detector = detector

    def put(self, data):
        self.queue.put(data)

    def start(self):
        self.done = False
        thread = threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def stop(self):
        self.done = True

    def link(self, sink):
        if hasattr(sink, 'put') and callable(sink.put):
            self.sinks.append(sink)
        else:
            raise ValueError('Not implement put() method')

    def unlink(self, sink):
        self.sinks.remove(sink)

    def run(self):
        while not self.done:
            chunk = self.queue.get()
            self.wakeup_detector.feed_data(chunk)

            for sink in self.sinks:
                sink.put(chunk)


def main():
    from sdk.dueros_core import DuerOS
    from framework.mic import Audio

    logging.basicConfig(level=logging.DEBUG)

    config = None if len(sys.argv) < 2 else sys.argv[1]

    audio = Audio()
    kws = KWS()
    dueros = DuerOS(config)
    snowboy = SnowBoy()

    audio.link(kws)
    kws.link(dueros)
    kws.set_wakeup_detector(snowboy)

    def wakeup():
        print '=============wake up is triggered!'
        dueros.listen()

    snowboy.set_callback(wakeup)

    dueros.start()
    kws.start()
    snowboy.start()
    audio.start()

    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    dueros.stop()
    kws.stop()
    audio.stop()
    snowboy.stop()


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-
import Queue as queue
import threading
import wave


class MicDataSaver(object):
    '''
    录音数据保存工具类
    '''

    def __init__(self):
        # 保存录音数据文件名称
        self.file_name = 'mic_save_data.wav'
        self.queue = queue.Queue()
        self.wf = None

    def put(self, data):
        '''
        录音数据缓存
        :param data:录音pcm流
        :return:
        '''

        self.queue.put(data)

    def start(self):
        '''
        开始保存录音数据
        :return:
        '''
        self.wf = wave.open(self.file_name, 'wb')
        self.wf.setnchannels(1)
        self.wf.setsampwidth(2)
        self.wf.setframerate(16000)

        self.done = False
        thread = threading.Thread(target=self.__run)
        thread.daemon = True
        thread.start()

    def stop(self):
        '''
        停止录音数据保存
        :return:
        '''
        self.done = True

        self.wf.close()

    def __run(self):
        '''
        录音数据保存到文件中
        :return:
        '''
        while not self.done:
            chunk = self.queue.get()
            self.wf.writeframes(chunk)

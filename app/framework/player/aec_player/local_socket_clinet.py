# coding:utf-8

import socket
import sys


class LocalSocketClint(object):
    def __init__(self):
        self.AUDIO_PLAYER_ADDR = '/duer/audioplayer_socket_file'
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    def bind(self):
        print 'start to bind server........'

        try:
            self.sock.connect(self.AUDIO_PLAYER_ADDR)
            print 'bind success!'
        except socket.error, msg:
            print 'bind failed!, msg=', msg
            sys.exit(1)

    def ubind(self):
        self.sock.close()

    def send(self, data):
        self.sock.sendall(data)

    def recv(self, data_len):
        return self.sock.recv(data_len)

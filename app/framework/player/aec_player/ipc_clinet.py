# coding:utf-8
import struct
import Queue as queue
import threading
from app.framework.player.aec_player.local_socket_clinet import LocalSocketClint
from app.framework.player.aec_player.process_message import ProcessMessage
import app.framework.player.aec_player.common_params as common_params


class IpcClient(object):
    def __init__(self):
        self.local_socket_client = LocalSocketClint()
        self.local_socket_client.bind()
        self.send_queue = queue.Queue()
        self.recv_queue = queue.Queue()

        self.send_thread_flag = True
        send_thread = threading.Thread(target=self.__send_run)
        send_thread.daemon = True
        send_thread.start()

        self.recv_thread_flag = True
        recv_thread = threading.Thread(target=self.__recv_run)
        recv_thread.daemon = True
        recv_thread.start()

        self.listener_list = []

    def add_listener(self, listener):
        if not callable(listener):
            raise 'listener is not callable!'

        self.listener_list.append(listener)

    def send(self, msg):
        self.send_queue.put(msg)

    def __serialize(self, msg):
        type_int_bytes = struct.pack('i', common_params.TYPE_INT)
        msg.send_data += type_int_bytes

        msg_type_bytes = struct.pack('i', msg.type)
        msg.send_data += msg_type_bytes

        for key in msg.map_str:
            # key
            key_len_bytes = struct.pack('i', len(key))
            msg.send_data += key_len_bytes
            key_type_bytes = struct.pack('i', common_params.TYPE_STRING)
            msg.send_data += key_type_bytes
            msg.send_data += bytes(key)

            # value
            val = msg.map_str[key]
            val_len_bytes = struct.pack('i', len(val))
            msg.send_data += val_len_bytes
            val_type_bytes = struct.pack('i', common_params.TYPE_STRING)
            msg.send_data += val_type_bytes
            msg.send_data += bytes(val)

            print 'key= ', key
            print 'val= ', val

        for key in msg.map_int:
            # key
            key_len_bytes = struct.pack('i', len(key))
            msg.send_data += key_len_bytes
            key_type_bytes = struct.pack('i', common_params.TYPE_STRING)
            msg.send_data += key_type_bytes
            msg.send_data += bytes(key)

            # value
            val = msg.map_int[key]
            val_len_bytes = struct.pack('i', 4)
            msg.send_data += val_len_bytes
            val_type_bytes = struct.pack('i', common_params.TYPE_INT)
            msg.send_data += val_type_bytes
            val_bytes = struct.pack('i', val)
            msg.send_data += val_bytes

        data_len_bytes = struct.pack('i', len(msg.send_data))
        print 'package len= ', len(msg.send_data)
        msg.send_len += data_len_bytes

        send_package_bytes = msg.send_len + msg.send_data
        return send_package_bytes

    def __send_msg(self, msg):
        print '\n\n\nipc send msg:\n\n\n'
        send_data = self.__serialize(msg)
        self.local_socket_client.send(send_data)

    def __send_run(self):
        while self.send_thread_flag:
            msg = self.send_queue.get()
            self.__send_msg(msg)

    def __recv_run(self):
        while self.recv_thread_flag:
            print '\n\n\nipc recv msg:\n\n\n'
            msg = ProcessMessage()
            #read length part in messge
            package_size = self.local_socket_client.recv(4)
            package_size = struct.unpack('i', package_size)[0]
            print 'whole received package size= ', package_size

            #read length of bytes form socked
            package_body = self.local_socket_client.recv(package_size)

            #read the type of packet
            pos = 0
            int_type = package_body[pos:pos + 4]
            pos += 4
            package_type = package_body[pos:pos + 4]
            msg.type = struct.unpack('i', package_type)[0]
            print 'recv msg.type= %d' %(msg.type)
            pos += 4
            while pos < package_size:
                # key
                key_len = struct.unpack('i', package_body[pos:pos + 4])[0]
                pos += 4
                key_type = package_body[pos:pos + 4]
                pos += 4
                key = str(package_body[pos:pos + key_len])
                print 'recv key= ', key
                pos += key_len

                # val
                val_len = struct.unpack('i', package_body[pos:pos + 4])[0]
                pos += 4
                val_type = package_body[pos:pos + 4]
                val_type = struct.unpack('i', val_type)[0]
                pos += 4
                val = package_body[pos:pos + val_len]
                pos += val_len

                if val_type == common_params.TYPE_INT:
                    int_val = struct.unpack('i', val)[0]
                    msg.set_int_params(key, int_val)
                    print 'recv int_val= ', int_val
                elif val_type == common_params.TYPE_STRING:
                    msg.set_str_params(key, str(val))
                    print 'recv string val= ', str(val)

            for listener_callback in self.listener_list:
                listener_callback(msg)

    def __del__(self):
        self.local_socket_client.ubind()
        self.send_thread_flag = False
        self.recv_thread_flag = False

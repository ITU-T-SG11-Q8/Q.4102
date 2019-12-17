import socketserver
import threading
import json

from config import CLIENT_CONFIG
from data.factory import Factory
from classes.peer import Peer
from tcp.tcp_message_server import TcpThreadingSocketServer, TcpMessageHandler


class PublicDataListener:
    def __init__(self, port):
        self._port = port
        self._public_socket_server = None
        self._socket_list = []

    def start(self):
        p_t = threading.Thread(target=self.run_server, args=(), daemon=True)
        p_t.start()

    def run_server(self):
        address = (CLIENT_CONFIG['TCP_SERVER_IP'], self._port)
        self._public_socket_server = TcpThreadingSocketServer(address, PublicDataRequestHandler)
        print("\n[Public Data] Public Listening Port:{0} \n".format(self._port))
        self._public_socket_server.serve_forever()

    def get_public_socket_server(self):
        return self._public_socket_server

    def get_socket_list(self):
        return self._socket_list

    def add_socket(self, sock):
        self._socket_list.append(sock)


class PublicDataRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        socket_ip = self.client_address[0]
        socket_port = self.client_address[1]
        print('\n[Public Data] CONNECT SOCKET'.format(socket_ip, socket_port))
        sock = None
        try:
            sock = self.request
            request_message = self.convert_bytes_to_message(sock)
            public_data_listener = Factory.instance().get_public_data_listener()
            public_data_listener.add_socket(sock)

            while request_message:
                print('\n[Public Data] Received Data')
                Factory.instance().get_web_socket_handler().send_public_data(request_message)
                peer: Peer = Factory.instance().get_peer()
                TcpMessageHandler.send_broadcast_data(peer, request_message)

                request_message = self.convert_bytes_to_message(sock)

        except Exception as e:
            print('\n[Public Data] Error', e)

        print('\n[Public Data] DISCONNECT SOCKET'.format(socket_ip, socket_port))
        sock.close()

    @classmethod
    def convert_bytes_to_message(cls, conn):
        try:
            received_buffer = conn.recv(4)
            bytes_size = int.from_bytes(received_buffer, 'little')
            received_buffer = conn.recv(bytes_size)
            message = json.loads(str(received_buffer, encoding='utf=8'))
            return message
        except Exception as e:
            print('\n[Public Data] Error', e)
            conn.close()
            return None

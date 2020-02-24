import json
import socket


class TcpConnection:
    def __init__(self, ip, port):
        self._ip = ip
        self._port = port
        self._sock = None

    def closed_connection(self):
        if self._sock is not None:
            self._sock.close()
            self._sock = None

    def send_message(self, message):
        send_connection = self.get_connection()
        try:
            if send_connection is not None:
                bytes_body = bytes(json.dumps(message), encoding='utf=8')
                bytes_length = len(bytes_body).to_bytes(4, 'little')
                send_connection.sendall((bytes_length + bytes_body))
                print('[Data Collector] Send Message.')
            else:
                print('[Data Collector] Connection is None.')
        except Exception as e:
            self.closed_connection()
            print('[Data Collector] ', e)

    def get_connection(self):
        try:
            if self._sock is None:
                self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._sock.connect((self._ip, self._port))
        except Exception as e:
            self.closed_connection()
            print(e)

        return self._sock

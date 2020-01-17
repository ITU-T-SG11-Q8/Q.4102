import threading

from simple_websocket_server import WebSocketServer

from config import GUI_CONFIG
from data.factory import Factory
from web_socket.web_socket_handler import WebSocketHandler
from web_socket.web_socket_message_handler import WebSocketMessageHandler


class Hp2pWebSocketServer:
    def __init__(self, port_number):
        self.host = GUI_CONFIG['WEB_SOCKET_HOST']
        self.port = port_number

    def start(self):
        t = threading.Thread(target=self.run_web_socket_server, daemon=True)
        t.start()

    def run_web_socket_server(self):
        print("[SERVER] Start Web Socket Server... {0}:{1}".format(self.host, self.port), flush=True)

        handler = WebSocketMessageHandler()
        Factory.instance().set_web_socket_handler(handler)

        server = WebSocketServer(self.host, self.port, WebSocketHandler)
        Factory.instance().get_web_socket_handler().set_web_socket_server(server)

        server.serve_forever()

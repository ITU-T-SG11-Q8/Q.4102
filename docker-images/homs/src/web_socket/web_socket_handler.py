import json
from simple_websocket_server import WebSocket

from config import LOG_CONFIG
from data.factory import Factory


class WebSocketHandler(WebSocket):
    def handle(self):
        if LOG_CONFIG['PRINT_WEB_SOCKET_LOG']:
            print(self.address, 'message', self.data)
        try:
            data_dic = json.loads(self.data)
            if 'server' in data_dic:
                if data_dic.get('action') == 'hello':
                    Factory.get().get_web_socket_message_handler().append_web_socket_client(self)
                elif data_dic.get('action') == 'get' and data_dic.get('overlay_id') is not None:
                    overlay = Factory.get().get_overlay(data_dic.get('overlay_id'))
                    if overlay is not None:
                        message = Factory.get().get_web_socket_message_handler().create_overlay_cost_map_message(
                            overlay)
                        self.send_message(json.dumps(message))
            else:
                if 'peer_id' in data_dic:
                    peer_id = data_dic.get('peer_id')
                    if data_dic.get('action') == 'hello':
                        Factory.get().get_web_socket_message_handler().add_web_socket_peer(peer_id, self)
                    elif data_dic.get('action') == 'bye':
                        Factory.get().get_web_socket_message_handler().delete_web_socket_peer(self)
                elif 'toid' in data_dic:
                    to_id = data_dic.get('toid')
                    Factory.get().get_web_socket_message_handler().send_message_to_peer(to_id, data_dic)
                else:
                    if LOG_CONFIG['PRINT_WEB_SOCKET_LOG']:
                        print('WebSocket Handler Error...')
        except Exception as e:
            if LOG_CONFIG['PRINT_WEB_SOCKET_LOG']:
                print(e)
            pass

    def connected(self):
        if LOG_CONFIG['PRINT_WEB_SOCKET_LOG']:
            print(self.address, 'connected')

    def handle_close(self):
        if LOG_CONFIG['PRINT_WEB_SOCKET_LOG']:
            print(self.address, 'closed')
        Factory.get().get_web_socket_message_handler().remove_web_socket_client(self)
        Factory.get().get_web_socket_message_handler().delete_web_socket_peer(self)

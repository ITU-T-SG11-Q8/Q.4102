import json

from simple_websocket_server import WebSocket

from service.service import Service


class WebSocketHandler(WebSocket):
    def handle(self):
        print(self.address, 'message', self.data)
        try:
            data_dic = json.loads(self.data)
            if 'server' in data_dic:
                if data_dic.get('action') == 'hello':
                    Service.get().get_web_socket_handler().append_web_socket_client(self)
                elif data_dic.get('action') == 'get' and data_dic.get('overlay_id') is not None:
                    overlay = Service.get().get_overlay(data_dic.get('overlay_id'))
                    if overlay is not None:
                        message = Service.get().get_web_socket_handler().create_overlay_cost_map_message(overlay)
                        self.send_message(json.dumps(message))
            else:
                if 'peer_id' in data_dic:
                    peer_id = data_dic.get('peer_id')
                    if data_dic.get('action') == 'hello':
                        Service.get().get_web_socket_handler().add_web_socket_peer(peer_id, self)
                    elif data_dic.get('action') == 'bye':
                        Service.get().get_web_socket_handler().delete_web_socket_peer(self)
                elif 'toid' in data_dic:
                    to_id = data_dic.get('toid')
                    Service.get().get_web_socket_handler().send_message_to_peer(to_id, data_dic)
                else:
                    print('Error...')
        except:
            pass

    def connected(self):
        print(self.address, 'connected')

    def handle_close(self):
        print(self.address, 'closed')
        Service.get().get_web_socket_handler().remove_web_socket_client(self)
        Service.get().get_web_socket_handler().delete_web_socket_peer(self)

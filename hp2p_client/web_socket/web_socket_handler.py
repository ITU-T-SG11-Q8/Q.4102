import json
import requests
from simple_websocket_server import WebSocket

from data.factory import Factory
from tcp.tcp_message_server import TcpMessageHandler
from config import CLIENT_CONFIG
from classes.constants import RequestPath


class WebSocketHandler(WebSocket):
    def handle(self):
        print(self.address, 'message', self.data)
        try:
            data_dic = json.loads(self.data)
            get_peer = Factory.instance().get_peer()

            if data_dic.get('type') == 'send_data':
                if Factory.instance().is_used_tcp():
                    TcpMessageHandler.send_broadcast_data(get_peer, data_dic.get('data'))
                else:
                    print('webrtc')
            elif data_dic.get('type') == 'scan_tree':
                if Factory.instance().is_used_tcp():
                    TcpMessageHandler.send_scan_tree(get_peer)
                else:
                    print('webrtc')
            elif data_dic.get('type') == 'overlay_costmap':
                param = {
                    'overlay_id': Factory.instance().get_peer().overlay_id
                }
                response = requests.get(CLIENT_CONFIG['HOMS_URL'] + RequestPath.OverlayCostMap, params=param)
                result_data = {'data': None}
                if response.status_code == 200:
                    result_data = response.json()

                if Factory.instance().get_peer().using_web_gui:
                    Factory.instance().get_web_socket_handler().send_overlay_costmap(result_data)
            else:
                print('Error...')
        except:
            pass

    def connected(self):
        print(self.address, 'connected')

    def handle_close(self):
        print(self.address, 'closed')

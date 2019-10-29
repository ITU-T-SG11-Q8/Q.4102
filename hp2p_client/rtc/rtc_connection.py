from rtc.rtcdata import RTCData
from classes.constants import MessageType
from config import PEER_CONFIG, CLIENT_CONFIG
from classes.peer import Peer


class RtcConnection:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self._rtcData = None
        self.join_peer_list = []
        self._connect_server()

        # @self.__event_emitter.on('receive_message')
        # def message_handler(message):
        #     print('\nRtcConnection...', message)
        #     if 'action' in message and message.get('action') == 'hello_peer':
        #         if 'result' in message and not message.get('result'):
        #             peer: Peer = Factory.instance().get_peer()
        #             rtc_connection: RtcConnection = Factory.instance().get_rtc_connection()
        #             rtc_connection.run_send_hello_peer(peer)
        #             return
        #
        #         received_message = message.get('message')
        #         if 'ReqCode' in received_message:
        #             req_code = received_message.get('ReqCode')
        #             if req_code == MessageType.REQUEST_HELLO_PEER:
        #                 peer = received_message.get('ReqParams').get('peer')
        #                 target_peer_id = peer.get('peer_id')
        #                 target_address = peer.get('address')
        #                 target_ticket_id = peer.get('ticket_id')
        #
        #                 rtc_connection: RtcConnection = Factory.instance().get_rtc_connection()
        #                 rtc_connection.send_response_hello_peer(target_peer_id)
        #
        #         elif 'RspCode' in received_message:
        #             rsp_code = received_message.get('RspCode')
        #             if rsp_code == MessageType.RESPONSE_HELLO_PEER:
        #                 print('RECEIVED RESPONSE_HELLO_PEER...')

    def _connect_server(self):
        self._rtcData = RTCData(self.peer_id, 5)
        self._rtcData.connect_signal_server(CLIENT_CONFIG['WEB_SOCKET_SERVER_IP'],
                                            CLIENT_CONFIG['WEB_SOCKET_SERVER_PORT'])

    def close(self):
        self.web_socket_send_bye()
        self._rtcData.close()

    def send(self, message):
        self._rtcData.send_to_server(message)

    def web_socket_send_hello(self):
        bye_message = {
            'action': 'hello',
            'peer_id': self.peer_id
        }
        self.send(bye_message)

    def web_socket_send_bye(self):
        bye_message = {
            'action': 'bye',
            'peer_id': self.peer_id
        }
        self.send(bye_message)

    def run_send_hello_peer(self, peer: Peer):
        if len(self.join_peer_list) > 0:
            peer_info = self.join_peer_list.pop()

            target_peer_id = peer_info.get('peer_id')
            target_address = peer_info.get('address')
            print("Join...", target_peer_id, target_address, flush=True)

            return self.send_hello_peer(peer, target_peer_id)
        else:
            return None

    def web_socket_send_hello_peer(self, peer: Peer, target_peer_id):
        message = self.send_hello_peer(peer, target_peer_id)
        self.send(message)

    def send_hello_peer(self, peer: Peer, target_peer_id):
        hello_peer_message = {
            'action': 'hello_peer',
            'to_peer_id': target_peer_id,
            'message': {
                'ReqCode': MessageType.REQUEST_HELLO_PEER,
                'ReqParams': {
                    'operation': {
                        'overlay_id': peer.overlay_id,
                        'conn_num': PEER_CONFIG['ESTAB_PEER_MAX_COUNT'],
                        'ttl': PEER_CONFIG['PEER_TTL']
                    },
                    'peer': {
                        'peer_id': peer.peer_id,
                        'address': peer.get_address(),
                        'ticket_id': peer.ticket_id
                    }
                }
            }
        }
        return hello_peer_message

    def send_response_hello_peer(self, target_peer_id):
        response_hello_peer_message = {
            'action': 'hello_peer',
            'to_peer_id': target_peer_id,
            'message': {
                'RspCode': MessageType.RESPONSE_HELLO_PEER
            }
        }
        return response_hello_peer_message

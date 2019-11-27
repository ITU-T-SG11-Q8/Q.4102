import threading
import math
import json
import operator
from datetime import datetime

from data.factory import Factory, Peer
from config import CLIENT_CONFIG, PEER_CONFIG
from rtc.rtcdata import RTCData
from classes.constants import MessageType
from homp.homp_message_handler import HompMessageHandler
from data.client_scheduler import ClientScheduler


class RtcHp2pClient:
    def __init__(self):
        self.message_delay = 1
        self.peer: Peer = Factory.instance().get_peer()
        self.handler: HompMessageHandler = Factory.instance().get_homp_handler()
        self._rtc_data = None
        self.join_peer_list = []
        self.fmt = "%Y-%m-%d %H:%M:%S.%f"
        self._s_flag = False
        Factory.instance().set_rtc_hp2p_client(self)

    # WebRtc Message ...
    def set_rtc_data(self, rtc_data: RTCData):
        rtc_data.on('message', self.__on_message)
        rtc_data.on('connection', self.__on_connection)
        self._rtc_data = rtc_data

    def get_rtc_data(self) -> RTCData:
        return self._rtc_data

    def get_peer_manager(self):
        return self.get_rtc_data().get_collection()

    def connection_to_peer(self, peer_id, ticket_id):
        self.get_rtc_data().connect_to_peer(peer_id, ticket_id)

    def send_report(self):
        self.handler.report(self.peer, self.get_peer_manager())

    def reassignment_connections_for_recovery(self, peer_id, ticket_id):
        return self.get_peer_manager().get_in_candidate_remove_peer_id(peer_id, ticket_id)

    def __on_connection(self, sender):
        self.send_report()
        if sender.is_outgoing:
            if sender.isDataChannelOpened:
                print('[OutGoing] Connection Open => ', sender.connectedId)
            else:
                print('[OutGoing] Connection Closed => ', sender.connectedId)
        else:
            if sender.isDataChannelOpened:
                # threading.Timer(self.message_delay + 1, self.send_estab_peer, [sender.connectedId]).start()
                self.send_estab_peer(sender.connectedId)
                print('[InComing] Connection Open => ', sender.connectedId)
            else:
                print('[InComing] Connection Closed => ', sender.connectedId)

    def __on_message(self, sender, msg):
        print('\nRtcHp2pClient sender => ', sender.connectedId)
        request_message = json.loads(msg)

        if 'ReqCode' in request_message:
            req_code = request_message.get('ReqCode')
            if MessageType.REQUEST_HELLO_PEER == req_code:
                self.received_hello_peer(request_message)
            elif MessageType.REQUEST_ESTAB_PEER == req_code:
                # threading.Timer(self.message_delay, self.received_estab_peer, [sender, request_message]).start()
                self.received_estab_peer(sender, request_message)
            elif MessageType.REQUEST_PROBE_PEER == req_code:
                self.received_probe_peer(sender, request_message)
            elif MessageType.REQUEST_SET_PRIMARY == req_code:
                self.received_set_primary(sender)
            elif MessageType.REQUEST_SET_CANDIDATE == req_code:
                self.received_set_candidate(sender)
            elif MessageType.REQUEST_BROADCAST_DATA == req_code:
                self.received_broadcast_data(sender, request_message)
            elif MessageType.REQUEST_RELEASE_PEER == req_code:
                self.received_release_peer(sender, request_message)
            elif MessageType.REQUEST_HEARTBEAT == req_code:
                self.received_heartbeat(sender)

        elif 'RspCode' in request_message:
            rsp_code = request_message.get('RspCode')
            if MessageType.RESPONSE_HELLO_PEER == rsp_code:
                self.received_response_hello_peer(request_message)
            elif MessageType.RESPONSE_ESTAB_PEER == rsp_code:
                self.received_response_estab_peer(sender, True)
            elif MessageType.RESPONSE_ESTAB_PEER_ERROR == rsp_code:
                self.received_response_estab_peer(sender, False)
            elif MessageType.RESPONSE_PROBE_PEER == rsp_code:
                self.received_response_probe_peer(sender, request_message)
            elif MessageType.RESPONSE_SET_PRIMARY == rsp_code:
                self.received_response_set_primary(sender, True)
            elif MessageType.RESPONSE_SET_PRIMARY_ERROR == rsp_code:
                self.received_response_set_primary(sender, False)
            elif MessageType.RESPONSE_SET_CANDIDATE == rsp_code:
                self.received_response_set_candidate(sender)
            elif MessageType.RESPONSE_BROADCAST_DATA == rsp_code:
                self.received_response_broadcast_data(sender.connectedId)
            elif MessageType.RESPONSE_RELEASE_PEER == rsp_code:
                self.received_response_release_peer(sender)
            elif MessageType.RESPONSE_HEARTBEAT == rsp_code:
                self.received_response_heartbeat(sender)

    # Received Message ...
    def received_hello_peer(self, received_message):
        print('\n++++++++[HOPP] RECEIVED REQUEST_HELLO_PEER...')
        target_peer = received_message.get('ReqParams').get('peer')
        target_peer_id = target_peer.get('peer_id')
        target_ticket_id = target_peer.get('ticket_id')
        target_address = target_peer.get('address')

        response_hello_peer_message = {
            'action': 'hello_peer',
            'to_peer_id': target_peer_id,
            'message': {
                'RspCode': MessageType.RESPONSE_HELLO_PEER
            }
        }
        self.send_to_server(response_hello_peer_message)
        operation = received_message.get('ReqParams').get('operation')
        conn_num = operation.get('conn_num')
        ttl = operation.get('ttl')
        recovery = operation.get('recovery') if 'recovery' in operation else False

        if conn_num < 1 or ttl < 1:
            return

        children_count = self.get_peer_manager().get_children_count()
        is_assignment = self.get_peer_manager().assignment_peer(target_peer_id)
        if not recovery:
            if children_count > 0:
                operation['ttl'] = ttl - 1
                new_conn_num = conn_num - (1 if is_assignment else 0)

                if new_conn_num > 0:
                    operation['conn_num'] = math.ceil(new_conn_num / children_count)

                    print('\n++++++++[HOPP] HELLO_PEER REQUEST !!!BROADCAST!!!', received_message)
                    self.get_rtc_data().send_broadcast_message_to_children(received_message)

            if is_assignment:
                # threading.Timer(self.message_delay, self.connection_to_peer, [target_peer_id, target_ticket_id]).start()
                self.connection_to_peer(target_peer_id, target_ticket_id)
        else:
            if target_ticket_id <= self.peer.ticket_id:
                print('\n++++++++[HOPP] RECOVERY ==  target_ticket_id.... bigger than me', received_message)
                return

            print('\n++++++++[HOPP] RECOVERY == HELLO_PEER', target_peer_id)
            is_assignment_recovery = True
            if not is_assignment:
                is_assignment_recovery = False
                remove_peer_id = self.reassignment_connections_for_recovery(target_peer_id, target_ticket_id)
                if remove_peer_id is not None:
                    is_assignment_recovery = True
                    self.send_release_peer(remove_peer_id, False)

            if children_count > 0:
                operation['ttl'] = ttl - 1
                new_conn_num = conn_num - (1 if is_assignment_recovery else 0)

                if new_conn_num > 0:
                    operation['conn_num'] = math.ceil(new_conn_num / children_count)

                    print('\n++++++++[HOPP] RECOVERY ==  HELLO_PEER REQUEST !!!BROADCAST!!!', received_message)
                    self.get_rtc_data().send_broadcast_message_to_children(received_message)

            if is_assignment_recovery:
                # threading.Timer(self.message_delay, self.connection_to_peer, [target_peer_id, target_ticket_id]).start()
                self.connection_to_peer(target_peer_id, target_ticket_id)

        self.send_report()

    def received_response_hello_peer(self, is_estab=False):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_HELLO_PEER...')
        if is_estab:
            self.run_estab_peer_timer()

    def run_estab_peer_timer(self):
        print('\n++++++++[HOPP] RUN_ESTAB_PEER_TIMER')
        threading.Timer(PEER_CONFIG['ESTAB_PEER_TIMEOUT'], self.send_to_all_probe_peer).start()

    def received_estab_peer(self, sender, request_message):
        print('\n++++++++[HOPP] RECEIVED ESTAB_PEER REQUEST')
        received_message = request_message.get('ReqParams')
        # target_overlay_id = received_message.get('operation').get('overlay_id')
        target_peer_id = received_message.get('peer').get('peer_id')
        target_ticket_id = received_message.get('peer').get('ticket_id')
        estab_response_message = {
            'RspCode': MessageType.RESPONSE_ESTAB_PEER_ERROR
        }

        is_established = False

        if not self.get_peer_manager().is_run_probe_peer:
            is_established = self.get_peer_manager().establish_peer(target_peer_id)
            if is_established:
                estab_response_message['RspCode'] = MessageType.RESPONSE_ESTAB_PEER
                self.send_report()
            else:
                self.send_to_all_probe_peer()

        if is_established:
            print('\n++++++++[HOPP] SEND ESTAB_PEER RESPONSE', estab_response_message)
            self.get_rtc_data().send(target_peer_id, estab_response_message)
        else:
            self.send_release_peer(sender)

    def received_response_estab_peer(self, sender, is_success):
        if is_success:
            print('\n++++++++[HOPP] RECEIVED RESPONSE_ESTAB_PEER ')
        else:
            print('\n++++++++[HOPP] ERROR RECEIVED RESPONSE_ESTAB_PEER ', sender.connectedId)
            self.get_peer_manager().un_assignment_peer(sender.connectedId)
            # threading.Timer(self.message_delay, self.get_rtc_data().disconnect_to_peer, [sender]).start()
            self.get_rtc_data().disconnect_to_peer(sender)

    def received_probe_peer(self, sender, request_message):
        print('\n++++++++[HOPP] RECEIVED PROBE_PEER')
        probe_response_message = {
            'RspCode': MessageType.RESPONSE_PROBE_PEER,
            'RspParams': {
                'operation': {
                    'ntp_time': request_message.get('ReqParams').get('operation').get('ntp_time')
                }
            }
        }
        print('\n++++++++[HOPP] SEND PROBE_PEE RESPONSE', probe_response_message)
        # threading.Timer(self.message_delay, self.get_rtc_data().send,
        #                 [sender.connectedId, probe_response_message]).start()
        self.get_rtc_data().send(sender.connectedId, probe_response_message)

    def received_response_probe_peer(self, sender, response_message):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_PROBE_PEER ')
        send_time = datetime.strptime(response_message.get('RspParams').get('operation').get('ntp_time'),
                                      self.fmt)
        now_time = datetime.strptime(str(datetime.now()), self.fmt)
        delta_time = now_time - send_time
        probe_time = delta_time.seconds * 1000000 + delta_time.microseconds
        self.get_peer_manager().estab_peers[sender.connectedId] = probe_time

    def received_set_primary(self, sender):
        print('\n++++++++[HOPP] RECEIVED SET_PRIMARY', sender.connectedId)
        result_set_primary = self.get_peer_manager().set_primary_peer(sender.connectedId, not sender.is_parent)

        primary_response_message = {
            'RspCode': MessageType.RESPONSE_SET_PRIMARY_ERROR
        }
        if result_set_primary:
            primary_response_message['RspCode'] = MessageType.RESPONSE_SET_PRIMARY

        print('\n++++++++[HOPP] SEND SET_PRIMARY RESPONSE', primary_response_message)
        # threading.Timer(self.message_delay, self.get_rtc_data().send,
        #                 [sender.connectedId, primary_response_message]).start()
        self.get_rtc_data().send(sender.connectedId, primary_response_message)

        if result_set_primary:
            self.send_report()

    def received_response_set_primary(self, sender, is_success):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY ', sender.connectedId)
        if self.get_peer_manager().is_run_primary_peer:
            if is_success:
                self.get_peer_manager().set_primary_peer(sender.connectedId, not sender.is_parent)
                self.send_report()
                self.send_to_all_set_candidate()  # optional
                # self.get_peer_manager().is_run_primary_peer = False  # send_to_all_set_candidate 미사용시 활성화
            else:
                self.check_and_send_set_primary()
        else:
            if is_success:
                self.get_peer_manager().set_primary_peer(sender.connectedId, not sender.is_parent)
                self.send_report()
            else:
                self.recovery_connection()

    def received_set_candidate(self, sender):
        print('\n++++++++[HOPP] RECEIVED SET_CANDIDATE ', sender.connectedId)

        candidate_response_message = {
            'RspCode': MessageType.RESPONSE_SET_CANDIDATE
        }
        print('\n++++++++[HOPP] SEND SET_CANDIDATE RESPONSE', candidate_response_message)
        # threading.Timer(self.message_delay, self.get_rtc_data().send,
        #                 [sender.connectedId, candidate_response_message]).start()
        self.get_rtc_data().send(sender.connectedId, candidate_response_message)
        self.send_report()

    def received_response_set_candidate(self, sender):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_CANDIDATE ', sender.connectedId)
        self.send_report()

    def received_broadcast_data(self, sender, request_message):
        print('\n++++++++[HOPP] RECEIVED BROADCAST_DATA ', sender.connectedId)

        request_params = request_message.get('ReqParams')
        source_peer = request_params.get('peer').get('peer_id')
        payload = request_message.get('payload')
        print_message = '\n++++++++[HOPP] SENDER:{0} / SOURCE:{1} / DATA=>{2}'
        print(print_message.format(sender.connectedId, source_peer, payload))

        if request_params.get('ack'):
            broadcast_data_response_message = {
                'RspCode': MessageType.RESPONSE_BROADCAST_DATA
            }
            print('\n++++++++[HOPP] SEND BROADCAST_DATA RESPONSE', broadcast_data_response_message)
            # threading.Timer(self.message_delay, self.get_rtc_data().send,
            #                 [sender.connectedId, broadcast_data_response_message]).start()
            self.get_rtc_data().send(sender.connectedId, broadcast_data_response_message)

        if source_peer != self.peer.peer_id:
            self.relay_broadcast_data(sender, request_message)

    def received_response_broadcast_data(self, to_peer_id):
        print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_BROADCAST_DATA ', to_peer_id)

    def relay_broadcast_data(self, sender, request_message):
        print('\n++++++++[HOPP] RELAY BROADCAST_DATA REQUEST')
        self.get_rtc_data().send_broadcast_message_other(sender.connectedId, request_message)

    def received_release_peer(self, sender, request_message):
        print('\n++++++++[HOPP] RECEIVED RELEASE_PEER ', sender.connectedId)

        if request_message.get('ReqParams').get('operation').get('ack'):
            release_response_message = {
                'RspCode': MessageType.RESPONSE_RELEASE_PEER
            }
            print('\n++++++++[HOPP] SEND RELEASE_PEER RESPONSE', release_response_message)
            # threading.Timer(self.message_delay, self.get_rtc_data().send,
            #                 [sender.connectedId, release_response_message]).start()
            self.get_rtc_data().send(sender.connectedId, release_response_message)
        else:
            self.get_rtc_data().disconnect_to_peer(sender.connectedId)

    def received_response_release_peer(self, sender):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_RELEASE_PEER ', sender.connectedId)
        self.get_rtc_data().disconnect_to_peer(sender.connectedId)

    def recovery_connection(self):
        print('\n++++++++[HOPP] START Recovery Connection...')
        peers = self.get_peer_manager().get_all_peer_connection()

        new_primary_peer_id = None
        for connection in peers.values():
            if connection.ticket_id < self.peer.ticket_id and connection.is_parent:
                if connection.priority is not None:
                    connection.priority = connection.priority - 1
                    if connection.priority == 0:
                        new_primary_peer_id = connection.connectedId
                else:
                    print('\n++++++++[HOPP] Connection priority Error....')

        if new_primary_peer_id is not None:
            self.send_set_primary(new_primary_peer_id)
        else:
            self.recovery_join()

    def recovery_join(self):
        print('\n++++++++[HOPP] SEND RECOVERY HELLO')
        self.get_peer_manager().is_run_probe_peer = False
        self.get_peer_manager().is_run_primary_peer = False

        recovery_response = self.handler.recovery(self.peer)

        if recovery_response is None:
            print('\n++++++++[HOPP] Failed RECOVERY JOIN')
        else:
            if len(recovery_response) > 0:
                self.join_peer_list = recovery_response
                self.run_send_hello_peer(True)
            else:
                self.send_report()
                print('Peer List is None (RECOVERY JOIN)')

    def received_heartbeat(self, sender):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n++++++++[HOPP] RECEIVED HEARTBEAT ', sender.connectedId)

        if sender is not None:
            sender.update_time = datetime.now()
            release_response_message = {
                'RspCode': MessageType.RESPONSE_HEARTBEAT
            }
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n++++++++[HOPP] SEND HEARTBEAT RESPONSE', release_response_message)

            # threading.Timer(self.message_delay, self.get_rtc_data().send,
            #                 [sender.connectedId, release_response_message]).start()
            self.get_rtc_data().send(sender.connectedId, release_response_message)

    def received_response_heartbeat(self, sender):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n++++++++[HOPP] RECEIVED RESPONSE_HEARTBEAT ', sender.connectedId)

        if sender is not None:
            sender.update_time = datetime.now()

    # Send Message ...
    def send_hello_peer(self, target_peer_id):
        hello_peer_message = {
            'action': 'hello_peer',
            'to_peer_id': target_peer_id,
            'message': {
                'ReqCode': MessageType.REQUEST_HELLO_PEER,
                'ReqParams': {
                    'operation': {
                        'overlay_id': self.peer.overlay_id,
                        'conn_num': PEER_CONFIG['ESTAB_PEER_MAX_COUNT'],
                        'ttl': PEER_CONFIG['PEER_TTL']
                    },
                    'peer': {
                        'peer_id': self.peer.peer_id,
                        'address': self.peer.get_address(),
                        'ticket_id': self.peer.ticket_id
                    }
                }
            }
        }
        self.send_to_server(hello_peer_message)

    def send_recovery_hello_peer(self, target_peer_id):
        hello_recovery_message = {
            'action': 'hello_peer',
            'to_peer_id': target_peer_id,
            'message': {
                'ReqCode': MessageType.REQUEST_HELLO_PEER,
                'ReqParams': {
                    'operation': {
                        'overlay_id': self.peer.overlay_id,
                        'conn_num': PEER_CONFIG['ESTAB_PEER_MAX_COUNT'],
                        'ttl': PEER_CONFIG['PEER_TTL'],
                        'recovery': True
                    },
                    'peer': {
                        'peer_id': self.peer.peer_id,
                        'address': self.peer.get_address(),
                        'ticket_id': self.peer.ticket_id
                    }
                }
            }
        }
        self.send_to_server(hello_recovery_message)

    def send_estab_peer(self, to_peer_id):
        establish_message = {
            'ReqCode': MessageType.REQUEST_ESTAB_PEER,
            'ReqParams': {
                'operation': {
                    'overlay_id': self.peer.overlay_id
                },
                'peer': {
                    'peer_id': self.peer.peer_id,
                    'ticket_id': self.peer.ticket_id
                }
            }
        }

        print('\n++++++++[HOPP] SEND ESTABLISH REQUEST', establish_message)
        self.get_rtc_data().send(to_peer_id, establish_message)

    def send_to_all_probe_peer(self):
        if not self.get_peer_manager().is_run_probe_peer:
            print('\n++++++++[HOPP] SEND TO ALL PROBE_PEER')
            self.get_peer_manager().is_run_probe_peer = True
            estab_peers = self.get_peer_manager().get_estab_peers()

            if len(estab_peers) > 0:
                # delay_count = 0
                for peer_id in estab_peers.keys():
                    # delay_count = delay_count + 1
                    # threading.Timer(delay_count * 0.5, self.send_probe_peer, [peer_id]).start()
                    self.send_probe_peer(peer_id)

                self.run_probe_peer_timer()
            else:
                print('\n++++++++[HOPP] ESTAB_PEER is None...')

    def send_probe_peer(self, to_peer_id):
        probe_message = {
            'ReqCode': MessageType.REQUEST_PROBE_PEER,
            'ReqParams': {
                'operation': {
                    'ntp_time': str(datetime.now())
                }
            }
        }
        print('\n++++++++[HOPP] SEND PROBE_PEER REQUEST', probe_message)
        self.get_rtc_data().send(to_peer_id, probe_message)

    def run_probe_peer_timer(self):
        print('\n++++++++[HOPP] RUN_PROBE_PEER_TIMER')
        threading.Timer(PEER_CONFIG['PROBE_PEER_TIMEOUT'], self.check_and_send_set_primary).start()

    def check_and_send_set_primary(self):
        self.get_peer_manager().is_run_primary_peer = True

        print('\n++++++++[HOPP] CHECK AND SEND SET_PRIMARY')
        if len(self.get_peer_manager().estab_peers) < 1:
            print('\n++++++++[HOPP] Error... ESTAB_PEERS len = 0')
            return

        sorted_estab_peers = sorted(self.get_peer_manager().estab_peers.items(), key=operator.itemgetter(1))

        primary_peer_id = None
        for estab_index, (peer_id, delta_time) in enumerate(sorted_estab_peers):
            connection = self.get_peer_manager().get_peer_connection(peer_id)
            connection.priority = estab_index
            if estab_index == 0:
                primary_peer_id = peer_id

        if primary_peer_id is not None:
            del self.get_peer_manager().estab_peers[primary_peer_id]
            self.send_set_primary(primary_peer_id)

    def send_set_primary(self, to_peer_id):
        primary_message = {
            'ReqCode': MessageType.REQUEST_SET_PRIMARY
        }
        print('\n++++++++[HOPP] SEND SET_PRIMARY REQUEST', primary_message)
        self.get_rtc_data().send(to_peer_id, primary_message)

    def send_to_all_set_candidate(self):
        print('\n++++++++[HOPP] SEND TO ALL SET CANDIDATE')
        self.get_peer_manager().is_run_primary_peer = False

        if len(self.get_peer_manager().estab_peers) > 0:
            # delay_count = 0
            for peer_id in self.get_peer_manager().estab_peers.keys():
                # delay_count = delay_count + 1
                # threading.Timer(delay_count * 0.5, self.send_set_candidate, [peer_id]).start()
                self.send_set_candidate(peer_id)

        self.get_peer_manager().estab_peers.clear()

    def send_set_candidate(self, to_peer_id):
        # TODO => 직접 사용할 경우 self.send_report() 를 해야된다.
        candidate_message = {
            'ReqCode': MessageType.REQUEST_SET_CANDIDATE
        }
        print('\n++++++++[HOPP] SEND SET_CANDIDATE REQUEST', candidate_message)
        self.get_rtc_data().send(to_peer_id, candidate_message)

    def send_broadcast_data(self, send_data, is_ack=None):
        operation_ack = is_ack if is_ack is not None else PEER_CONFIG['BROADCAST_OPERATION_ACK']
        # TODO 수정 필요함.
        data_message = {
            'ReqCode': MessageType.REQUEST_BROADCAST_DATA,
            'ReqParams': {
                'operation': {
                    'ack': operation_ack
                },
                'peer': {
                    'peer_id': self.peer.peer_id
                },
                'payload': {
                    'length': len(send_data),
                    'type': 'text/plain'
                }
            },
            'payload': send_data
        }

        print('\n++++++++[HOPP] SEND BROADCAST_DATA REQUEST', data_message)
        self.get_rtc_data().send_broadcast_message(data_message)

    def send_release_peer(self, sender, is_ack=None):
        print('\n++++++++[HOPP] SEND RELEASE PEER')
        operation_ack = is_ack if is_ack is not None else PEER_CONFIG['RELEASE_OPERATION_ACK']
        release_message = {
            'ReqCode': MessageType.REQUEST_RELEASE_PEER,
            'ReqParams': {
                'operation': {
                    'ack': operation_ack
                }
            }
        }

        self.get_rtc_data().send(sender.connectedId, release_message)
        self.get_rtc_data().disconnect_to_peer(sender.connectedId)

    def send_to_all_release_peer(self):
        self.get_peer_manager().is_destroy = True
        peers = self.get_peer_manager().get_all_peer_connection()
        operation_ack = PEER_CONFIG['RELEASE_OPERATION_ACK']

        if len(peers) > 0:
            release_message = {
                'ReqCode': MessageType.REQUEST_RELEASE_PEER,
                'ReqParams': {
                    'operation': {
                        'ack': operation_ack
                    }
                }
            }
            print('\n++++++++[HOPP] SEND TO ALL RELEASE_PEER REQUEST', release_message)

            # if len(estab_peers) > 0:
            #     delay_count = 0
            #     for peer_id in estab_peers.keys():
            #         delay_count = delay_count + 1
            #         threading.Timer(delay_count * 0.5, self.send_probe_peer, [peer_id]).start()
            #
            #     self.run_probe_peer_timer()
            #
            # peer_list = list(peers.keys())
            # for peer_id in peer_list:
            #     connection: PeerConnection = peers[peer_id]
            #     connection.connection.send(request_message)
            #     if not operation_ack:
            #         connection.connection.close()

    # WebSocket Message...
    def run_send_hello_peer(self, is_recovery=False):
        if len(self.join_peer_list) > 0:
            peer_info = self.join_peer_list.pop()
            target_peer_id = peer_info.get('peer_id')
            target_address = peer_info.get('address')
            print("Join...", target_peer_id, target_address, flush=True)
            if not is_recovery:
                self.send_hello_peer(target_peer_id)
            else:
                self.send_recovery_hello_peer(target_peer_id)

    def close(self):
        self.web_socket_send_bye()
        self.get_rtc_data().close()

    def send_to_server(self, message):
        print('send message: ', message)
        # TODO 웹소켓 확인
        # threading.Timer(self.message_delay, self.send_to_server, [response_hello_peer_message]).start()
        self.get_rtc_data().send_to_server(message)

    def _send(self, message):
        print('send message: ', message)
        self.get_rtc_data().send_to_server(message)

    def web_socket_send_hello(self):
        bye_message = {
            'action': 'hello',
            'peer_id': self.peer.peer_id
        }
        self._send(bye_message)

    def web_socket_send_bye(self):
        bye_message = {
            'action': 'bye',
            'peer_id': self.peer.peer_id
        }
        self._send(bye_message)

    # Client function ...
    def client_start(self):
        web_socket_ip = CLIENT_CONFIG['WEB_SOCKET_SERVER_IP']
        web_socket_port = CLIENT_CONFIG['WEB_SOCKET_SERVER_PORT']
        self.peer.set_web_socket_server_info(web_socket_ip, web_socket_port)

        self.set_rtc_data(RTCData(self.peer.peer_id))
        self.get_rtc_data().connect_signal_server(web_socket_ip, web_socket_port)
        self.web_socket_send_hello()

        scheduler = ClientScheduler()
        scheduler.start()
        Factory.instance().set_client_scheduler(scheduler)

        threading.Timer(1, self.run_auto_client).start()

    def run_auto_client(self):
        print('run_auto_client')
        self.auto_creation_and_join()
        self.process_client()

    def auto_creation_and_join(self):
        if self.peer.isOwner:
            self.handler.creation(self.peer)
            self.handler.join(self.peer)
            self.get_rtc_data().set_ticket_id(self.peer.ticket_id)
            self.send_report()
            self.handler.modification(self.peer)

            # TODO 요기
            # self.run_expires_scheduler(self.peer.peer_expires)
            # TcpMessageHandler.run_heartbeat_scheduler()
        else:
            if self.peer.overlay_id is None:
                overlay_list = self.handler.query()
                if len(overlay_list) > 0:
                    overlay = overlay_list[len(overlay_list) - 1]
                    self.peer.overlay_id = overlay.get('overlay_id')
                else:
                    print('overlay List is None')
                    return

            join_response = self.handler.join(self.peer)
            self.get_rtc_data().set_ticket_id(self.peer.ticket_id)

            if join_response is None:
                print('filed join...')
            else:
                # TODO => rtc run_heartbeat_scheduler -> TcpMessageHandler.run_heartbeat_scheduler()
                if len(join_response) > 0:
                    self.join_peer_list = join_response
                    self.run_send_hello_peer()
                else:
                    self.send_report()
                    print('Peer List is None')

    def process_client(self):
        try:
            if self.peer.overlay_id is None:
                return

            while True:
                if self.peer.overlay_id is None:
                    input_method = input("\n작업 선택 (연결상태 확인:1, 종료:0) =>")
                else:
                    input_method = input("\n작업 선택 (연결상태 확인:1, 데이터 전송:2, 채널 탈퇴:3, 종료:0) =>")

                if input_method.lower() == '0':  # 종료
                    break

                elif input_method.lower() == '1':  # 연결상태 확인
                    print(
                        '\n*******************************************************************************************')
                    print('Peer ID => {0}   &&&   Ticket ID => {1}'.format(self.peer.peer_id, self.peer.ticket_id))
                    print('PRIMARY_LIST', self.get_peer_manager().primary_list)
                    print('IN_CANDIDATE_LIST', self.get_peer_manager().in_candidate_list)
                    print('OUT_CANDIDATE_LIST', self.get_peer_manager().out_candidate_list)
                    print(
                        '*******************************************************************************************\n')

                elif input_method.lower() == '2' and self.peer.overlay_id is not None:  # 데이터 전송
                    send_data = input("데이터 입력 =>")
                    self.send_broadcast_data(send_data)
                    ## TcpMessageHandler.send_broadcast_data(self.peer, send_data)

                elif input_method.lower() == '3' and self.peer.overlay_id is not None:  # 채널 탈퇴
                    self.handler.leave(self.peer)
                    ## TcpMessageHandler.send_to_all_release_peer()

                elif input_method.lower() == '':
                    print("")

                else:
                    print("잘못된 입력입니다.")
        except Exception as e:
            print(e)
        finally:
            ## TcpMessageHandler.send_to_all_release_peer()
            self.handler.leave(self.peer)
            # TODO => homp_handler.modification(peer) stop timer expires

            scheduler = Factory.instance().get_heartbeat_scheduler()
            if scheduler is not None:
                scheduler.stop()
                Factory.instance().set_heartbeat_scheduler(None)

            print("__END__")

    def run_expires_scheduler(self, interval):
        self._s_flag = False
        scheduler: ClientScheduler = Factory.instance().get_client_scheduler()
        scheduler.append_expires_scheduler(int(interval / 2), self.send_overlay_refresh)

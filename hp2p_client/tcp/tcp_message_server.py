import socketserver
import threading
import math
import socket
import json
import operator
from datetime import datetime

from data.factory import Factory, Peer, HompMessageHandler
from heartbeat_scheduler import HeartScheduler
from classes.constants import MessageType
from config import PEER_CONFIG
from classes.hopp_message import HoppMessage
from data.tcp_peer_connection_manager import TcpPeerConnectionManager, PeerConnection


class TcpMessageHandler(socketserver.BaseRequestHandler):
    peer_manager = TcpPeerConnectionManager()
    Factory.instance().set_peer_manager(peer_manager)
    peer: Peer = Factory.instance().get_peer()

    _byteorder = 'little'
    _encoding = 'utf=8'
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    __this__ = None
    print('\n++++++++[HOPP] CREATE TcpMessageHandler')

    def handle(self):
        print('\n++++++++[HOPP] [{0}:{1}] OUT_GOING CONNECT SOCKET'.format(self.client_address[0],
                                                                           self.client_address[1]))
        socket_ip = self.client_address[0]
        socket_port = self.client_address[1]
        socket_peer_id = None

        try:
            sock = self.request
            is_out_going = True
            request_message = self.convert_bytes_to_message(sock)

            while request_message:
                # print('\n++++++++[HOPP] OUT_GOING RECEIVED', request_message.header)
                socket_peer_id = self.peer_manager.get_peer_id_by_connection(sock)

                # HELLO_PEER
                if MessageType.REQUEST_HELLO_PEER == request_message.message_type:
                    self.received_hello_peer(sock, request_message)
                    if socket_peer_id is None:
                        sock.close()
                        break

                elif MessageType.RESPONSE_HELLO_PEER == request_message.message_type:
                    self.received_response_hello_peer(is_out_going, socket_peer_id)

                # ESTAB_PEER
                elif MessageType.REQUEST_ESTAB_PEER == request_message.message_type:
                    is_established = self.received_estab_peer(sock, request_message)
                    if not is_established:
                        sock.close()
                        break

                elif MessageType.RESPONSE_ESTAB_PEER == request_message.message_type or \
                        MessageType.RESPONSE_ESTAB_PEER_ERROR == request_message.message_type:
                    self.received_response_estab_peer(request_message.message_type, is_out_going, socket_peer_id)

                # PROBE_PEER
                elif MessageType.REQUEST_PROBE_PEER == request_message.message_type:
                    self.received_probe_peer(sock, request_message, is_out_going)

                elif MessageType.RESPONSE_PROBE_PEER == request_message.message_type:
                    self.received_response_probe_peer(request_message, is_out_going, socket_peer_id)

                # SET_PRIMARY
                elif MessageType.REQUEST_SET_PRIMARY == request_message.message_type:
                    self.received_set_primary(sock, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_SET_PRIMARY == request_message.message_type or \
                        MessageType.RESPONSE_SET_PRIMARY_ERROR == request_message.message_type:
                    self.received_response_set_primary(request_message.message_type, is_out_going, socket_peer_id)

                # SET_CANDIDATE
                elif MessageType.REQUEST_SET_CANDIDATE == request_message.message_type:
                    self.received_set_candidate(sock, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_SET_CANDIDATE == request_message.message_type:
                    self.received_response_set_candidate(is_out_going, socket_peer_id)

                # BROADCAST_DATA
                elif MessageType.REQUEST_BROADCAST_DATA == request_message.message_type:
                    self.received_broadcast_data(sock, request_message, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_BROADCAST_DATA == request_message.message_type:
                    self.received_response_broadcast_data(is_out_going, socket_peer_id)

                # RELEASE_PEER
                elif MessageType.REQUEST_RELEASE_PEER == request_message.message_type:
                    self.received_release_peer(sock, request_message, is_out_going, socket_peer_id)
                    break

                elif MessageType.RESPONSE_RELEASE_PEER == request_message.message_type:
                    self.received_response_release_peer(sock, is_out_going, socket_peer_id)
                    break

                # HEARTBEAT
                elif MessageType.REQUEST_HEARTBEAT == request_message.message_type:
                    self.received_heartbeat(sock, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_HEARTBEAT == request_message.message_type:
                    self.received_response_heartbeat(is_out_going, socket_peer_id)

                request_message = self.convert_bytes_to_message(sock)

        except Exception as e:
            print('\n++++++++[HOPP] OUT_GOING Error\n', e)

        print('\n++++++++[HOPP] [{0}:{1}] OUT_GOING DISCONNECT SOCKET'.format(socket_ip, socket_port))
        self.clear_connection(socket_peer_id, is_out_going)

    @classmethod
    def get_peer_id_by_connection(cls, sock):
        peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        return peer_manager.get_peer_id_by_connection(sock)

    @classmethod
    def convert_bytes_to_message(cls, conn):
        try:
            message = HoppMessage()

            received_buffer = conn.recv(1)
            message.version = int.from_bytes(received_buffer, cls._byteorder)

            received_buffer = conn.recv(1)
            message.type = int.from_bytes(received_buffer, cls._byteorder)

            received_buffer = conn.recv(2)
            message.length = int.from_bytes(received_buffer, cls._byteorder)

            received_buffer = conn.recv(message.length)
            message.header = json.loads(str(received_buffer, encoding=cls._encoding))

            if 'ReqCode' in message.header:
                message.message_type = message.header.get('ReqCode')
            elif 'RspCode' in message.header:
                message.message_type = message.header.get('RspCode')
            else:
                return None

            if message.message_type == MessageType.REQUEST_BROADCAST_DATA:
                content_length = message.header.get('ReqParams').get('payload').get('length')
                received_buffer = conn.recv(content_length)
                message.content = str(received_buffer, encoding=cls._encoding)

            return message
        except Exception as e:
            print('\n++++++++[HOPP] Error convert_bytes_to_message\n', e)
            return None

    @classmethod
    def convert_to_bytes(cls, data):
        try:
            bytes_data = bytes(data, encoding=cls._encoding)
            return bytes_data
        except Exception as e:
            print('\n++++++++[HOPP] Error convert_data_to_bytes\n', e)
            return None

    @classmethod
    def convert_data_to_bytes(cls, data):
        try:
            bytes_data = bytes(data, encoding=cls._encoding)
            bytes_length = len(bytes_data)
            return bytes_data, bytes_length
        except Exception as e:
            print('\n++++++++[HOPP] Error convert_data_to_bytes\n', e)
            return None

    @classmethod
    def convert_message_to_bytes(cls, message, bytes_data=None):
        try:
            bytes_version = MessageType.VERSION.to_bytes(1, cls._byteorder)
            bytes_type = MessageType.TYPE.to_bytes(1, cls._byteorder)
            bytes_header = bytes(json.dumps(message), encoding=cls._encoding)
            bytes_length = len(bytes_header).to_bytes(2, cls._byteorder)
            if bytes_data is None:
                return bytes_version + bytes_type + bytes_length + bytes_header
            else:
                return bytes_version + bytes_type + bytes_length + bytes_header + bytes_data
        except Exception as e:
            print('\n++++++++[HOPP] Error convert_message_to_bytes\n', e)
            return None

    def send_report(self):
        handler: HompMessageHandler = Factory.instance().get_homp_handler()
        handler.report(self.peer, self.peer_manager)

    def clear_connection(self, peer_id, is_out_going):
        if peer_id is None:
            return

        if is_out_going:
            print('\n++++++++[HOPP] OUT_GOING *********** CLEAR', peer_id)
        else:
            print('\n++++++++[HOPP] IN_COMING ************ CLEAR', peer_id)

        if self.peer_manager.is_destroy:
            self.peer_manager.clear_peer(peer_id)
        else:
            connection: PeerConnection = self.peer_manager.get_peer_connection(peer_id)
            run_recovery = connection is not None and connection.is_primary and connection.ticket_id < self.peer.ticket_id
            self.peer_manager.clear_peer(peer_id)
            self.send_report()

            if run_recovery:
                self.recovery_connection()

    def recovery_connection(self):
        print('\n++++++++[HOPP] START Recovery Connection...')
        peers = self.peer_manager.get_all_peer_connection()

        new_primary_connection = None
        for p_value in peers.values():
            if type(p_value) == PeerConnection:
                connection: PeerConnection = p_value

                if connection.ticket_id < self.peer.ticket_id and connection.is_parent:
                    if connection.priority is not None:
                        connection.priority = connection.priority - 1
                        if connection.priority == 0:
                            new_primary_connection = connection
                    else:
                        print('\n++++++++[HOPP] Connection priority Error....')

        if new_primary_connection is not None:
            self.send_set_primary(new_primary_connection)
        else:
            self.recovery_join()

    def recovery_join(self):
        print('\n++++++++[HOPP] SEND RECOVERY HELLO')

        self.peer_manager.is_run_probe_peer = False
        self.peer_manager.is_run_primary_peer = False

        handler: HompMessageHandler = Factory.instance().get_homp_handler()
        recovery_response = handler.recovery(self.peer)

        if recovery_response is None:
            print('\n++++++++[HOPP] Failed RECOVERY JOIN')
        else:
            if len(recovery_response) > 0:
                for peer_info in recovery_response:
                    target_peer_id = peer_info.get('peer_id')
                    target_address = peer_info.get('address')
                    print("Recovery Join...", target_peer_id, target_address, flush=True)
                    try:
                        recovery_hello_result = self.send_recovery_hello_peer(self.peer, target_address)
                        if recovery_hello_result:
                            TcpMessageHandler.run_estab_peer_timer()
                    except Exception as e:
                        print(e)
                        pass
            else:
                handler.report(self.peer, self.peer_manager)
                print('Peer List is None (RECOVERY JOIN)')

    def reassignment_connections_for_recovery(self, peer_id, ticket_id):
        return self.peer_manager.get_in_candidate_remove_peer_id(peer_id, ticket_id)

    def run_threading_received_socket(self, peer_id, sock):
        t = threading.Thread(target=self.message_handler, args=(peer_id, sock))
        t.daemon = True
        t.start()

    def message_handler(self, peer_id, sock):
        print('\n++++++++[HOPP] IN_COMING CONNECT SOCKET =>', peer_id)

        socket_ip = sock.getsockname()[0]
        socket_port = sock.getsockname()[1]
        socket_peer_id = None

        try:
            is_out_going = False
            request_message = self.convert_bytes_to_message(sock)

            while request_message:
                # print('\n++++++++[HOPP] IN_COMING RECEIVED ', request_message.header)
                socket_peer_id = self.peer_manager.get_peer_id_by_connection(sock)
                # if MessageType.REQUEST_HELLO_PEER == request_message.message_type:
                #     self.received_hello_peer(sock, request_message, is_out_going)
                # if MessageType.REQUEST_ESTAB_PEER == request_message.message_type:
                #     self.received_estab_peer(sock, request_message, is_out_going)

                # HELLO_PEER
                if MessageType.RESPONSE_HELLO_PEER == request_message.message_type:
                    self.received_response_hello_peer(is_out_going, socket_peer_id)

                # ESTAB_PEER
                elif MessageType.RESPONSE_ESTAB_PEER == request_message.message_type or \
                        MessageType.RESPONSE_ESTAB_PEER_ERROR == request_message.message_type:
                    self.received_response_estab_peer(request_message.message_type, is_out_going, socket_peer_id)

                # PROBE_PEER
                elif MessageType.REQUEST_PROBE_PEER == request_message.message_type:
                    self.received_probe_peer(sock, request_message, is_out_going)

                elif MessageType.RESPONSE_PROBE_PEER == request_message.message_type:
                    self.received_response_probe_peer(request_message, is_out_going, socket_peer_id)

                # SET_PRIMARY
                elif MessageType.REQUEST_SET_PRIMARY == request_message.message_type:
                    self.received_set_primary(sock, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_SET_PRIMARY == request_message.message_type or \
                        MessageType.RESPONSE_SET_PRIMARY_ERROR == request_message.message_type:
                    self.received_response_set_primary(request_message.message_type, is_out_going, socket_peer_id)

                # SET_CANDIDATE
                elif MessageType.REQUEST_SET_CANDIDATE == request_message.message_type:
                    self.received_set_candidate(sock, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_SET_CANDIDATE == request_message.message_type:
                    self.received_response_set_candidate(is_out_going, socket_peer_id)

                # BROADCAST_DATA
                elif MessageType.REQUEST_BROADCAST_DATA == request_message.message_type:
                    self.received_broadcast_data(sock, request_message, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_BROADCAST_DATA == request_message.message_type:
                    self.received_response_broadcast_data(is_out_going, socket_peer_id)

                # RELEASE_PEER
                elif MessageType.REQUEST_RELEASE_PEER == request_message.message_type:
                    self.received_release_peer(sock, request_message, is_out_going, socket_peer_id)
                    break

                elif MessageType.RESPONSE_RELEASE_PEER == request_message.message_type:
                    self.received_response_release_peer(sock, is_out_going, socket_peer_id)
                    break

                # HEARTBEAT
                elif MessageType.REQUEST_HEARTBEAT == request_message.message_type:
                    self.received_heartbeat(sock, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_HEARTBEAT == request_message.message_type:
                    self.received_response_heartbeat(is_out_going, socket_peer_id)

                request_message = self.convert_bytes_to_message(sock)

        except Exception as e:
            print('\n++++++++[HOPP] IN_COMING Error\n', e)

        print('\n++++++++[HOPP] [{0}:{1}] IN_COMING DISCONNECT SOCKET'.format(socket_ip, socket_port))
        self.clear_connection(socket_peer_id, is_out_going)

    def received_hello_peer(self, sock, request_message):
        print('\n++++++++[HOPP] RECEIVED HELLO_PEER REQUEST')

        hello_response_message = {
            'RspCode': MessageType.RESPONSE_HELLO_PEER
        }
        print('\n++++++++[HOPP] SEND HELLO_PEER RESPONSE', hello_response_message)
        response_message = self.convert_message_to_bytes(hello_response_message)
        sock.send(response_message)

        received_message = request_message.header

        peer = received_message.get('ReqParams').get('peer')
        target_peer_id = peer.get('peer_id')
        target_address = peer.get('address')
        target_ticket_id = peer.get('ticket_id')

        operation = received_message.get('ReqParams').get('operation')
        conn_num = operation.get('conn_num')
        ttl = operation.get('ttl')
        recovery = operation.get('recovery') if 'recovery' in operation else False

        if conn_num < 1 or ttl < 1:
            return

        children_count = self.peer_manager.get_children_count()
        is_assignment = self.peer_manager.assignment_peer(target_peer_id)

        if not recovery:
            if children_count > 0:
                operation['ttl'] = ttl - 1
                new_conn_num = conn_num - (1 if is_assignment else 0)

                if new_conn_num > 0:
                    operation['conn_num'] = math.ceil(new_conn_num / children_count)

                    print('\n++++++++[HOPP] HELLO_PEER REQUEST !!!BROADCAST!!!', received_message)
                    broadcast_hello_message = self.convert_message_to_bytes(received_message)
                    self.peer_manager.broadcast_message_to_children(broadcast_hello_message)

            if is_assignment:
                establish_socket = self.send_estab_peer(self.peer, target_address)

                if establish_socket is not None:
                    self.peer_manager.add_peer(target_peer_id, target_ticket_id, False, False, establish_socket,
                                               target_address)
                    self.run_threading_received_socket(target_peer_id, establish_socket)
                else:
                    self.peer_manager.un_assignment_peer(target_peer_id)
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
                    broadcast_hello_message = self.convert_message_to_bytes(received_message)
                    self.peer_manager.broadcast_message_to_children(broadcast_hello_message)

            if is_assignment_recovery:
                establish_socket = self.send_estab_peer(self.peer, target_address)

                if establish_socket is not None:
                    self.peer_manager.add_peer(target_peer_id, target_ticket_id, False, False, establish_socket,
                                               target_address)
                    self.run_threading_received_socket(target_peer_id, establish_socket)
                else:
                    self.peer_manager.un_assignment_peer(target_peer_id)

    def received_response_hello_peer(self, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_HELLO_PEER ', socket_peer_id, self.__this__)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_HELLO_PEER ', socket_peer_id, self.__this__)

    def received_estab_peer(self, sock, request_message):
        print('\n++++++++[HOPP] RECEIVE ESTAB_PEER REQUEST')

        received_message = request_message.header.get('ReqParams')
        # target_overlay_id = received_message.get('operation').get('overlay_id')
        target_peer_id = received_message.get('peer').get('peer_id')
        target_ticket_id = received_message.get('peer').get('ticket_id')
        estab_response_message = {
            'RspCode': MessageType.RESPONSE_ESTAB_PEER_ERROR
        }

        is_established = False

        if not self.peer_manager.is_run_probe_peer:
            is_established = self.peer_manager.establish_peer(target_peer_id)
            if is_established:
                estab_response_message['RspCode'] = MessageType.RESPONSE_ESTAB_PEER
                self.peer_manager.add_peer(target_peer_id, target_ticket_id, False, True, sock)
            else:
                self.send_to_all_probe_peer()

        print('\n++++++++[HOPP] SEND ESTAB_PEER RESPONSE', estab_response_message)
        response_message = self.convert_message_to_bytes(estab_response_message)
        sock.send(response_message)

        return is_established

    def received_response_estab_peer(self, message_type, is_out_going, socket_peer_id):
        if message_type == MessageType.RESPONSE_ESTAB_PEER:
            if is_out_going:
                print('\n++++++++[HOPP] ERROR RECEIVED OUT_GOING RESPONSE_ESTAB_PEER ', socket_peer_id, self.__this__)
            else:
                print('\n++++++++[HOPP] ERROR RECEIVED IN_COMING RESPONSE_ESTAB_PEER ', socket_peer_id, self.__this__)
        else:
            if is_out_going:
                print('\n++++++++[HOPP] ERROR RECEIVED OUT_GOING RESPONSE_ESTAB_PEER ', socket_peer_id)
            else:
                print('\n++++++++[HOPP] ERROR RECEIVED IN_COMING RESPONSE_ESTAB_PEER ', socket_peer_id)

    def received_probe_peer(self, sock, request_message, is_out_going):
        if is_out_going:
            print('\n++++++++[HOPP] OUT_GOING RECEIVED PROBE_PEER')
        else:
            print('\n++++++++[HOPP] IN_COMING RECEIVED PROBE_PEER')

        probe_response_message = {
            'RspCode': MessageType.RESPONSE_PROBE_PEER,
            'RspParams': {
                'operation': {
                    'ntp_time': request_message.header.get('ReqParams').get('operation').get('ntp_time')
                }
            }
        }
        print('\n++++++++[HOPP] SEND PROBE_PEE RESPONSE', probe_response_message)
        response_message = self.convert_message_to_bytes(probe_response_message)
        sock.send(response_message)

    def received_response_probe_peer(self, response_message, is_out_going, socket_peer_id):
        send_time = datetime.strptime(response_message.header.get('RspParams').get('operation').get('ntp_time'),
                                      self.fmt)
        now_time = datetime.strptime(str(datetime.now()), self.fmt)
        delta_time = now_time - send_time
        probe_time = delta_time.seconds * 1000000 + delta_time.microseconds
        self.peer_manager.estab_peers[socket_peer_id] = probe_time

        if is_out_going:
            print('\n++++++++[HOPP] OUT_GOING RECEIVED RESPONSE_PROBE_PEER ', socket_peer_id, probe_time)
        else:
            print('\n++++++++[HOPP] IN_COMING RECEIVED RESPONSE_PROBE_PEER ', socket_peer_id, probe_time)

    def received_set_primary(self, sock, is_out_going, socket_peer_id):
        print('\n++++++++[HOPP] RECEIVED SET_PRIMARY', socket_peer_id)
        result_set_primary = self.peer_manager.set_primary_peer(socket_peer_id, is_out_going)

        primary_response_message = {
            'RspCode': MessageType.RESPONSE_SET_PRIMARY_ERROR
        }
        if result_set_primary:
            primary_response_message['RspCode'] = MessageType.RESPONSE_SET_PRIMARY

        print('\n++++++++[HOPP] SEND SET_PRIMARY RESPONSE', primary_response_message)
        response_message = self.convert_message_to_bytes(primary_response_message)
        sock.send(response_message)

        if result_set_primary:
            self.send_report()

    def received_response_set_primary(self, message_type, is_out_going, socket_peer_id):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY ', socket_peer_id)

        if self.peer_manager.is_run_primary_peer:
            if message_type == MessageType.RESPONSE_SET_PRIMARY:
                self.peer_manager.set_primary_peer(socket_peer_id, is_out_going)
                self.send_report()
                self.send_to_all_set_candidate()  # optional
                # self.peer_manager.is_run_primary_peer = False  # send_to_all_set_candidate 미사용시 활성화
            else:
                self.check_and_send_set_primary()
        else:
            if message_type == MessageType.RESPONSE_SET_PRIMARY:
                self.peer_manager.set_primary_peer(socket_peer_id, is_out_going)
                self.send_report()
            else:
                self.recovery_connection()

    def received_set_candidate(self, sock, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING SET_CANDIDATE ', socket_peer_id, self.__this__)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING SET_CANDIDATE ', socket_peer_id, self.__this__)

        candidate_response_message = {
            'RspCode': MessageType.RESPONSE_SET_CANDIDATE
        }
        print('\n++++++++[HOPP] SEND SET_CANDIDATE RESPONSE', candidate_response_message)
        response_message = self.convert_message_to_bytes(candidate_response_message)
        sock.send(response_message)

        self.send_report()

    def received_response_set_candidate(self, is_out_going, socket_peer_id):
        # set_candidate 보낼때 self.send_report()를 한다.
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_SET_CANDIDATE ', socket_peer_id, self.__this__)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_SET_CANDIDATE ', socket_peer_id, self.__this__)

    def received_broadcast_data(self, sock, request_message, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING BROADCAST_DATA ', socket_peer_id)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING BROADCAST_DATA ', socket_peer_id)

        request_params = request_message.header.get('ReqParams')
        source_peer = request_params.get('peer').get('peer_id')
        print('\n++++++++[HOPP] SENDER:{0} / SOURCE:{1} / DATA=>{2}'.format(socket_peer_id, source_peer,
                                                                            request_message.content))

        if request_params.get('ack'):
            broadcast_data_response_message = {
                'RspCode': MessageType.RESPONSE_BROADCAST_DATA
            }
            print('\n++++++++[HOPP] SEND BROADCAST_DATA RESPONSE', broadcast_data_response_message)
            response_message = self.convert_message_to_bytes(broadcast_data_response_message)
            sock.send(response_message)

        if source_peer != self.peer.peer_id:
            self.relay_broadcast_data(socket_peer_id, request_message)

    def received_response_broadcast_data(self, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_BROADCAST_DATA ', socket_peer_id, self.__this__)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_BROADCAST_DATA ', socket_peer_id, self.__this__)

    def received_release_peer(self, sock, request_message, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RELEASE_PEER ', socket_peer_id, self.__this__)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RELEASE_PEER ', socket_peer_id, self.__this__)

        if request_message.header.get('ReqParams').get('operation').get('ack'):
            release_response_message = {
                'RspCode': MessageType.RESPONSE_RELEASE_PEER
            }
            print('\n++++++++[HOPP] SEND RELEASE_PEER RESPONSE', release_response_message)
            response_message = self.convert_message_to_bytes(release_response_message)
            sock.send(response_message)
        else:
            sock.close()

    def received_response_release_peer(self, sock, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_RELEASE_PEER ', socket_peer_id, self.__this__)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_RELEASE_PEER ', socket_peer_id, self.__this__)

        sock.close()

    def received_heartbeat(self, sock, is_out_going, socket_peer_id):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            if is_out_going:
                print('\n++++++++[HOPP] RECEIVED OUT_GOING HEARTBEAT ', socket_peer_id)
            else:
                print('\n++++++++[HOPP] RECEIVED IN_COMING HEARTBEAT ', socket_peer_id)

        connection: PeerConnection = self.peer_manager.get_peer_connection(socket_peer_id)
        if connection is not None:
            connection.update_time = datetime.now()

            release_response_message = {
                'RspCode': MessageType.RESPONSE_HEARTBEAT
            }
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n++++++++[HOPP] SEND HEARTBEAT RESPONSE', release_response_message)
            response_message = self.convert_message_to_bytes(release_response_message)
            sock.send(response_message)

    def received_response_heartbeat(self, is_out_going, socket_peer_id):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            if is_out_going:
                print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_HEARTBEAT ', socket_peer_id)
            else:
                print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_HEARTBEAT ', socket_peer_id)

        connection: PeerConnection = self.peer_manager.get_peer_connection(socket_peer_id)
        if connection is not None:
            connection.update_time = datetime.now()

    ###################
    ###################

    @classmethod
    def send_hello_peer(cls, peer: Peer, target_address):
        if 'tcp://' in target_address:
            try:
                _target_address = target_address.replace('tcp://', '')
                ip_port = _target_address.split(':')
                ip = ip_port[0]
                port = int(ip_port[1])

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, port))
                print('\n++++++++[HOPP] [{0}:{1}] CONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                   sock.getsockname()[1]))

                hello_message = {
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

                print('\n++++++++[HOPP] SEND HELLO REQUEST', hello_message)
                request_message = cls.convert_message_to_bytes(hello_message)
                sock.send(request_message)

                response_message: HoppMessage = cls.convert_bytes_to_message(sock)
                print('\n++++++++[HOPP] RECEIVED HELLO RESPONSE ', response_message.header)
                print('\n++++++++[HOPP] [{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                      sock.getsockname()[1]))
                sock.close()

                return True if response_message.header.get('RspCode') == MessageType.RESPONSE_HELLO_PEER else False
            except Exception as e:
                print('\n++++++++[HOPP] Error send_hello\n', e)
                return None
        else:
            return None

    def send_estab_peer(self, peer: Peer, target_address):
        if 'tcp://' in target_address:
            try:
                _target_address = target_address.replace('tcp://', '')
                ip_port = _target_address.split(':')
                ip = ip_port[0]
                port = int(ip_port[1])

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, port))
                print('\n++++++++[HOPP] [{0}:{1}] CONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                   sock.getsockname()[1]))

                establish_message = {
                    'ReqCode': MessageType.REQUEST_ESTAB_PEER,
                    'ReqParams': {
                        'operation': {
                            'overlay_id': peer.overlay_id
                        },
                        'peer': {
                            'peer_id': peer.peer_id,
                            'ticket_id': peer.ticket_id
                        }
                    }
                }

                print('\n++++++++[HOPP] SEND ESTABLISH REQUEST', establish_message)
                request_message = self.convert_message_to_bytes(establish_message)
                sock.send(request_message)

                response_message: HoppMessage = self.convert_bytes_to_message(sock)
                print('\n++++++++[HOPP] RECEIVED ESTABLISH RESPONSE', response_message.header)

                if response_message.header.get('RspCode') == MessageType.RESPONSE_ESTAB_PEER:
                    return sock
                elif response_message.header.get('RspCode') == MessageType.RESPONSE_ESTAB_PEER_ERROR:
                    print('\n++++++++[HOPP] [{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                          sock.getsockname()[1]))
                    sock.close()
                    return None
                else:
                    print('\n++++++++[HOPP] [{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                          sock.getsockname()[1]))
                    sock.close()
                    return None
            except Exception as e:
                print('\n++++++++[HOPP] Error send_establish\n', e)
                return None
        else:
            return None

    @classmethod
    def run_estab_peer_timer(cls):
        print('\n++++++++[HOPP] RUN_ESTAB_PEER_TIMER')
        threading.Timer(PEER_CONFIG['ESTAB_PEER_TIMEOUT'], cls.send_to_all_probe_peer).start()

    @classmethod
    def send_to_all_probe_peer(cls):
        peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        if not peer_manager.is_run_probe_peer:
            print('\n++++++++[HOPP] SEND TO ALL PROBE_PEER')
            peer_manager.is_run_probe_peer = True
            estab_peers = peer_manager.get_estab_peers()

            if len(estab_peers) > 0:
                for peer_id in estab_peers.keys():
                    connection: PeerConnection = peer_manager.get_peer_connection(peer_id)
                    if connection is not None:
                        cls.send_probe_peer(connection)

                cls.run_probe_peer_timer()
            else:
                print('\n++++++++[HOPP] ESTAB_PEER is None...')

    @classmethod
    def send_probe_peer(cls, connection: PeerConnection):
        probe_message = {
            'ReqCode': MessageType.REQUEST_PROBE_PEER,
            'ReqParams': {
                'operation': {
                    'ntp_time': str(datetime.now())
                }
            }
        }
        print('\n++++++++[HOPP] SEND PROBE_PEER REQUEST', probe_message)
        request_message = cls.convert_message_to_bytes(probe_message)
        connection.connection.send(request_message)

    @classmethod
    def run_probe_peer_timer(cls):
        print('\n++++++++[HOPP] RUN_PROBE_PEER_TIMER')
        threading.Timer(PEER_CONFIG['PROBE_PEER_TIMEOUT'], cls.check_and_send_set_primary).start()

    @classmethod
    def check_and_send_set_primary(cls):
        peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peer_manager.is_run_primary_peer = True

        print('\n++++++++[HOPP] CHECK AND SEND SET_PRIMARY')
        if len(peer_manager.estab_peers) < 1:
            print('\n++++++++[HOPP] Error... ESTAB_PEERS len = 0')
            return

        sorted_estab_peers = sorted(peer_manager.estab_peers.items(), key=operator.itemgetter(1))

        primary_peer_connection = None
        for estab_index, (peer_id, delta_time) in enumerate(sorted_estab_peers):
            connection: PeerConnection = peer_manager.get_peer_connection(peer_id)
            connection.priority = estab_index
            if estab_index == 0:
                primary_peer_connection = connection

        if primary_peer_connection is not None:
            del peer_manager.estab_peers[primary_peer_connection.peer_id]
            cls.send_set_primary(primary_peer_connection)

        # primary_peer_id = None
        # min_probe_time = 99 * 1000000
        # for peer_id in peer_manager.estab_peers.keys():
        #     probe_time = peer_manager.estab_peers[peer_id]
        #     if min_probe_time > probe_time:
        #         min_probe_time = probe_time
        #         primary_peer_id = peer_id
        #
        # connection: PeerConnection = peer_manager.get_peer_connection(primary_peer_id)
        # if connection is not None:
        #     del peer_manager.estab_peers[primary_peer_id]
        #     cls.send_set_primary(connection)

    @classmethod
    def send_set_primary(cls, connection: PeerConnection):
        primary_message = {
            'ReqCode': MessageType.REQUEST_SET_PRIMARY
        }
        print('\n++++++++[HOPP] SEND SET_PRIMARY REQUEST', primary_message)
        request_message = cls.convert_message_to_bytes(primary_message)
        connection.connection.send(request_message)

    @classmethod
    def send_to_all_set_candidate(cls):
        print('\n++++++++[HOPP] SEND TO ALL SET CANDIDATE')
        peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peer_manager.is_run_primary_peer = False

        if len(peer_manager.estab_peers) > 0:
            for peer_id in peer_manager.estab_peers.keys():
                connection: PeerConnection = peer_manager.get_peer_connection(peer_id)
                if connection is not None:
                    cls.send_set_candidate(connection)

        peer_manager.estab_peers.clear()

    @classmethod
    def send_set_candidate(cls, connection: PeerConnection):
        # TODO => 직접 사용할 경우 self.send_report() 를 해야된다.
        candidate_message = {
            'ReqCode': MessageType.REQUEST_SET_CANDIDATE
        }
        print('\n++++++++[HOPP] SEND SET_CANDIDATE REQUEST', candidate_message)
        request_message = cls.convert_message_to_bytes(candidate_message)
        connection.connection.send(request_message)

    @classmethod
    def send_broadcast_data(cls, peer: Peer, send_data, is_ack=None):
        bytes_data, data_length = cls.convert_data_to_bytes(send_data)
        operation_ack = is_ack if is_ack is not None else PEER_CONFIG['BROADCAST_OPERATION_ACK']

        data_message = {
            'ReqCode': MessageType.REQUEST_BROADCAST_DATA,
            'ReqParams': {
                'operation': {
                    'ack': operation_ack
                },
                'peer': {
                    'peer_id': peer.peer_id
                },
                'payload': {
                    'length': data_length,
                    'type': 'text/plain'
                }
            }
        }

        print('\n++++++++[HOPP] SEND BROADCAST_DATA REQUEST', data_message)
        request_message = cls.convert_message_to_bytes(data_message, bytes_data)

        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        get_peer_manager.send_message(request_message)

    def relay_broadcast_data(self, sender, hopp_message: HoppMessage):
        print('\n++++++++[HOPP] RELAY BROADCAST_DATA REQUEST', hopp_message.header)
        bytes_data = self.convert_to_bytes(hopp_message.content)
        request_message = self.convert_message_to_bytes(hopp_message.header, bytes_data)
        self.peer_manager.broadcast_message(sender, request_message)

    @classmethod
    def send_release_peer(cls, peer_id, is_ack=None):
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        connection: PeerConnection = get_peer_manager.get_peer_connection(peer_id)
        operation_ack = is_ack if is_ack is not None else PEER_CONFIG['RELEASE_OPERATION_ACK']

        if connection is not None:
            release_message = {
                'ReqCode': MessageType.REQUEST_RELEASE_PEER,
                'ReqParams': {
                    'operation': {
                        'ack': operation_ack
                    }
                }
            }

            print('\n++++++++[HOPP] SEND RELEASE_PEER REQUEST', release_message)
            request_message = cls.convert_message_to_bytes(release_message)
            connection.connection.send(request_message)
            if not operation_ack:
                connection.connection.close()
        else:
            print('\n++++++++[HOPP] RELEASE_PEER -- NOT EXIST PEER', peer_id)

    @classmethod
    def send_to_all_release_peer(cls):
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        get_peer_manager.is_destroy = True
        peers = get_peer_manager.get_all_peer_connection()
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
            request_message = cls.convert_message_to_bytes(release_message)

            peer_list = list(peers.keys())
            for peer_id in peer_list:
                connection: PeerConnection = peers[peer_id]
                connection.connection.send(request_message)
                if not operation_ack:
                    connection.connection.close()

    @classmethod
    def run_heartbeat_scheduler(cls):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n----------[HeartScheduler] RUN HEARTBEAT SCHEDULER')

        if Factory.instance().is_used_tcp():
            get_peer: Peer = Factory.instance().get_peer()
            scheduler = HeartScheduler(get_peer.heartbeat_interval, get_peer.heartbeat_timeout)
            Factory.instance().set_heartbeat_scheduler(scheduler)
            scheduler.start(cls.send_to_all_heartbeat, cls.check_connection_heartbeat)

    @classmethod
    def send_heartbeat(cls, peer_id):
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        connection: PeerConnection = get_peer_manager.get_peer_connection(peer_id)
        get_peer: Peer = Factory.instance().get_peer()

        if connection is not None:
            if (connection.is_primary and get_peer.ticket_id > connection.ticket_id) or \
                    connection.peer_id in get_peer_manager.out_candidate_list:
                heartbeat_message = {
                    'ReqCode': MessageType.REQUEST_HEARTBEAT
                }
                if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                    print('\n++++++++[HOPP] SEND REQUEST_HEARTBEAT REQUEST', heartbeat_message, connection.peer_id)
                request_message = cls.convert_message_to_bytes(heartbeat_message)
                connection.connection.send(request_message)
        else:
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n++++++++[HOPP] REQUEST_HEARTBEAT -- NOT EXIST PEER', peer_id)

    @classmethod
    def send_to_all_heartbeat(cls):
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peers = get_peer_manager.get_all_peer_connection()
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n----------[HeartScheduler] SEND TO ALL Heartbeat')

        if get_peer_manager.is_send_heartbeat:
            if len(peers) > 0:
                for peer_id in peers.keys():
                    cls.send_heartbeat(peer_id)
        else:
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n----------[HeartScheduler]] NOT WORK send_heartbeat')

    @classmethod
    def check_connection_heartbeat(cls):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n----------[HeartScheduler] CHECK CONNECTION Heartbeat')

        get_peer: Peer = Factory.instance().get_peer()
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peers = get_peer_manager.get_all_peer_connection()

        for p_value in peers.values():
            if type(p_value) == PeerConnection:
                connection: PeerConnection = p_value
                update_time = datetime.strptime(str(connection.update_time), cls.fmt)
                now_time = datetime.strptime(str(datetime.now()), cls.fmt)
                delta_time = now_time - update_time
                if delta_time.seconds > get_peer.heartbeat_timeout:
                    if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                        print('\n----------[HeartScheduler] Connection is not alive =>', connection.peer_id)
                    print('\n----------[HeartScheduler] Disconnection Socket =>', connection.peer_id)
                    connection.connection.close()
                else:
                    if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                        print('\n----------[HeartScheduler] Connection is alive =>', connection.peer_id)

    def send_recovery_hello_peer(self, peer: Peer, target_address):
        if 'tcp://' in target_address:
            try:
                _target_address = target_address.replace('tcp://', '')
                ip_port = _target_address.split(':')
                ip = ip_port[0]
                port = int(ip_port[1])

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ip, port))
                print('\n++++++++[HOPP] [{0}:{1}] CONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                   sock.getsockname()[1]))

                hello_recovery_message = {
                    'ReqCode': MessageType.REQUEST_HELLO_PEER,
                    'ReqParams': {
                        'operation': {
                            'overlay_id': peer.overlay_id,
                            'conn_num': PEER_CONFIG['ESTAB_PEER_MAX_COUNT'],
                            'ttl': PEER_CONFIG['PEER_TTL'],
                            'recovery': True
                        },
                        'peer': {
                            'peer_id': peer.peer_id,
                            'address': peer.get_address(),
                            'ticket_id': peer.ticket_id
                        }
                    }
                }

                print('\n++++++++[HOPP] SEND HELLO (RECOVERY) REQUEST', hello_recovery_message)
                request_message = self.convert_message_to_bytes(hello_recovery_message)
                sock.send(request_message)

                response_message: HoppMessage = self.convert_bytes_to_message(sock)
                print('\n++++++++[HOPP] RECEIVED HELLO (RECOVERY) RESPONSE ', response_message.header)
                print('\n++++++++[HOPP] [{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                      sock.getsockname()[1]))
                sock.close()

                return True if response_message.header.get('RspCode') == MessageType.RESPONSE_HELLO_PEER else False
            except Exception as e:
                print('\n++++++++[HOPP] Error send_hello (RECOVERY) \n', e)
                return None
        else:
            return None


class TcpThreadingSocketServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

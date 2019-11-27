import socketserver
import threading
import math
import socket
import json
import operator
from datetime import datetime

from config import PEER_CONFIG
from data.factory import Factory, Peer
from data.client_scheduler import ClientScheduler
from classes.hopp_message import HoppMessage
from classes.constants import MessageType
from tcp.tcp_peer_connection_manager import TcpPeerConnectionManager, PeerConnection
from homp.homp_message_handler import HompMessageHandler

lock = threading.Lock()


class TcpMessageHandler(socketserver.BaseRequestHandler):
    peer_manager = TcpPeerConnectionManager()
    Factory.instance().set_peer_manager(peer_manager)
    peer: Peer = Factory.instance().get_peer()

    _byteorder = 'little'
    _encoding = 'utf=8'
    fmt = "%Y-%m-%d %H:%M:%S.%f"
    print('\n++++++++[HOPP] CREATE TcpMessageHandler')

    def handle(self):
        print('\n++++++++[HOPP] [{0}:{1}] OUT_GOING CONNECT SOCKET'.format(self.client_address[0],
                                                                           self.client_address[1]))
        socket_ip = self.client_address[0]
        socket_port = self.client_address[1]
        socket_peer_id = None
        is_out_going = True

        try:
            sock = self.request
            request_message = self.convert_bytes_to_message(sock)

            while request_message:
                # print('\n++++++++[HOPP] OUT_GOING RECEIVED', request_message.header)
                if socket_peer_id is None:
                    socket_peer_id = self.peer_manager.get_peer_id_by_connection(sock)

                # HELLO_PEER
                if MessageType.REQUEST_HELLO_PEER == request_message.message_type:
                    self.received_hello_peer(sock, request_message)
                    if socket_peer_id is None:
                        self.close_tcp_connection(sock)
                        break

                elif MessageType.RESPONSE_HELLO_PEER == request_message.message_type:
                    self.received_response_hello_peer(is_out_going, socket_peer_id)

                # ESTAB_PEER
                elif MessageType.REQUEST_ESTAB_PEER == request_message.message_type:
                    if not self.peer.is_top_peer and not self.peer.isOwner and \
                            not Factory.instance().get_client_scheduler().is_set_checked_primary_scheduler():
                        self.run_recovery_scheduler()

                    is_established = self.received_estab_peer(sock, request_message)
                    if not is_established:
                        self.close_tcp_connection(sock)
                        break
                    elif PEER_CONFIG['PROBE_PEER_TIMEOUT'] < 1:
                        self.send_set_primary_is_skip_probe(sock)

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

                # SCAN_TREE
                elif MessageType.REQUEST_SCAN_TREE == request_message.message_type:
                    self.received_scan_tree(request_message, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_HEARTBEAT == request_message.message_type:
                    self.received_response_scan_tree(is_out_going, socket_peer_id)

                request_message = self.convert_bytes_to_message(sock)

        except Exception as e:
            print('\n++++++++[HOPP] OUT_GOING Error\n', e)

        print('\n++++++++[HOPP] [{0}:{1}] OUT_GOING DISCONNECT SOCKET'.format(socket_ip, socket_port))
        self.clear_connection(socket_peer_id, is_out_going)

    @classmethod
    def send_web_socket(cls, message):
        try:
            peer: Peer = Factory.instance().get_peer()
            if peer.using_web_gui:
                Factory.instance().get_web_socket_handler().send_log_message(message)
        except:
            print('\n++++++++[HOPP] failed send_web_socket... ')

    @classmethod
    def sendall_tcp_message(cls, connection, message):
        try:
            if connection is not None:
                lock.acquire()
                connection.sendall(message)
                lock.release()
        except:
            print('\n++++++++[HOPP] failed send_message... ')
            cls.close_tcp_connection(connection)

    @classmethod
    def close_tcp_connection(cls, connection):
        try:
            if connection is not None:
                lock.acquire()
                connection.close()
                lock.release()
                print('\n++++++++[HOPP] Close Socket...')
        except:
            print('\n++++++++[HOPP] Failed  Close Socket...')
        finally:
            peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
            peer_id = peer_manager.get_peer_id_by_connection(connection)
            if peer_id is not None:
                peer_manager.clear_peer(peer_id)

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
            cls.close_tcp_connection(conn)
            # try:
            #     chunk = conn.recv(1)
            #     if chunk == b'':
            #         print('\n++++++++[HOPP] Chunk Close\n', e)
            #         cls.close_tcp_connection(conn)
            # except:
            #     print('\n++++++++[HOPP] Error Chunk Close\n', e)
            #     cls.close_tcp_connection(conn)
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

        # if not self.peer.is_top_ticket_id_peer and not self.peer.isOwner and
        # not Factory.instance().get_client_scheduler().is_set_checked_primary_scheduler():
        #     self.run_recovery_scheduler()

        if is_out_going:
            print('\n++++++++[HOPP] OUT_GOING *********** CLEAR', peer_id)
        else:
            print('\n++++++++[HOPP] IN_COMING ************ CLEAR', peer_id)

        # self.send_web_socket('CLEAR_CONNECTION.')

        if not self.peer_manager.has_primary() and self.peer.using_web_gui:
            Factory.instance().get_web_socket_handler().send_connection_change(False)

        if self.peer_manager.is_destroy:
            self.peer_manager.clear_peer(peer_id)
        else:
            peer_connection: PeerConnection = self.peer_manager.get_peer_connection(peer_id)
            if peer_connection is not None and peer_connection.ticket_id < self.peer.ticket_id and \
                    peer_connection.is_primary and peer_connection.is_parent:
                self.recovery_connection()

            self.peer_manager.clear_peer(peer_id)
            self.send_report()

    def recovery_connection(self):
        print('\n++++++++[HOPP] START Recovery Connection...')
        self.send_web_socket('RECOVER_CONNECTION.')

        new_primary_connection = None
        for peer_id in self.peer_manager.get_out_going_candidate_list():
            if not self.peer_manager.is_peer_in_failed_primary_list(peer_id):
                peer_connection: PeerConnection = self.peer_manager.get_peer_connection(peer_id)

                if peer_connection.ticket_id < self.peer.ticket_id and peer_connection.is_parent:
                    new_primary_connection = peer_connection
                    break

        if new_primary_connection is not None:
            self.send_set_primary(new_primary_connection)
        else:
            self.recovery_join()

    def recovery_join(self):
        print('\n++++++++[HOPP] SEND RECOVERY HELLO')
        self.send_web_socket('SEND RECOVERY HELLO.')

        self.peer_manager.is_run_probe_peer = False
        self.peer_manager.is_run_primary_peer = False
        self.peer_manager.is_first_peer_set_primary = False

        handler: HompMessageHandler = Factory.instance().get_homp_handler()
        recovery_response = handler.recovery(self.peer)

        if recovery_response is None:
            print('\n++++++++[HOPP] Failed RECOVERY JOIN')
            self.send_web_socket('FAILED RECOVERY HELLO.')
        else:
            if len(recovery_response) > 0:
                is_process = False
                for peer_info in recovery_response:
                    target_peer_id = peer_info.get('peer_id')
                    target_address = peer_info.get('address')

                    if self.peer.peer_id == target_peer_id:
                        self.peer.is_top_peer = True
                        print("Top Peer...", flush=True)
                        self.send_web_socket('TOP PEER.')
                        is_process = True
                        break
                    else:
                        print("Recovery Join...", target_peer_id, target_address, flush=True)
                        self.send_web_socket('RECOVERY JOIN.')

                        recovery_hello_result = self.send_recovery_hello_peer(self.peer, target_address)
                        if recovery_hello_result:
                            TcpMessageHandler.run_estab_peer_timer()
                            is_process = True
                            break

                if not is_process:
                    # TODO 복구
                    self.send_web_socket('RECOVERY JOIN LIST IS NONE.')
                    print('\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                    print('++++++++[HOPP] (RECOVERY JOIN) HELLO_PEER List is None... 네트웨크에 참가 실패.')
                    print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
            else:
                # TODO 복구
                self.send_web_socket('RECOVERY JOIN LIST IS NONE.')
                handler.report(self.peer, self.peer_manager)
                print('\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                print('(RECOVERY JOIN) HELLO_PEER  List is None... 네트웨크에 참가 실패. 서버 문제 발생...')
                print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

    def reassignment_connections_for_recovery(self, peer_id, ticket_id):
        return self.peer_manager.get_in_candidate_remove_peer_id(peer_id, ticket_id)

    def run_threading_received_socket(self, peer_id, sock):
        t = threading.Thread(target=self.message_handler, args=(peer_id, sock), daemon=True)
        t.start()

    def message_handler(self, peer_id, sock):
        print('\n++++++++[HOPP] IN_COMING CONNECT SOCKET =>', peer_id)

        socket_ip = sock.getsockname()[0]
        socket_port = sock.getsockname()[1]
        socket_peer_id = None
        is_out_going = False

        try:
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

                # SCAN_TREE
                elif MessageType.REQUEST_SCAN_TREE == request_message.message_type:
                    self.received_scan_tree(request_message, is_out_going, socket_peer_id)

                elif MessageType.RESPONSE_HEARTBEAT == request_message.message_type:
                    self.received_response_scan_tree(is_out_going, socket_peer_id)

                request_message = self.convert_bytes_to_message(sock)

        except Exception as e:
            print('\n++++++++[HOPP] IN_COMING Error\n', e)

        print('\n++++++++[HOPP] [{0}:{1}] IN_COMING DISCONNECT SOCKET'.format(socket_ip, socket_port))
        self.clear_connection(socket_peer_id, is_out_going)

    def received_hello_peer(self, sock, request_message):
        print('\n++++++++[HOPP] RECEIVED HELLO_PEER REQUEST')
        self.send_web_socket('RECEIVED HELLO_PEER.')

        hello_response_message = {
            'RspCode': MessageType.RESPONSE_HELLO_PEER
        }
        print('\n++++++++[HOPP] SEND HELLO_PEER RESPONSE', hello_response_message)
        self.send_web_socket('SEND HELLO_PEER RESPONSE.')

        response_message = self.convert_message_to_bytes(hello_response_message)
        self.sendall_tcp_message(sock, response_message)

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
                    self.send_web_socket('SEND BROADCAST HELLO_PEER.')
                    broadcast_hello_message = self.convert_message_to_bytes(received_message)
                    self.peer_manager.broadcast_message_to_children(broadcast_hello_message)

            if is_assignment:
                establish_socket = self.send_estab_peer(self.peer, target_address)

                if establish_socket is not None:
                    self.peer_manager.add_peer(target_peer_id, target_ticket_id, False, False, establish_socket,
                                               target_address)
                    self.send_report()
                    self.run_threading_received_socket(target_peer_id, establish_socket)
                else:
                    self.peer_manager.un_assignment_peer(target_peer_id)
        else:
            if target_ticket_id <= self.peer.ticket_id:
                print('\n++++++++[HOPP] RECOVERY ==  target_ticket_id.... bigger than me', received_message)
                return

            print('\n++++++++[HOPP] RECOVERY == HELLO_PEER', target_peer_id)
            self.send_web_socket('RECOVERY HELLO_PEER.')
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
                    self.send_web_socket('BROADCAST RECOVERY HELLO_PEER.')
                    broadcast_hello_message = self.convert_message_to_bytes(received_message)
                    self.peer_manager.broadcast_message_to_children(broadcast_hello_message)

            if is_assignment_recovery:
                establish_socket = self.send_estab_peer(self.peer, target_address)

                if establish_socket is not None:
                    self.peer_manager.add_peer(target_peer_id, target_ticket_id, False, False, establish_socket,
                                               target_address)
                    self.send_report()
                    self.run_threading_received_socket(target_peer_id, establish_socket)
                else:
                    self.peer_manager.un_assignment_peer(target_peer_id)

    @classmethod
    def received_response_hello_peer(cls, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_HELLO_PEER ', socket_peer_id)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_HELLO_PEER ', socket_peer_id)
        cls.send_web_socket('RECEIVED RESPONSE_HELLO_PEER.')

    def received_estab_peer(self, sock, request_message):
        print('\n++++++++[HOPP] RECEIVE ESTAB_PEER REQUEST')
        self.send_web_socket('RECEIVED ESTAB_PEER.')

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

        print('\n++++++++[HOPP] SEND ESTAB_PEER RESPONSE', estab_response_message)
        self.send_web_socket('SEND ESTAB_PEER RESPONSE.')
        response_message = self.convert_message_to_bytes(estab_response_message)
        self.sendall_tcp_message(sock, response_message)

        if is_established:
            self.send_report()
        else:
            self.send_to_all_probe_peer()

        return is_established

    @classmethod
    def received_response_estab_peer(cls, message_type, is_out_going, socket_peer_id):
        if message_type == MessageType.RESPONSE_ESTAB_PEER:
            if is_out_going:
                print('\n++++++++[HOPP] ERROR RECEIVED OUT_GOING RESPONSE_ESTAB_PEER ', socket_peer_id)
            else:
                print('\n++++++++[HOPP] ERROR RECEIVED IN_COMING RESPONSE_ESTAB_PEER ', socket_peer_id)
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

        self.send_web_socket('RECEIVED PROBE_PEER.')

        probe_response_message = {
            'RspCode': MessageType.RESPONSE_PROBE_PEER,
            'RspParams': {
                'operation': {
                    'ntp_time': request_message.header.get('ReqParams').get('operation').get('ntp_time')
                }
            }
        }
        print('\n++++++++[HOPP] SEND PROBE_PEE RESPONSE', probe_response_message)
        self.send_web_socket('SEND PROBE_PEER RESPONSE.')

        response_message = self.convert_message_to_bytes(probe_response_message)
        self.sendall_tcp_message(sock, response_message)

    def received_response_probe_peer(self, response_message, is_out_going, socket_peer_id):
        send_time = datetime.strptime(response_message.header.get('RspParams').get('operation').get('ntp_time'),
                                      self.fmt)
        now_time = datetime.strptime(str(datetime.now()), self.fmt)
        delta_time = now_time - send_time
        probe_time = delta_time.seconds * 1000000 + delta_time.microseconds
        self.peer_manager.set_estab_peers_probe_time(socket_peer_id, probe_time)

        if is_out_going:
            print('\n++++++++[HOPP] OUT_GOING RECEIVED RESPONSE_PROBE_PEER ', socket_peer_id, probe_time)
        else:
            print('\n++++++++[HOPP] IN_COMING RECEIVED RESPONSE_PROBE_PEER ', socket_peer_id, probe_time)

        self.send_web_socket('RECEIVED PROBE_PEER RESPONSE.')

    def received_set_primary(self, sock, is_out_going, socket_peer_id):
        print('\n++++++++[HOPP] RECEIVED SET_PRIMARY', socket_peer_id)
        self.send_web_socket('RECEIVED SET_PRIMARY.')

        result_set_primary = self.peer_manager.set_primary_peer(socket_peer_id, is_out_going)

        primary_response_message = {
            'RspCode': MessageType.RESPONSE_SET_PRIMARY_ERROR
        }

        if result_set_primary:
            primary_response_message['RspCode'] = MessageType.RESPONSE_SET_PRIMARY
            if self.peer.using_web_gui:
                Factory.instance().get_web_socket_handler().send_connection_change(True)

        print('\n++++++++[HOPP] SEND SET_PRIMARY RESPONSE', primary_response_message)
        self.send_web_socket('SEND SET_PRIMARY RESPONSE.')

        response_message = self.convert_message_to_bytes(primary_response_message)
        self.sendall_tcp_message(sock, response_message)

        if result_set_primary:
            self.send_report()

    def received_response_set_primary(self, message_type, is_out_going, socket_peer_id):
        if self.peer_manager.is_run_primary_peer:
            print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY (RUN_PRIMARY_PEER)', socket_peer_id)
            self.send_web_socket('RECEIVED SET_PRIMARY RESPONSE(RUN_PRIMARY_PEER).')

            if message_type == MessageType.RESPONSE_SET_PRIMARY:
                self.peer_manager.set_primary_peer(socket_peer_id, is_out_going)
                self.send_report()

                if self.peer.using_web_gui:
                    Factory.instance().get_web_socket_handler().send_connection_change(True)

                self.peer_manager.is_run_primary_peer = False
                if PEER_CONFIG['SEND_CANDIDATE']:  # optional
                    self.send_to_all_set_candidate()
                else:
                    self.peer_manager.clear_estab_peers()
            else:
                self.check_and_send_set_primary()
        elif self.peer_manager.is_first_peer_set_primary:
            print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY (FIRST_PEER_SET_PRIMARY)', socket_peer_id)
            self.send_web_socket('RECEIVED SET_PRIMARY RESPONSE(FIRST_PEER_SET_PRIMARY)')

            if message_type == MessageType.RESPONSE_SET_PRIMARY:
                self.peer_manager.set_primary_peer(socket_peer_id, is_out_going)
                self.send_report()

                if self.peer.using_web_gui:
                    Factory.instance().get_web_socket_handler().send_connection_change(True)
        else:
            print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY (RECOVERY)', socket_peer_id)
            self.send_web_socket('RECEIVED SET_PRIMARY RESPONSE(RECOVERY).')

            if message_type == MessageType.RESPONSE_SET_PRIMARY:
                self.peer_manager.clear_failed_primary_list()
                self.peer_manager.set_primary_peer(socket_peer_id, is_out_going)
                self.send_report()

                if self.peer.using_web_gui:
                    Factory.instance().get_web_socket_handler().send_connection_change(True)
            else:
                self.peer_manager.append_failed_primary_list(socket_peer_id)
                self.recovery_connection()

    def received_set_candidate(self, sock, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING SET_CANDIDATE ', socket_peer_id, )
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING SET_CANDIDATE ', socket_peer_id)

        candidate_response_message = {
            'RspCode': MessageType.RESPONSE_SET_CANDIDATE
        }
        print('\n++++++++[HOPP] SEND SET_CANDIDATE RESPONSE', candidate_response_message)
        self.send_web_socket('SEND SET_CANDIDATE RESPONSE.')
        response_message = self.convert_message_to_bytes(candidate_response_message)

        self.sendall_tcp_message(sock, response_message)
        self.send_report()

    @classmethod
    def received_response_set_candidate(cls, is_out_going, socket_peer_id):
        # set_candidate 보낼때 self.send_report()를 한다.
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_SET_CANDIDATE ', socket_peer_id)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_SET_CANDIDATE ', socket_peer_id)
        cls.send_web_socket('RECEIVED SET_CANDIDATE RESPONSE.')

    def received_broadcast_data(self, sock, request_message, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING BROADCAST_DATA ', socket_peer_id)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING BROADCAST_DATA ', socket_peer_id)

        self.send_web_socket('RECEIVED BROADCAST_DATA.')
        Factory.instance().sendto_udp_socket(request_message.content)

        request_params = request_message.header.get('ReqParams')
        source_peer = request_params.get('peer').get('peer_id')
        print('\n++++++++[HOPP] SENDER:{0} / SOURCE:{1} / DATA=>{2}'.format(socket_peer_id, source_peer,
                                                                            request_message.content))
        if Factory.instance().get_peer().using_web_gui:
            Factory.instance().get_web_socket_handler().send_received_data(socket_peer_id, source_peer,
                                                                           request_message.content)

        if request_params.get('ack'):
            broadcast_data_response_message = {
                'RspCode': MessageType.RESPONSE_BROADCAST_DATA
            }
            print('\n++++++++[HOPP] SEND BROADCAST_DATA RESPONSE', broadcast_data_response_message)
            self.send_web_socket('SEND BROADCAST_DATA RESPONSE.')

            response_message = self.convert_message_to_bytes(broadcast_data_response_message)
            self.sendall_tcp_message(sock, response_message)

        if source_peer != self.peer.peer_id:
            self.relay_broadcast_data(socket_peer_id, request_message)

    @classmethod
    def received_response_broadcast_data(cls, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_BROADCAST_DATA ', socket_peer_id)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_BROADCAST_DATA ', socket_peer_id)
        cls.send_web_socket('RECEIVED BROADCAST_DATA RESPONSE.')

    def received_release_peer(self, sock, request_message, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RELEASE_PEER ', socket_peer_id)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RELEASE_PEER ', socket_peer_id)

        self.send_web_socket('RECEIVED RELEASE_PEER.')

        if request_message.header.get('ReqParams').get('operation').get('ack'):
            release_response_message = {
                'RspCode': MessageType.RESPONSE_RELEASE_PEER
            }
            print('\n++++++++[HOPP] SEND RELEASE_PEER RESPONSE', release_response_message)
            self.send_web_socket('SEND RELEASE_PEER RESPONSE.')

            response_message = self.convert_message_to_bytes(release_response_message)
            self.sendall_tcp_message(sock, response_message)
        else:
            self.close_tcp_connection(sock)

    @classmethod
    def received_response_release_peer(cls, sock, is_out_going, socket_peer_id):
        if is_out_going:
            print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_RELEASE_PEER ', socket_peer_id)
        else:
            print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_RELEASE_PEER ', socket_peer_id)

        cls.send_web_socket('RECEIVED RELEASE_PEER RESPONSE.')
        cls.close_tcp_connection(sock)

    def received_heartbeat(self, sock, is_out_going, socket_peer_id):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            if is_out_going:
                print('\n++++++++[HOPP] RECEIVED OUT_GOING HEARTBEAT ', socket_peer_id)
            else:
                print('\n++++++++[HOPP] RECEIVED IN_COMING HEARTBEAT ', socket_peer_id)

            self.send_web_socket('RECEIVED HEARTBEAT.')

        peer_connection: PeerConnection = self.peer_manager.get_peer_connection(socket_peer_id)
        if peer_connection is not None:
            peer_connection.update_time = datetime.now()

            release_response_message = {
                'RspCode': MessageType.RESPONSE_HEARTBEAT
            }
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n++++++++[HOPP] SEND HEARTBEAT RESPONSE', release_response_message)
                self.send_web_socket('SEND HEARTBEAT RESPONSE.')

            response_message = self.convert_message_to_bytes(release_response_message)
            self.sendall_tcp_message(sock, response_message)

    def received_response_heartbeat(self, is_out_going, socket_peer_id):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            if is_out_going:
                print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_HEARTBEAT ', socket_peer_id)
            else:
                print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_HEARTBEAT ', socket_peer_id)
            self.send_web_socket('RECEIVED HEARTBEAT RESPONSE.')

        peer_connection: PeerConnection = self.peer_manager.get_peer_connection(socket_peer_id)
        if peer_connection is not None:
            peer_connection.update_time = datetime.now()

    def received_scan_tree(self, request_message, is_out_going, socket_peer_id):
        if PEER_CONFIG['PRINT_SCAN_TREE_LOG']:
            if is_out_going:
                print('\n++++++++[HOPP] RECEIVED OUT_GOING SCAN_TREE ', socket_peer_id)
            else:
                print('\n++++++++[HOPP] RECEIVED IN_COMING SCAN_TREE ', socket_peer_id)
            self.send_web_socket('RECEIVED SCAN_TREE.')

        params_overlay = request_message.header.get('ReqParams').get('overlay')
        params_peer = request_message.header.get('ReqParams').get('peer')
        via_list = params_overlay.get('via')
        target_peer_id, target_peer_address = via_list[0]

        if self.peer.peer_id == target_peer_id:
            via_list.remove((target_peer_id, target_peer_address))

            if len(via_list) > 0:
                target_peer_id, target_peer_address = via_list[0]
            else:
                target_peer_id = None
                target_peer_address = None

        path_list = params_overlay.get('path')
        path_list.insert(0, (self.peer.peer_id, self.peer.get_address()))

        children_cnt = self.peer_manager.get_children_count()
        rsp_code = MessageType.RESPONSE_SCAN_TREE_NON_LEAF if children_cnt > 0 else MessageType.RESPONSE_SCAN_TREE_LEAF
        scan_tree_response_message = {
            'RspCode': rsp_code,
            'RspParams': {
                'overlay': {
                    'overlay_id': params_overlay.get('overlay_id'),
                    's_seq': params_overlay.get('s_seq'),
                    'via': via_list,
                    'path': path_list
                },
                'peer': {
                    'peer_id': params_peer.get('peer_id'),
                    'address': params_peer.get('address'),
                    'ticket_id': params_peer.get('ticket_id')
                }
            }
        }

        if PEER_CONFIG['PRINT_SCAN_TREE_LOG']:
            print('\n++++++++[HOPP] SEND SCAN_TREE RESPONSE', scan_tree_response_message)
            self.send_web_socket('SEND SCAN_TREE RESPONSE.')

        response_message = self.convert_message_to_bytes(scan_tree_response_message)
        self.peer_manager.send_message_to_peer(target_peer_id, response_message)

        if children_cnt > 0:
            scan_tree_message = {
                'ReqCode': MessageType.REQUEST_SCAN_TREE,
                'ReqParams': {
                    'overlay': {
                        'overlay_id': params_overlay.get('overlay_id'),
                        's_seq': params_overlay.get('s_seq'),
                        'via': via_list,
                        'path': path_list
                    },
                    'peer': {
                        'peer_id': params_peer.get('peer_id'),
                        'address': params_peer.get('address'),
                        'ticket_id': params_peer.get('ticket_id')
                    }
                }
            }
            if PEER_CONFIG['PRINT_SCAN_TREE_LOG']:
                print('\n++++++++[HOPP] SEND SCAN_TREE (RELAY)', scan_tree_response_message)
                self.send_web_socket('SEND SCAN_TREE (RELAY).')

            response_message = self.convert_message_to_bytes(scan_tree_message)
            self.peer_manager.broadcast_message(socket_peer_id, response_message)

    def received_response_scan_tree(self, is_out_going, socket_peer_id):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            if is_out_going:
                print('\n++++++++[HOPP] RECEIVED OUT_GOING RESPONSE_HEARTBEAT ', socket_peer_id)
            else:
                print('\n++++++++[HOPP] RECEIVED IN_COMING RESPONSE_HEARTBEAT ', socket_peer_id)
            self.send_web_socket('RECEIVED HEARTBEAT RESPONSE.')

        peer_connection: PeerConnection = self.peer_manager.get_peer_connection(socket_peer_id)
        if peer_connection is not None:
            peer_connection.update_time = datetime.now()

    ###################
    ###################

    @classmethod
    def send_hello_peer(cls, peer: Peer, target_address):
        if 'tcp://' in target_address:
            sock = None
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
                cls.send_web_socket('SEND HELLO_PEER.')

                request_message = cls.convert_message_to_bytes(hello_message)
                # cls.sendall_tcp_message(sock, request_message)
                sock.sendall(request_message)

                response_message: HoppMessage = cls.convert_bytes_to_message(sock)
                cls.send_web_socket('RECEIVED HELLO_PEER RESPONSE.')
                print('\n++++++++[HOPP] RECEIVED HELLO RESPONSE ', response_message.header)
                print('\n++++++++[HOPP] [{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                      sock.getsockname()[1]))
                cls.close_tcp_connection(sock)

                return True if response_message.header.get('RspCode') == MessageType.RESPONSE_HELLO_PEER else False
            except Exception as e:
                print('\n++++++++[HOPP] Error send_hello\n', e)
                cls.close_tcp_connection(sock)

                return None
        else:
            return None

    def send_estab_peer(self, peer: Peer, target_address):
        if 'tcp://' in target_address:
            sock = None
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
                self.send_web_socket('SEND ESTABLISH_PEER.')

                request_message = self.convert_message_to_bytes(establish_message)
                self.sendall_tcp_message(sock, request_message)

                response_message: HoppMessage = self.convert_bytes_to_message(sock)
                print('\n++++++++[HOPP] RECEIVED ESTABLISH RESPONSE', response_message.header)
                self.send_web_socket('RECEIVED ESTABLISH_PEER RESPONSE.')

                if response_message.header.get('RspCode') == MessageType.RESPONSE_ESTAB_PEER:
                    return sock
                elif response_message.header.get('RspCode') == MessageType.RESPONSE_ESTAB_PEER_ERROR:
                    print('\n++++++++[HOPP] [{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                          sock.getsockname()[1]))
                    self.close_tcp_connection(sock)
                    return None
                else:
                    print('\n++++++++[HOPP] [{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                          sock.getsockname()[1]))
                    self.close_tcp_connection(sock)
                    return None
            except Exception as e:
                print('\n++++++++[HOPP] Error send_establish\n', e)
                self.close_tcp_connection(sock)

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
            peer_manager.is_run_probe_peer = True
            estab_peers = peer_manager.get_estab_peers()

            if len(estab_peers) > 0:
                if PEER_CONFIG['PROBE_PEER_TIMEOUT'] > 0:
                    for peer_id in estab_peers.keys():
                        peer_connection: PeerConnection = peer_manager.get_peer_connection(peer_id)
                        if peer_connection is not None:
                            cls.send_probe_peer(peer_connection)

                    cls.run_probe_peer_timer()
                else:
                    cls.check_and_send_set_primary()
            else:
                # TODO 복구
                cls.send_web_socket('ESTAB_PEER is None.')
                print('\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
                print('++++++++[HOPP] ESTAB_PEER is None... 네트웨크에 참가 실패.')
                print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')

    @classmethod
    def send_probe_peer(cls, peer_connection: PeerConnection):
        probe_message = {
            'ReqCode': MessageType.REQUEST_PROBE_PEER,
            'ReqParams': {
                'operation': {
                    'ntp_time': str(datetime.now())
                }
            }
        }
        print('\n++++++++[HOPP] SEND PROBE_PEER REQUEST', probe_message)
        cls.send_web_socket('SEND PROBE_PEER.')

        request_message = cls.convert_message_to_bytes(probe_message)
        cls.sendall_tcp_message(peer_connection.connection, request_message)

    @classmethod
    def run_probe_peer_timer(cls):
        print('\n++++++++[HOPP] RUN_PROBE_PEER_TIMER')
        threading.Timer(PEER_CONFIG['PROBE_PEER_TIMEOUT'], cls.check_and_send_set_primary).start()

    @classmethod
    def check_and_send_set_primary(cls):
        peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peer_manager.is_run_primary_peer = True
        primary_peer_connection = None
        estab_peers = peer_manager.get_estab_peers()
        print('\n++++++++[HOPP] CHECK AND SEND SET_PRIMARY')

        if PEER_CONFIG['PROBE_PEER_TIMEOUT'] > 0:
            if len(estab_peers) < 1:
                print('\n++++++++[HOPP] Error... ESTAB_PEERS len = 0')
                return

            sorted_estab_peers = sorted(estab_peers.items(), key=operator.itemgetter(1))
            for estab_index, (peer_id, delta_time) in enumerate(sorted_estab_peers):
                peer_connection: PeerConnection = peer_manager.get_peer_connection(peer_id)
                if peer_connection is not None:
                    primary_peer_connection = peer_connection
                    break

        else:
            peer_manager.is_first_peer_set_primary = False

            if len(peer_manager.get_primary_list()) > 0:
                print('\n++++++++[HOPP] FIRST PEER SET_PRIMARY SUCCESS.')
                peer_manager.is_run_primary_peer = False
                if PEER_CONFIG['SEND_CANDIDATE']:  # optional
                    cls.send_to_all_set_candidate()
            else:
                print('\n++++++++[HOPP] FIRST PEER SET_PRIMARY FAILED... AND START SET_PRIMARY')
                for peer_id in peer_manager.get_out_going_candidate_list():
                    if peer_id in estab_peers.keys():
                        peer_connection: PeerConnection = peer_manager.get_peer_connection(peer_id)
                        if peer_connection is not None:
                            primary_peer_connection = peer_connection
                            break

        if primary_peer_connection is not None:
            peer_manager.delete_establish_peer(primary_peer_connection.peer_id)
            cls.send_set_primary(primary_peer_connection)

    def send_set_primary_is_skip_probe(self, sock):
        if not self.peer_manager.is_first_peer_set_primary:
            self.peer_manager.is_first_peer_set_primary = True

            primary_message = {
                'ReqCode': MessageType.REQUEST_SET_PRIMARY
            }
            print('\n++++++++[HOPP] SEND SET_PRIMARY REQUEST(SKIP_PROBE)', primary_message)
            request_message = self.convert_message_to_bytes(primary_message)
            self.sendall_tcp_message(sock, request_message)

    @classmethod
    def send_set_primary(cls, peer_connection: PeerConnection):
        primary_message = {
            'ReqCode': MessageType.REQUEST_SET_PRIMARY
        }
        print('\n++++++++[HOPP] SEND SET_PRIMARY REQUEST', primary_message)
        cls.send_web_socket('SEND SET_PRIMARY.')

        request_message = cls.convert_message_to_bytes(primary_message)
        cls.sendall_tcp_message(peer_connection.connection, request_message)

    @classmethod
    def send_to_all_set_candidate(cls):
        print('\n++++++++[HOPP] SEND TO ALL SET CANDIDATE')
        peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        estab_peers = peer_manager.get_estab_peers()
        if len(estab_peers) > 0:
            for peer_id in estab_peers.keys():
                peer_connection: PeerConnection = peer_manager.get_peer_connection(peer_id)
                if peer_connection is not None:
                    cls.send_set_candidate(peer_connection)

        peer_manager.clear_estab_peers()

    @classmethod
    def send_set_candidate(cls, peer_connection: PeerConnection):
        candidate_message = {
            'ReqCode': MessageType.REQUEST_SET_CANDIDATE
        }
        print('\n++++++++[HOPP] SEND SET_CANDIDATE REQUEST', candidate_message)
        cls.send_web_socket('SEND SET_CANDIDATE.')

        request_message = cls.convert_message_to_bytes(candidate_message)
        cls.sendall_tcp_message(peer_connection.connection, request_message)

    @classmethod
    def send_broadcast_data(cls, peer: Peer, send_data, is_ack=None):
        Factory.instance().sendto_udp_socket(send_data)
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()

        if get_peer_manager.has_primary():
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
            cls.send_web_socket('SEND BROADCAST_DATA.')

            request_message = cls.convert_message_to_bytes(data_message, bytes_data)
            get_peer_manager.send_message(request_message)

    def relay_broadcast_data(self, sender, hopp_message: HoppMessage):
        print('\n++++++++[HOPP] RELAY BROADCAST_DATA REQUEST', hopp_message.header)
        # self.send_web_socket('RELAY BROADCAST_DATA.')

        bytes_data = self.convert_to_bytes(hopp_message.content)
        request_message = self.convert_message_to_bytes(hopp_message.header, bytes_data)
        self.peer_manager.broadcast_message(sender, request_message)

    @classmethod
    def send_release_peer(cls, peer_id, is_ack=None):
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peer_connection: PeerConnection = get_peer_manager.get_peer_connection(peer_id)
        operation_ack = is_ack if is_ack is not None else PEER_CONFIG['RELEASE_OPERATION_ACK']

        if peer_connection is not None:
            release_message = {
                'ReqCode': MessageType.REQUEST_RELEASE_PEER,
                'ReqParams': {
                    'operation': {
                        'ack': operation_ack
                    }
                }
            }

            print('\n++++++++[HOPP] SEND RELEASE_PEER REQUEST', release_message)
            cls.send_web_socket('SEND RELEASE_PEER.')

            request_message = cls.convert_message_to_bytes(release_message)
            cls.sendall_tcp_message(peer_connection.connection, request_message)

            if not operation_ack:
                cls.close_tcp_connection(peer_connection.connection)
        else:
            print('\n++++++++[HOPP] RELEASE_PEER -- NOT EXIST PEER', peer_id)

    @classmethod
    def send_to_all_release_peer(cls):
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        if get_peer_manager.is_destroy:
            return

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
            cls.send_web_socket('SEND TO ALL RELEASE_PEER.')

            request_message = cls.convert_message_to_bytes(release_message)

            peer_list = list(peers.keys())
            for peer_id in peer_list:
                peer_connection: PeerConnection = peers[peer_id]
                cls.sendall_tcp_message(peer_connection.connection, request_message)

                if not operation_ack:
                    cls.close_tcp_connection(peer_connection.connection)

    @classmethod
    def run_heartbeat_scheduler(cls):
        if Factory.instance().is_used_tcp():
            get_peer: Peer = Factory.instance().get_peer()
            scheduler: ClientScheduler = Factory.instance().get_client_scheduler()
            scheduler.append_heartbeat_scheduler(get_peer.heartbeat_interval, cls.send_to_all_heartbeat,
                                                 get_peer.heartbeat_timeout, cls.check_connection_heartbeat)

    @classmethod
    def send_heartbeat(cls, peer_id):
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peer_connection: PeerConnection = get_peer_manager.get_peer_connection(peer_id)
        get_peer: Peer = Factory.instance().get_peer()

        if peer_connection is not None:
            if (peer_connection.is_primary and get_peer.ticket_id > peer_connection.ticket_id) or \
                    peer_connection.peer_id in get_peer_manager.get_out_going_candidate_list():
                heartbeat_message = {
                    'ReqCode': MessageType.REQUEST_HEARTBEAT
                }
                if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                    print('\n++++++++[HOPP] SEND HEARTBEAT REQUEST', heartbeat_message, peer_connection.peer_id)
                    cls.send_web_socket('SEND HEARTBEAT.')

                request_message = cls.convert_message_to_bytes(heartbeat_message)
                cls.sendall_tcp_message(peer_connection.connection, request_message)
        else:
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n++++++++[HOPP] HEARTBEAT -- NOT EXIST PEER', peer_id)

    @classmethod
    def send_to_all_heartbeat(cls):
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peers = get_peer_manager.get_all_peer_connection()
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n----------[Heartbeat] SEND TO ALL Heartbeat')

        if get_peer_manager.is_send_heartbeat:
            if len(peers) > 0:
                for peer_id in peers.keys():
                    cls.send_heartbeat(peer_id)
        else:
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n----------[Heartbeat] NOT WORK send_heartbeat')

    @classmethod
    def check_connection_heartbeat(cls):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n----------[Heartbeat] CHECK CONNECTION Heartbeat')

        get_peer: Peer = Factory.instance().get_peer()
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        peers = get_peer_manager.get_all_peer_connection()

        for p_value in peers.values():
            if type(p_value) == PeerConnection:
                peer_connection: PeerConnection = p_value
                update_time = datetime.strptime(str(peer_connection.update_time), cls.fmt)
                now_time = datetime.strptime(str(datetime.now()), cls.fmt)
                delta_time = now_time - update_time
                if delta_time.seconds > get_peer.heartbeat_timeout:
                    if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                        print('\n----------[Heartbeat] Connection is not alive =>', peer_connection.peer_id)
                        print('\n----------[Heartbeat] Disconnection Socket =>', peer_connection.peer_id)

                    cls.close_tcp_connection(peer_connection.connection)
                else:
                    if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                        print('\n----------[Heartbeat] Connection is alive =>', peer_connection.peer_id)

    def send_recovery_hello_peer(self, peer: Peer, target_address):
        if 'tcp://' in target_address:
            sock = None
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
                self.send_web_socket('SEND HELLO_PEER (RECOVERY).')

                request_message = self.convert_message_to_bytes(hello_recovery_message)
                self.sendall_tcp_message(sock, request_message)

                response_message: HoppMessage = self.convert_bytes_to_message(sock)
                print('\n++++++++[HOPP] RECEIVED HELLO (RECOVERY) RESPONSE ', response_message.header)
                print('\n++++++++[HOPP] [{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0],
                                                                                      sock.getsockname()[1]))
                self.send_web_socket('RECEIVED HELLO_PEER RESPONSE(RECOVERY).')

                self.close_tcp_connection(sock)

                return True if response_message.header.get('RspCode') == MessageType.RESPONSE_HELLO_PEER else False
            except Exception as e:
                print('\n++++++++[HOPP] Error send_hello (RECOVERY) \n', e)
                self.close_tcp_connection(sock)

                return None
        else:
            return None

    @classmethod
    def send_scan_tree(cls, peer: Peer):
        peer.scan_tree_sequence += 1
        scan_tree_message = {
            'ReqCode': MessageType.REQUEST_SCAN_TREE,
            'ReqParams': {
                'overlay': {
                    'overlay_id': peer.overlay_id,
                    's_seq': peer.scan_tree_sequence,
                    'via': [(peer.peer_id, peer.get_address())],
                    'path': []
                },
                'peer': {
                    'peer_id': peer.peer_id,
                    'address': peer.get_address(),
                    'ticket_id': peer.ticket_id
                }
            }
        }
        print('\n++++++++[HOPP] SEND SCAN_TREE REQUEST', scan_tree_message)
        cls.send_web_socket('SEND SCAN_TREE.')

        request_message = cls.convert_message_to_bytes(scan_tree_message)
        get_peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        get_peer_manager.send_message(request_message)

    #####################################################
    #####################################################

    def run_recovery_scheduler(self):
        scheduler: ClientScheduler = Factory.instance().get_client_scheduler()
        scheduler.append_checked_primary_scheduler(PEER_CONFIG['CHECKED_PRIMARY_INTERVAL'],
                                                   self.checked_primary_connection)

    def checked_primary_connection(self):
        if self.peer.is_top_peer or self.peer.isOwner:
            scheduler: ClientScheduler = Factory.instance().get_client_scheduler()
            scheduler.remove_checked_primary_scheduler()
            return

        if PEER_CONFIG['PRINT_CHECKED_PRIMARY_LOG']:
            print('\n++++++++[HOPP] Run checked_my_primary_connection')

        find_parent_primary = False
        remove_primary_id_list = []
        for peer_id in self.peer_manager.get_primary_list():
            peer_connection: PeerConnection = self.peer_manager.get_peer_connection(peer_id)
            if peer_connection.ticket_id < self.peer.ticket_id and peer_connection.is_primary \
                    and peer_connection.is_parent:
                if find_parent_primary:
                    remove_primary_id_list.append(peer_connection.peer_id)
                find_parent_primary = True

        if not find_parent_primary:
            if PEER_CONFIG['PRINT_CHECKED_PRIMARY_LOG']:
                print('\n++++++++[HOPP] Primary Connection is None...')

            self.recovery_connection()
        elif len(remove_primary_id_list) > 0:
            if PEER_CONFIG['PRINT_CHECKED_PRIMARY_LOG']:
                print('\n++++++++[HOPP] Primary Connection Error and remove_peer...')

            for remove_peer_id in remove_primary_id_list:
                self.send_release_peer(remove_peer_id)
        else:
            if PEER_CONFIG['PRINT_CHECKED_PRIMARY_LOG']:
                print('\n++++++++[HOPP] Primary Connection is OK!!!!!!...')


class TcpThreadingSocketServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

import threading
import math
import json
import operator
from datetime import datetime
import asyncio
import uuid
import random

from data.factory import Factory, Peer
from config import CLIENT_CONFIG, PEER_CONFIG
from rtc.rtcdata import RTCData
from classes.constants import MessageType
from homp.homp_message_handler import HompMessageHandler
from data.client_scheduler import ClientScheduler
from classes.hopp_message import HoppMessage


class RtcHp2pClient:
    def __init__(self):
        self.message_delay = 1
        self.peer: Peer = Factory.instance().get_peer()
        self.handler: HompMessageHandler = Factory.instance().get_homp_handler()
        self._rtc_data = None
        self.join_peer_list = []
        self.fmt = "%Y-%m-%d %H:%M:%S.%f"
        self._s_flag = False
        self.retry_count = 0
        self.is_process_client = False
        self._byteorder = 'little'
        self._encoding = 'utf=8'
        self._hello_ticket_code = -1
        self._recovery_hello_ticket_code = -2
        self._hello_peer_id = None
        self._hello_peer_success = False
        self.is_run_recovery = False
        self.received_hello_check_interval = 20
        self.received_recovery_hello_check_interval = 20
        Factory.instance().set_rtc_hp2p_client(self)

    # Client handle  ############################################################
    ###################################################################################
    def client_start(self):
        try:
            web_socket_ip = CLIENT_CONFIG['WEB_SOCKET_SERVER_IP']
            web_socket_port = CLIENT_CONFIG['WEB_SOCKET_SERVER_PORT']

            self.peer.set_web_socket_server_info(web_socket_ip, web_socket_port)
            self.set_rtc_data(RTCData(self.peer.peer_id))
            self.get_rtc_data().connect_signal_server(web_socket_ip, web_socket_port)
            self.web_socket_send_hello()

            threading.Timer(1, self.run_auto_client).start()
        except Exception as e:
            print('failed connect signal server.', e)

    def client_end(self):
        self.handler.leave(self.peer)
        self.web_socket_send_bye()
        self.send_to_all_release_peer()
        threading.Timer(3, self.get_rtc_data().close).start()

        scheduler: ClientScheduler = Factory.instance().get_client_scheduler()
        if scheduler is not None:
            print('\n Scheduler Stop...')
            scheduler.stop()

        public_data_listener = Factory.instance().get_public_data_listener()
        if public_data_listener is not None:
            print('\nPublic Data Listening Server Shutdown')

            for sock in public_data_listener.get_socket_list():
                sock.close()

            public_socket_server = public_data_listener.get_public_socket_server()
            if public_socket_server is not None:
                public_socket_server.shutdown()
                public_socket_server.server_close()

        print("__END__")

    def run_auto_client(self):
        print('Run Client')
        self.auto_creation_and_join()

    def failed_join(self):
        print('\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        print('++++++++[HOPP] Overlay 네트웨크에 참가 실패.')
        print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
        self.client_end()

    def retry_join(self, is_joined, message):
        print(message)

        if PEER_CONFIG['RETRY_OVERLAY_JOIN']:
            self.retry_count += 1
            if is_joined:
                self.handler.leave(self.peer)

            if self.retry_count <= PEER_CONFIG['RETRY_OVERLAY_JOIN_COUNT']:
                threading.Timer(PEER_CONFIG['RETRY_OVERLAY_JOIN_INTERVAL'], self.auto_creation_and_join).start()
            else:
                self.failed_join()
        else:
            self.failed_join()

    def auto_creation_and_join(self):
        print('Creation or Join')
        if self.peer.isOwner:
            self.handler.creation(self.peer)
            self.handler.join(self.peer)
            self.get_rtc_data().set_ticket_id(self.peer.ticket_id)
            self.send_report()
            # self.handler.modification(self.peer) - 사용안함

            self.run_expires_scheduler(self.peer.peer_expires)
            self.run_heartbeat_scheduler()
            self.simple_process_client()
        else:
            if self.peer.overlay_id is None:
                overlay_list = self.handler.query()
                if len(overlay_list) > 0:
                    overlay = overlay_list[len(overlay_list) - 1]
                    self.peer.overlay_id = overlay.get('overlay_id')
                else:
                    print('overlay List is None')
                    self.client_end()
                    return

            join_response = self.handler.join(self.peer)
            if join_response is None:
                self.retry_join(False, "join_response is None.")
            else:
                self.get_rtc_data().set_ticket_id(self.peer.ticket_id)
                self.run_expires_scheduler(self.peer.peer_expires)
                self.run_heartbeat_scheduler()

                if len(join_response) > 0:
                    self.rtc_connect_to_peer(join_response[0], self._hello_ticket_code)
                else:
                    self.retry_join(True, "Server Error")
                    # self.send_report() - 사용안함

    def rtc_connect_to_peer(self, peer_info, ticket_code):
        target_peer_id = peer_info.get('peer_id')
        target_address = peer_info.get('address')

        if self.peer.peer_id == target_peer_id:
            self.peer.is_top_peer = True
            print("Top Peer.", flush=True)
            self.send_gui_web_socket('TOP PEER.')
        else:
            print("Join.", target_peer_id, target_address, flush=True)
            self.send_gui_web_socket("Join ID:{0}, Address:{1}".format(target_peer_id, target_address))
            self._hello_peer_success = False
            self._hello_peer_id = target_peer_id
            self.get_rtc_data().connect_to_peer(self._hello_peer_id, ticket_code)
            threading.Timer(self.received_hello_check_interval, self.checked_received_hello).start()

    def checked_received_hello(self):
        if self._hello_peer_success:
            self.simple_process_client()
        else:
            self.retry_join(True, "Failed Join.")

    def simple_process_client(self):
        if self.is_process_client:
            return

        print('Process Client.')
        self.is_process_client = True
        try:
            while True:
                input_method = input("")

                if input_method.lower() == '/end' or input_method.lower() == '0':  # 종료
                    break
                elif input_method.lower() == '/show' or input_method.lower() == '/s':  # 연결상태 확인
                    print(
                        '\n*******************************************************************************************')
                    print('Peer ID => {0}   &&&   Ticket ID => {1}'.format(self.peer.peer_id, self.peer.ticket_id))
                    if self.peer.using_web_gui:
                        print('GUI URL=> localhost:{0}'.format(self.peer.gui_server_port))
                    if self.peer.public_data_port is not None:
                        print('Public Data Listening Server => localhost:{0}'.format(self.peer.public_data_port))
                    print('PRIMARY_LIST', self.get_peer_manager().get_primary_list())
                    print('IN_CANDIDATE_LIST', self.get_peer_manager().get_in_coming_candidate_list())
                    print('OUT_CANDIDATE_LIST', self.get_peer_manager().get_out_going_candidate_list())
                    print(
                        '*******************************************************************************************\n')
                elif input_method.lower() == '/data' or input_method.lower() == '/d':  # 데이터 전송
                    send_data = input("Message =>")
                    self.send_broadcast_data(send_data)
                else:
                    print("")
        except Exception as e:
            print(e)
        finally:
            self.client_end()

    def run_expires_scheduler(self, interval):
        self._s_flag = False
        scheduler: ClientScheduler = Factory.instance().get_client_scheduler()
        scheduler.append_expires_scheduler(int(interval / 2), self.send_overlay_refresh)

    def send_overlay_refresh(self):
        if not self._s_flag:
            self._s_flag = True
            self.handler.refresh(self.peer)
            self._s_flag = False

    # def check_and_send_hello_peer(self, is_recovery=False):  # 사용 미정
    #     if len(self.join_peer_list) > 0:
    #         peer_info = self.join_peer_list.pop()
    #         target_peer_id = peer_info.get('peer_id')
    #         target_address = peer_info.get('address')
    #         print("Join...", target_peer_id, target_address, flush=True)
    #         # if not is_recovery:
    #         # # self.get_rtc_data().connect_to_peer(target_peer_id, target_ticket_id)
    #         # # self.send_hello_peer(target_peer_id)
    #     #         # else:
    #     #         #     # self.send_recovery_hello_peer(target_peer_id)
    #     #     elif not is_recovery:
    #         self.retry_join(True, "Failed Join.")

    # GUI Message handle  #######################################################
    ###################################################################################
    def send_gui_web_socket(self, message):
        try:
            if self.peer.using_web_gui:
                Factory.instance().get_web_socket_handler().send_log_message(message)
        except Exception as e:
            print('\n++++++++[HOPP] failed send_web_socket... ', e)

    # HOMP Message handle  #######################################################
    ###################################################################################
    def send_report(self):
        self.handler.report(self.peer, self.get_peer_manager())

    # Schedule Message handle  #######################################################
    ###################################################################################
    def run_heartbeat_scheduler(self):
        if Factory.instance().is_used_rtc():
            scheduler: ClientScheduler = Factory.instance().get_client_scheduler()
            scheduler.append_heartbeat_scheduler(self.peer.heartbeat_interval, self.send_to_all_heartbeat,
                                                 self.peer.heartbeat_timeout, self.check_connection_heartbeat)

    def check_connection_heartbeat(self):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n----------[Heartbeat] CHECK CONNECTION Heartbeat')

        peers = self.get_peer_manager().get_all_peer_connection()
        for peer_connection in peers.values():
            update_time = datetime.strptime(str(peer_connection.update_time), self.fmt)
            now_time = datetime.strptime(str(datetime.now()), self.fmt)
            delta_time = now_time - update_time
            if delta_time.seconds > self.peer.heartbeat_timeout:
                if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                    print('\n----------[Heartbeat] Connection is not alive =>', peer_connection.connectedId)
                    print('\n----------[Heartbeat] Disconnection Socket =>', peer_connection.connectedId)

                self.get_rtc_data().disconnect_to_peer(peer_connection.connectedId)
            else:
                if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                    print('\n----------[Heartbeat] Connection is alive =>', peer_connection.connectedId)

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
        for peer_id in self.get_peer_manager().get_primary_list():
            peer_connection = self.get_peer_manager().get_peer_connection(peer_id)
            if peer_connection.ticket_id < self.peer.ticket_id and peer_connection.is_primary \
                    and peer_connection.is_parent:
                if find_parent_primary:
                    remove_primary_id_list.append(peer_connection.connectedId)
                find_parent_primary = True

        if not find_parent_primary:
            if PEER_CONFIG['PRINT_CHECKED_PRIMARY_LOG']:
                print('\n++++++++[HOPP] Primary Connection is None...')

            self.recovery_connection_sync()
        elif len(remove_primary_id_list) > 0:
            if PEER_CONFIG['PRINT_CHECKED_PRIMARY_LOG']:
                print('\n++++++++[HOPP] Primary Connection Error and remove_peer...')

            for remove_peer_id in remove_primary_id_list:
                self.send_release_peer_sync(remove_peer_id)
        else:
            if PEER_CONFIG['PRINT_CHECKED_PRIMARY_LOG']:
                print('\n++++++++[HOPP] Primary Connection is OK!!!!!!...')

    def send_set_primary_sync(self, target_peer_id):
        primary_message = {
            'ReqCode': MessageType.REQUEST_SET_PRIMARY
        }
        print('\n++++++++[HOPP] SEND SET_PRIMARY REQUEST / ID:', target_peer_id)
        self.send_gui_web_socket('SEND SET_PRIMARY / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(primary_message)
        self.get_rtc_data().send(target_peer_id, request_message)

    def recovery_connection_sync(self):
        if self.is_run_recovery:
            print('\n++++++++[HOPP] Already to IS_RUN_RECOVERY...')
            return

        self.is_run_recovery = True
        print('\n++++++++[HOPP] START Recovery Connection...')
        self.send_gui_web_socket('START RECOVER_CONNECTION.')

        new_primary_peer_id = None
        for peer_id in self.get_peer_manager().get_out_going_candidate_list():
            if not self.get_peer_manager().is_peer_in_failed_primary_list(peer_id):
                peer_connection = self.get_peer_manager().get_peer_connection(peer_id)
                if peer_connection.ticket_id < self.peer.ticket_id and peer_connection.is_parent:
                    new_primary_peer_id = peer_connection.connectedId
                    break

        if new_primary_peer_id is not None:
            self.send_set_primary_sync(new_primary_peer_id)
        else:
            self.recovery_join_sync()

        print('\n++++++++[HOPP] End Recovery Connection...')
        self.is_run_recovery = False

    def send_release_peer_sync(self, target_peer_id, is_ack=None):
        operation_ack = is_ack if is_ack is not None else PEER_CONFIG['RELEASE_OPERATION_ACK']
        release_message = {
            'ReqCode': MessageType.REQUEST_RELEASE_PEER,
            'ReqParams': {
                'operation': {
                    'ack': operation_ack
                }
            }
        }
        print('\n++++++++[HOPP] SEND RELEASE PEER REQUEST / ID:', target_peer_id)
        self.send_gui_web_socket('SEND RELEASE_PEER / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(release_message)
        self.get_rtc_data().send(target_peer_id, request_message)

        if not operation_ack:
            self.get_rtc_data().disconnect_to_peer(target_peer_id)

    # WebSocket Message handle  #######################################################
    ###################################################################################
    def web_socket_send_hello(self):
        hello_message = {
            'action': 'hello',
            'peer_id': self.peer.peer_id
        }
        self.get_rtc_data().send_to_server(hello_message)

    def web_socket_send_bye(self):
        bye_message = {
            'action': 'bye',
            'peer_id': self.peer.peer_id
        }
        self.get_rtc_data().send_to_server(bye_message)

    # WebRtc Message handle  #######################################################
    ################################################################################
    def get_rtc_data(self) -> RTCData:
        return self._rtc_data

    def set_rtc_data(self, rtc_data: RTCData):
        rtc_data.on('message', self.__on_message)
        rtc_data.on('connection', self.__on_connection)
        self._rtc_data = rtc_data

    def get_peer_manager(self):
        return self.get_rtc_data().get_collection()

    def reassignment_connections_for_recovery(self, peer_id, ticket_id):
        return self.get_peer_manager().get_in_candidate_remove_peer_id(peer_id, ticket_id)

    async def __on_connection(self, sender):
        print('[Connection {0}] => {1}'.format("Open" if sender.isDataChannelOpened else "Closed",
                                               sender.to_information()))

        if sender.ticket_id < 0:  # Hello 를 위한 연결인 경우
            if self._hello_ticket_code == sender.ticket_id:
                print('[__on_connection] ==> send_hello_peer ')
                await self.send_hello_peer(sender.connectedId)

                if not self.peer.is_top_peer and not self.peer.isOwner and \
                        not Factory.instance().get_client_scheduler().is_set_checked_primary_scheduler():
                    print('[__on_connection] ==> run_recovery_scheduler ')
                    self.run_recovery_scheduler()
            elif self._recovery_hello_ticket_code == sender.ticket_id:
                print('[__on_connection] ==> send_recovery_hello_peer ')
                await self.send_recovery_hello_peer(sender.connectedId)
        else:
            if sender.isDataChannelOpened:
                if self.get_peer_manager().is_in_in_coming_candidate_list(
                        sender.connectedId) and self.peer.ticket_id < sender.ticket_id:
                    print('[__on_connection] ==> send_estab_peer ')
                    await self.send_estab_peer(sender.connectedId)
            else:
                print('[__on_connection] ==> check_and_recovery_primary ')
                await self.check_and_recovery_primary(sender)

            self.send_report()

    def set_tree_sequence(self):
        uuid_str = str(uuid.uuid1())
        keys = uuid_str.split('-')
        self.peer.scan_tree_sequence = keys[0] + "#" + str(random.randrange(1, 99))

    async def run_probe_peer_timer(self):
        print('\n++++++++[HOPP] RUN_PROBE_PEER_TIMER')
        await asyncio.sleep(PEER_CONFIG['PROBE_PEER_TIMEOUT'])
        await self.check_and_send_set_primary()

    async def check_and_send_set_primary(self):
        print('\n++++++++[HOPP] CHECK AND SEND SET_PRIMARY')
        self.get_peer_manager().is_run_primary_peer = True
        estab_peers = self.get_peer_manager().get_estab_peers()
        primary_peer_id = None

        if PEER_CONFIG['PROBE_PEER_TIMEOUT'] > 0:
            if len(estab_peers) < 1:
                print('\n++++++++[HOPP] Error... ESTAB_PEERS len = 0')
                return

            sorted_estab_peers = sorted(estab_peers.items(), key=operator.itemgetter(1))
            for estab_index, (peer_id, delta_time) in enumerate(sorted_estab_peers):
                connection = self.get_peer_manager().get_peer_connection(peer_id)
                if connection is not None and connection.isDataChannelOpened:
                    primary_peer_id = peer_id
        else:
            self.get_peer_manager().is_first_peer_set_primary = False

            if len(self.get_peer_manager().get_primary_list()) > 0:
                print('\n++++++++[HOPP] FIRST PEER SET_PRIMARY SUCCESS.')
                self.get_peer_manager().is_run_primary_peer = False
                if PEER_CONFIG['SEND_CANDIDATE']:  # optional
                    await self.send_to_all_set_candidate()
            else:
                print('\n++++++++[HOPP] FIRST PEER SET_PRIMARY FAILED... AND START SET_PRIMARY')
                for peer_id in self.get_peer_manager().get_out_going_candidate_list():
                    if peer_id in estab_peers.keys():
                        connection = self.get_peer_manager().get_peer_connection(peer_id)
                        if connection is not None and connection.isDataChannelOpened:
                            primary_peer_id = peer_id
                            break

        if primary_peer_id is not None:
            print('primary_peer_id', primary_peer_id)
            self.get_peer_manager().delete_establish_peer(primary_peer_id)
            await self.send_set_primary(primary_peer_id)
        else:
            self.get_peer_manager().is_run_primary_peer = False

    async def relay_broadcast_data(self, target_peer_id, message):
        print('\n++++++++[HOPP] RELAY BROADCAST_DATA REQUEST')

        bytes_data = self.convert_to_bytes(message.content)
        request_message = self.convert_message_to_bytes(message.header, bytes_data)
        await self.get_rtc_data().send_broadcast_message_other_async(target_peer_id, request_message)

    def success_set_primary(self, target_peer_id, is_outgoing):
        self.get_peer_manager().set_primary_peer(target_peer_id, is_outgoing)
        self.send_report()

        if self.peer.using_web_gui:
            Factory.instance().get_web_socket_handler().send_connection_change(True)

    async def check_and_recovery_primary(self, sender):
        if not self.get_peer_manager().has_primary() and self.peer.using_web_gui:
            Factory.instance().get_web_socket_handler().send_connection_change(False)

        if not self.get_peer_manager().is_destroy:
            if sender is not None and sender.ticket_id < self.peer.ticket_id and sender.is_primary and sender.is_parent:
                print('\n++++++++[HOPP] check_and_recovery_primary ==> recovery_connection (ASYNC)*********')
                await self.recovery_connection()

            self.send_report()

    async def run_estab_peer_timer(self):
        print('\n++++++++[HOPP] RUN_ESTAB_PEER_TIMER')
        await asyncio.sleep(PEER_CONFIG['ESTAB_PEER_TIMEOUT'])
        await self.send_to_all_probe_peer()

    async def recovery_connection(self):
        if self.is_run_recovery:
            print('\n++++++++[HOPP] Already to IS_RUN_RECOVERY...(ASYNC)*********')
            return

        self.is_run_recovery = True
        print('\n++++++++[HOPP] START Recovery Connection...(ASYNC)*********')
        self.send_gui_web_socket('RECOVER_CONNECTION(ASYNC)')

        new_primary_peer_id = None
        for peer_id in self.get_peer_manager().get_out_going_candidate_list():
            if not self.get_peer_manager().is_peer_in_failed_primary_list(peer_id):
                peer_connection = self.get_peer_manager().get_peer_connection(peer_id)
                if peer_connection.ticket_id < self.peer.ticket_id and peer_connection.is_parent:
                    new_primary_peer_id = peer_connection.connectedId
                    break

        if new_primary_peer_id is not None:
            await self.send_set_primary(new_primary_peer_id)
        else:
            await self.recovery_join()

        print('\n++++++++[HOPP] End Recovery Connection...(ASYNC)*********')
        self.is_run_recovery = False

    async def recovery_join(self):
        print('\n++++++++[HOPP] SEND RECOVERY HELLO (ASYNC)*********')
        self.send_gui_web_socket('SEND RECOVERY HELLO(ASYNC)')

        self.get_peer_manager().is_run_probe_peer = False
        self.get_peer_manager().is_run_primary_peer = False
        self.get_peer_manager().is_first_peer_set_primary = False

        recovery_response = self.handler.recovery(self.peer)

        if recovery_response is None:
            print('\n++++++++[HOPP] Failed RECOVERY JOIN(ASYNC)')
            self.send_gui_web_socket('FAILED RECOVERY JOIN(ASYNC)')
        else:
            if len(recovery_response) > 0:
                target_peer_id = recovery_response[0].get('peer_id')
                target_address = recovery_response[0].get('address')

                if self.peer.peer_id == target_peer_id:
                    self.peer.is_top_peer = True
                    print("Top Peer(ASYNC)", flush=True)
                    self.send_gui_web_socket('TOP PEER(ASYNC)')
                else:
                    print("Join(ASYNC)", target_peer_id, target_address, flush=True)
                    self.send_gui_web_socket("Join(ASYNC) ID:{0}, Address:{1}".format(target_peer_id, target_address))
                    self._hello_peer_id = target_peer_id
                    self._hello_peer_success = False
                    await self.get_rtc_data().connect_to_peer_async(self._hello_peer_id,
                                                                    self._recovery_hello_ticket_code)
            else:
                self.send_gui_web_socket('RECOVERY JOIN LIST IS NONE(ASYNC)')

    def recovery_join_sync(self):
        print('\n++++++++[HOPP] SEND RECOVERY HELLO')
        self.send_gui_web_socket('SEND RECOVERY HELLO')

        self.get_peer_manager().is_run_probe_peer = False
        self.get_peer_manager().is_run_primary_peer = False
        self.get_peer_manager().is_first_peer_set_primary = False

        recovery_response = self.handler.recovery(self.peer)

        if recovery_response is None:
            print('\n++++++++[HOPP] Failed RECOVERY JOIN')
            self.send_gui_web_socket('FAILED RECOVERY JOIN')
        else:
            if len(recovery_response) > 0:
                self.rtc_connect_to_peer(recovery_response[0], self._recovery_hello_ticket_code)
            else:
                self.send_gui_web_socket('RECOVERY JOIN LIST IS NONE')

    def convert_bytes_to_message(self, byte_list):
        try:
            offset = 0
            message = HoppMessage()
            received_buffer = byte_list[offset:offset + 1]
            message.version = int.from_bytes(received_buffer, self._byteorder)
            offset = 1
            received_buffer = byte_list[offset:offset + 1]
            message.type = int.from_bytes(received_buffer, self._byteorder)
            offset = 2
            received_buffer = byte_list[offset:offset + 2]
            message.length = int.from_bytes(received_buffer, self._byteorder)
            offset = 4
            received_buffer = byte_list[offset:offset + message.length]
            message.header = json.loads(str(received_buffer, encoding=self._encoding))

            if 'ReqCode' in message.header:
                message.message_type = message.header.get('ReqCode')
            elif 'RspCode' in message.header:
                message.message_type = message.header.get('RspCode')
            else:
                return None

            if message.message_type == MessageType.REQUEST_BROADCAST_DATA:
                offset = 4 + message.length
                content_length = message.header.get('ReqParams').get('payload').get('length')
                received_buffer = byte_list[offset:offset + content_length]
                message.content = str(received_buffer, encoding=self._encoding)

            return message
        except Exception as e:
            print('\n++++++++[HOPP] Error convert_bytes_to_message\n', e)
            return None

    def convert_to_bytes(self, data):
        try:
            bytes_data = bytes(data, encoding=self._encoding)
            return bytes_data
        except Exception as e:
            print('\n++++++++[HOPP] Error convert_data_to_bytes\n', e)
            return None

    def convert_data_to_bytes(self, data):
        try:
            bytes_data = bytes(data, encoding=self._encoding)
            bytes_length = len(bytes_data)
            return bytes_data, bytes_length
        except Exception as e:
            print('\n++++++++[HOPP] Error convert_data_to_bytes\n', e)
            return None

    def convert_message_to_bytes(self, message, bytes_data=None):
        try:
            bytes_version = MessageType.VERSION.to_bytes(1, self._byteorder)
            bytes_type = MessageType.TYPE.to_bytes(1, self._byteorder)
            bytes_header = bytes(json.dumps(message), encoding=self._encoding)
            bytes_length = len(bytes_header).to_bytes(2, self._byteorder)
            if bytes_data is None:
                return bytes_version + bytes_type + bytes_length + bytes_header
            else:
                return bytes_version + bytes_type + bytes_length + bytes_header + bytes_data
        except Exception as e:
            print('\n++++++++[HOPP] Error convert_message_to_bytes\n', e)
            return None

    async def __on_message(self, sender, bytes_msg):
        message: HoppMessage = self.convert_bytes_to_message(bytes_msg)
        # print('\nRtcHp2pClient sender => ', sender.connectedId)

        # HELLO_PEER
        if MessageType.REQUEST_HELLO_PEER == message.message_type:
            estab_peer = await self.received_hello_peer(sender.connectedId, message.header)
            if sender.is_primary:
                await self.get_rtc_data().connect_to_peer_async(estab_peer.get('peer_id'), estab_peer.get('ticket_id'))
            else:
                if estab_peer is not None and sender.connectedId == estab_peer.get('peer_id'):
                    sender.update_status(False)
                    await self.send_estab_peer(sender.connectedId)
                else:
                    await self.get_rtc_data().disconnect_to_peer_async(sender.connectedId)
        elif MessageType.RESPONSE_HELLO_PEER == message.message_type:
            if not sender.is_primary:
                if sender.connectedId == self._hello_peer_id:
                    self._hello_peer_success = True
            await self.received_response_hello_peer(sender.connectedId)

        # ESTAB_PEER
        elif MessageType.REQUEST_ESTAB_PEER == message.message_type:
            is_established = await self.received_estab_peer(sender.connectedId, message.header)
            if not is_established:
                await self.get_rtc_data().disconnect_to_peer_async(sender.connectedId)
            elif PEER_CONFIG['PROBE_PEER_TIMEOUT'] < 1:
                await self.send_set_primary_is_skip_probe(sender.connectedId)

        elif MessageType.RESPONSE_ESTAB_PEER == message.message_type:
            await self.received_response_estab_peer(sender.connectedId, True)
        elif MessageType.RESPONSE_ESTAB_PEER_ERROR == message.message_type:
            await self.received_response_estab_peer(sender.connectedId, False)

        # PROBE_PEER
        elif MessageType.REQUEST_PROBE_PEER == message.message_type:
            await self.received_probe_peer(sender.connectedId, message.header)
        elif MessageType.RESPONSE_PROBE_PEER == message.message_type:
            self.received_response_probe_peer(sender.connectedId, message.header)

        # SET_PRIMARY
        elif MessageType.REQUEST_SET_PRIMARY == message.message_type:
            await self.received_set_primary(sender.connectedId, sender.is_outgoing)
        elif MessageType.RESPONSE_SET_PRIMARY == message.message_type:
            await self.received_response_set_primary(sender.connectedId, sender.is_outgoing, True)
        elif MessageType.RESPONSE_SET_PRIMARY_ERROR == message.message_type:
            await self.received_response_set_primary(sender.connectedId, sender.is_outgoing, False)

        # SET_CANDIDATE
        elif MessageType.REQUEST_SET_CANDIDATE == message.message_type:
            await self.received_set_candidate(sender.connectedId)
        elif MessageType.RESPONSE_SET_CANDIDATE == message.message_type:
            self.received_response_set_candidate(sender.connectedId)

        # BROADCAST_DATA
        elif MessageType.REQUEST_BROADCAST_DATA == message.message_type:
            await self.received_broadcast_data(sender.connectedId, message)
        elif MessageType.RESPONSE_BROADCAST_DATA == message.message_type:
            self.received_response_broadcast_data(sender.connectedId)

        # RELEASE_PEER
        elif MessageType.REQUEST_RELEASE_PEER == message.message_type:
            await self.received_release_peer(sender.connectedId, message.header)
        elif MessageType.RESPONSE_RELEASE_PEER == message.message_type:
            await self.received_response_release_peer(sender.connectedId)

        # HEARTBEAT
        elif MessageType.REQUEST_HEARTBEAT == message.message_type:
            await self.received_heartbeat(sender.connectedId)
        elif MessageType.RESPONSE_HEARTBEAT == message.message_type:
            self.received_response_heartbeat(sender.connectedId)

        # SCAN_TREE
        elif MessageType.REQUEST_SCAN_TREE == message.message_type:
            await self.received_scan_tree(sender.connectedId, message.header)

        elif MessageType.RESPONSE_SCAN_TREE_NON_LEAF == message.message_type:
            self.received_response_scan_tree_non_leaf(sender.connectedId)

        elif MessageType.RESPONSE_SCAN_TREE_LEAF == message.message_type:
            await self.received_response_scan_tree_leaf(sender.connectedId, message.header)

        else:
            print('error')

    # Receive Message handle  #######################################################
    ################################################################################
    async def received_hello_peer(self, target_peer_id, message):
        result = False
        print('\n++++++++[HOPP] RECEIVED REQUEST_HELLO_PEER / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED HELLO_PEER / ID:' + target_peer_id)

        request_peer = message.get('ReqParams').get('peer')
        request_peer_id = request_peer.get('peer_id')
        request_ticket_id = request_peer.get('ticket_id')
        # target_address = target_peer.get('address')
        if target_peer_id != request_peer_id:
            print('\n################################################################################')
            print('\n++++++++[HOPP] RECEIVED REQUEST_HELLO_PEER(RELAY MESSAGE)', request_peer_id)

        response_hello_peer_message = {
            'RspCode': MessageType.RESPONSE_HELLO_PEER
        }
        print('\n++++++++[HOPP] SEND HELLO_PEER RESPONSE / ID:', target_peer_id)
        request_message = self.convert_message_to_bytes(response_hello_peer_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

        operation = message.get('ReqParams').get('operation')
        conn_num = operation.get('conn_num')
        ttl = operation.get('ttl')
        recovery = operation.get('recovery') if 'recovery' in operation else False

        if conn_num < 1 or ttl < 1:
            return None

        children_count = self.get_peer_manager().get_children_count()
        is_assignment = self.get_peer_manager().assignment_peer(request_peer_id)

        if not recovery:
            if children_count > 0:
                operation['ttl'] = ttl - 1
                new_conn_num = conn_num - (1 if is_assignment else 0)

                if new_conn_num > 0:
                    operation['conn_num'] = math.ceil(new_conn_num / children_count)

                    print('\n++++++++[HOPP] HELLO_PEER REQUEST(BROADCAST) / REQUEST ID:', request_peer_id)
                    self.send_gui_web_socket('BROADCAST HELLO_PEER / REQUEST ID:' + request_peer_id)
                    broadcast_request_message = self.convert_message_to_bytes(message)
                    await self.get_rtc_data().send_broadcast_message_to_children_async(broadcast_request_message)

            if is_assignment:
                result = True
        else:
            if request_ticket_id <= self.peer.ticket_id:
                print('\n++++++++[HOPP] RECOVERY ==>  ticket_id.... bigger than me / ID:', request_peer_id)
                return None

            print('\n++++++++[HOPP] RECOVERY == HELLO_PEER / ID:', request_peer_id)
            self.send_gui_web_socket('RECOVERY HELLO_PEER / ID:' + request_peer_id)
            is_assignment_recovery = True

            if not is_assignment:
                is_assignment_recovery = False
                remove_peer_id = self.reassignment_connections_for_recovery(request_peer_id, request_ticket_id)
                if remove_peer_id is not None:
                    is_assignment_recovery = True
                    await self.send_release_peer(remove_peer_id, False)
                    await self.get_rtc_data().disconnect_to_peer_async(remove_peer_id)

            if children_count > 0:
                operation['ttl'] = ttl - 1
                new_conn_num = conn_num - (1 if is_assignment_recovery else 0)

                if new_conn_num > 0:
                    operation['conn_num'] = math.ceil(new_conn_num / children_count)

                    print('\n++++++++[HOPP] RECOVERY ==  HELLO_PEER REQUEST(BROADCAST) / REQUEST ID:', request_peer_id)
                    self.send_gui_web_socket('BROADCAST HELLO_PEER(RECOVERY) / REQUEST ID:' + request_peer_id)
                    broadcast_request_message = self.convert_message_to_bytes(message)
                    await self.get_rtc_data().send_broadcast_message_to_children_async(broadcast_request_message)

            if is_assignment_recovery:
                result = True

        return request_peer if result else None

    async def received_response_hello_peer(self, target_peer_id):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_HELLO_PEER / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED RESPONSE_HELLO_PEER / ID:' + target_peer_id)
        await self.run_estab_peer_timer()

    async def received_estab_peer(self, target_peer_id, message):
        print('\n++++++++[HOPP] RECEIVED ESTAB_PEER REQUEST / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED ESTAB_PEER / ID:' + target_peer_id)

        received_message = message.get('ReqParams')
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
                if target_peer_id == self._hello_peer_id:
                    get_peer = self.get_peer_manager().get_peer_connection(target_peer_id)
                    get_peer.update_status(True, target_ticket_id)

        print('\n++++++++[HOPP] SEND ESTAB_PEER RESPONSE / ID:', target_peer_id)
        self.send_gui_web_socket('SEND ESTAB_PEER RESPONSE / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(estab_response_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

        if is_established:
            self.send_report()
        else:
            await self.send_to_all_probe_peer()

        return is_established

    async def received_response_estab_peer(self, target_peer_id, is_success):
        is_success_str = "" if is_success else "(ERROR)"
        print('\n++++++++[HOPP] RECEIVED RESPONSE_ESTAB_PEER{0}/ ID:{1}'.format(is_success_str, target_peer_id))
        self.send_gui_web_socket('RECEIVED RESPONSE_ESTAB_PEER{0} / ID:{1}'.format(is_success_str, target_peer_id))

        if not is_success:
            self.get_peer_manager().un_assignment_peer(target_peer_id)
            await self.get_rtc_data().disconnect_to_peer_async(target_peer_id)

    async def received_probe_peer(self, target_peer_id, message):
        print('\n++++++++[HOPP] RECEIVED PROBE_PEER / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED PROBE_PEER / ID:' + target_peer_id)

        probe_response_message = {
            'RspCode': MessageType.RESPONSE_PROBE_PEER,
            'RspParams': {
                'operation': {
                    'ntp_time': message.get('ReqParams').get('operation').get('ntp_time')
                }
            }
        }
        print('\n++++++++[HOPP] SEND PROBE_PEE RESPONSE / ID:', target_peer_id)
        self.send_gui_web_socket('SEND PROBE_PEER RESPONSE / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(probe_response_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

    def received_response_probe_peer(self, target_peer_id, message):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_PROBE_PEER / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED PROBE_PEER RESPONSE / ID:' + target_peer_id)

        send_time = datetime.strptime(message.get('RspParams').get('operation').get('ntp_time'), self.fmt)
        now_time = datetime.strptime(str(datetime.now()), self.fmt)
        delta_time = now_time - send_time
        probe_time = delta_time.seconds * 1000000 + delta_time.microseconds
        self.get_peer_manager().set_estab_peers_probe_time(target_peer_id, probe_time)

    async def received_set_primary(self, target_peer_id, is_outgoing):
        print('\n++++++++[HOPP] RECEIVED SET_PRIMARY / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED SET_PRIMARY / ID:' + target_peer_id)

        result_set_primary = self.get_peer_manager().set_primary_peer(target_peer_id, is_outgoing)
        primary_response_message = {
            'RspCode': MessageType.RESPONSE_SET_PRIMARY_ERROR
        }

        if result_set_primary:
            primary_response_message['RspCode'] = MessageType.RESPONSE_SET_PRIMARY
            if self.peer.using_web_gui:
                Factory.instance().get_web_socket_handler().send_connection_change(True)

        print('\n++++++++[HOPP] SEND SET_PRIMARY RESPONSE / ID:', target_peer_id)
        self.send_gui_web_socket('SEND SET_PRIMARY RESPONSE / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(primary_response_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

        if result_set_primary:
            self.send_report()

    async def received_response_set_primary(self, target_peer_id, is_outgoing, is_success):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED SET_PRIMARY RESPONSE / ID:' + target_peer_id)

        if is_success:
            self.success_set_primary(target_peer_id, is_outgoing)

            if self.get_peer_manager().is_run_primary_peer:
                self.get_peer_manager().is_run_primary_peer = False
                if PEER_CONFIG['SEND_CANDIDATE']:
                    await self.send_to_all_set_candidate()
                else:
                    self.get_peer_manager().clear_estab_peers()
            elif not self.get_peer_manager().is_first_peer_set_primary:
                self.get_peer_manager().clear_failed_primary_list()
        else:
            if self.get_peer_manager().is_run_primary_peer:
                await self.check_and_send_set_primary()
            elif not self.get_peer_manager().is_first_peer_set_primary:
                self.get_peer_manager().append_failed_primary_list(target_peer_id)
                print('\n++++++++[HOPP] received_response_set_primary ==> recovery_connection (ASYNC)*********')
                await self.recovery_connection()
        # if self.get_peer_manager().is_run_primary_peer:
        #     print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY ', target_peer_id)
        #     self.send_gui_web_socket('RECEIVED SET_PRIMARY RESPONSE(RUN_PRIMARY_PEER).')
        #
        #     if is_success:
        #         self.success_set_primary(target_peer_id, is_outgoing)
        #         self.get_peer_manager().is_run_primary_peer = False
        #
        #         if PEER_CONFIG['SEND_CANDIDATE']:
        #             await self.send_to_all_set_candidate()
        #         else:
        #             self.get_peer_manager().clear_estab_peers()
        #     else:
        #         await self.check_and_send_set_primary()
        #
        # elif self.get_peer_manager().is_first_peer_set_primary:
        #     print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY (FIRST_PEER_SET_PRIMARY)', target_peer_id)
        #     self.send_gui_web_socket('RECEIVED SET_PRIMARY RESPONSE(FIRST_PEER_SET_PRIMARY)')
        #
        #     if is_success:
        #         self.success_set_primary(target_peer_id, is_outgoing)
        # else:
        #     print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_PRIMARY(RECOVERY)', target_peer_id)
        #     self.send_gui_web_socket('RECEIVED SET_PRIMARY RESPONSE(RECOVERY).')
        #
        #     if is_success:
        #         self.get_peer_manager().clear_failed_primary_list()
        #         self.success_set_primary(target_peer_id, is_outgoing)
        #     else:
        #         self.get_peer_manager().append_failed_primary_list(target_peer_id)
        #         await self.recovery_connection()

    async def received_set_candidate(self, target_peer_id):
        print('\n++++++++[HOPP] RECEIVED SET_CANDIDATE / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED SET_CANDIDATE / ID:' + target_peer_id)
        candidate_response_message = {
            'RspCode': MessageType.RESPONSE_SET_CANDIDATE
        }

        print('\n++++++++[HOPP] SEND SET_CANDIDATE RESPONSE / ID:', target_peer_id)
        self.send_gui_web_socket('SEND SET_CANDIDATE RESPONSE / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(candidate_response_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)
        self.send_report()

    def received_response_set_candidate(self, target_peer_id):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_SET_CANDIDATE / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED SET_CANDIDATE RESPONSE / ID:' + target_peer_id)

    async def received_broadcast_data(self, target_peer_id, message):
        print('\n++++++++[HOPP] RECEIVED BROADCAST_DATA / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED BROADCAST_DATA / ID:' + target_peer_id)
        Factory.instance().sendto_udp_socket(message.content)

        request_params = message.header.get('ReqParams')
        source_peer = request_params.get('peer').get('peer_id')

        print_message = '\n++++++++[HOPP] SENDER:{0} / SOURCE:{1} / DATA=>{2}'
        print(print_message.format(target_peer_id, source_peer, message.content))

        if self.peer.using_web_gui:
            Factory.instance().get_web_socket_handler().send_received_data(target_peer_id, source_peer, message.content)

        if request_params.get('ack'):
            broadcast_data_response_message = {
                'RspCode': MessageType.RESPONSE_BROADCAST_DATA
            }
            print('\n++++++++[HOPP] SEND BROADCAST_DATA RESPONSE / ID:', target_peer_id)
            self.send_gui_web_socket('SEND BROADCAST_DATA RESPONSE / ID:' + target_peer_id)
            request_message = self.convert_message_to_bytes(broadcast_data_response_message)
            await self.get_rtc_data().send_async(target_peer_id, request_message)

        if source_peer != self.peer.peer_id:
            await self.relay_broadcast_data(target_peer_id, message)

    def received_response_broadcast_data(self, target_peer_id):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_BROADCAST_DATA / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED BROADCAST_DATA RESPONSE / ID:' + target_peer_id)

    async def received_release_peer(self, target_peer_id, message):
        print('\n++++++++[HOPP] RECEIVED RELEASE_PEER / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED RELEASE_PEER / ID:' + target_peer_id)

        if message.get('ReqParams').get('operation').get('ack'):
            release_response_message = {
                'RspCode': MessageType.RESPONSE_RELEASE_PEER
            }
            print('\n++++++++[HOPP] SEND RELEASE_PEER RESPONSE / ID:', target_peer_id)
            self.send_gui_web_socket('SEND RELEASE_PEER RESPONSE / ID:' + target_peer_id)
            request_message = self.convert_message_to_bytes(release_response_message)
            await self.get_rtc_data().send_async(target_peer_id, request_message)
        else:
            await self.get_rtc_data().disconnect_to_peer_async(target_peer_id)

    async def received_response_release_peer(self, target_peer_id):
        print('\n++++++++[HOPP] RECEIVED RESPONSE_RELEASE_PEER / ID:', target_peer_id)
        self.send_gui_web_socket('RECEIVED RELEASE_PEER RESPONSE / ID:' + target_peer_id)
        await self.get_rtc_data().disconnect_to_peer_async(target_peer_id)

    async def received_heartbeat(self, target_peer_id):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n++++++++[HOPP] RECEIVED HEARTBEA / ID:', target_peer_id)
            self.send_gui_web_socket('RECEIVED HEARTBEAT / ID:' + target_peer_id)

        peer_connection = self.get_peer_manager().get_peer_connection(target_peer_id)
        if peer_connection is not None and peer_connection.isDataChannelOpened:
            peer_connection.update_time = datetime.now()

            release_response_message = {
                'RspCode': MessageType.RESPONSE_HEARTBEAT
            }
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n++++++++[HOPP] SEND HEARTBEAT RESPONSE / ID:', target_peer_id)
                self.send_gui_web_socket('SEND HEARTBEAT RESPONSE / ID:' + target_peer_id)

            request_message = self.convert_message_to_bytes(release_response_message)
            await self.get_rtc_data().send_async(target_peer_id, request_message)

    def received_response_heartbeat(self, target_peer_id):
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n++++++++[HOPP] RECEIVED RESPONSE_HEARTBEAT / ID:', target_peer_id)
            self.send_gui_web_socket('RECEIVED HEARTBEAT RESPONSE / ID:' + target_peer_id)

        peer_connection = self.get_peer_manager().get_peer_connection(target_peer_id)
        if peer_connection is not None and peer_connection.isDataChannelOpened:
            peer_connection.update_time = datetime.now()

    async def received_scan_tree(self, target_peer_id, message):
        if PEER_CONFIG['PRINT_SCAN_TREE_LOG']:
            print('\n++++++++[HOPP] RECEIVED SCAN_TREE / ID:', target_peer_id)
            self.send_gui_web_socket('RECEIVED SCAN_TREE / ID:' + target_peer_id)

        params_overlay = message.get('ReqParams').get('overlay')
        params_peer = message.get('ReqParams').get('peer')
        cseq = message.get('ReqParams').get('cseq')
        via_list = params_overlay.get('via')
        # target_peer_id, target_peer_address = via_list[0]
        path_list = params_overlay.get('path')
        path_list.insert(0, [self.peer.peer_id, self.peer.ticket_id, self.peer.get_address()])

        is_leaf = self.get_peer_manager().is_leaf(target_peer_id)
        scan_tree_response_message = {
            'RspCode': MessageType.RESPONSE_SCAN_TREE_LEAF if is_leaf else MessageType.RESPONSE_SCAN_TREE_NON_LEAF,
            'RspParams': {
                'cseq': cseq,
                'overlay': {
                    'overlay_id': params_overlay.get('overlay_id'),
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
            print('\n++++++++[HOPP] SEND SCAN_TREE RESPONSE / ID:', target_peer_id)
            self.send_gui_web_socket('SEND SCAN_TREE RESPONSE / ID:' + target_peer_id)

        request_message = self.convert_message_to_bytes(scan_tree_response_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

        if not is_leaf:
            via_list.insert(0, [self.peer.peer_id, self.peer.get_address()])
            scan_tree_message = {
                'ReqCode': MessageType.REQUEST_SCAN_TREE,
                'ReqParams': {
                    'cseq': cseq,
                    'overlay': {
                        'overlay_id': params_overlay.get('overlay_id'),
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
                print('\n++++++++[HOPP] SEND SCAN_TREE(RELAY) / ID:', target_peer_id)
                self.send_gui_web_socket('SEND SCAN_TREE(RELAY) / ID:' + target_peer_id)

            relay_request_message = self.convert_message_to_bytes(scan_tree_message)
            await self.get_rtc_data().send_broadcast_message_other_async(target_peer_id, relay_request_message)

    def received_response_scan_tree_non_leaf(self, target_peer_id):
        if PEER_CONFIG['PRINT_SCAN_TREE_LOG']:
            print('\n++++++++[HOPP] RECEIVED RESPONSE_SCAN_TREE_NON_LEAF / ID:', target_peer_id)
            self.send_gui_web_socket('RECEIVED SCAN TREE(NON_LEAF) RESPONSE / ID:' + target_peer_id)

    async def received_response_scan_tree_leaf(self, target_peer_id, message):
        if PEER_CONFIG['PRINT_SCAN_TREE_LOG']:
            print('\n++++++++[HOPP] RECEIVED RESPONSE_SCAN_TREE_NON_LEAF / ID:', target_peer_id)
            self.send_gui_web_socket('RECEIVED SCAN TREE(NON_LEAF) RESPONSE / ID:' + target_peer_id)

        params_overlay = message.get('RspParams').get('overlay')
        params_peer = message.get('RspParams').get('peer')
        cseq = message.get('RspParams').get('cseq')
        via_list = params_overlay.get('via')
        target_peer_id, target_peer_address = via_list[0]

        if self.peer.peer_id == target_peer_id:
            via_list.remove([target_peer_id, target_peer_address])
            if len(via_list) > 0:
                target_peer_id, target_peer_address = via_list[0]
                scan_tree_response_message = {
                    'RspCode': MessageType.RESPONSE_SCAN_TREE_LEAF,
                    'RspParams': {
                        'cseq': cseq,
                        'overlay': {
                            'overlay_id': params_overlay.get('overlay_id'),
                            'via': via_list,
                            'path': params_overlay.get('path')
                        },
                        'peer': {
                            'peer_id': params_peer.get('peer_id'),
                            'address': params_peer.get('address'),
                            'ticket_id': params_peer.get('ticket_id')
                        }
                    }
                }

                if PEER_CONFIG['PRINT_SCAN_TREE_LOG']:
                    print('\n++++++++[HOPP] SEND SCAN_TREE RESPONSE / ID:', target_peer_id)
                    self.send_gui_web_socket('SEND SCAN_TREE RESPONSE / ID:' + target_peer_id)

                request_message = self.convert_message_to_bytes(scan_tree_response_message)
                await self.get_rtc_data().send_async(target_peer_id, request_message)
            else:
                if self.peer.peer_id == params_peer.get('peer_id') and self.peer.scan_tree_sequence == cseq:
                    if self.peer.using_web_gui:
                        Factory.instance().get_web_socket_handler().send_scan_tree_path(params_overlay.get('path'))

    # Send Message handle  #######################################################
    ################################################################################
    async def send_hello_peer(self, target_peer_id):
        hello_message = {
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
        print('\n++++++++[HOPP] SEND REQUEST_HELLO_PEER / ID:', target_peer_id)
        self.send_gui_web_socket('SEND HELLO_PEER / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(hello_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

    async def send_recovery_hello_peer(self, target_peer_id):
        recovery_hello_message = {
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
        print('\n++++++++[HOPP] SEND REQUEST_HELLO_PEER (RECOVERY) / ID:', target_peer_id)
        self.send_gui_web_socket('SEND HELLO_PEER (RECOVERY) / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(recovery_hello_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

    async def send_estab_peer(self, target_peer_id):
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
        print('\n++++++++[HOPP] SEND ESTABLISH REQUEST / ID:', target_peer_id)
        self.send_gui_web_socket('SEND ESTABLISH_PEER / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(establish_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

    async def send_to_all_probe_peer(self):
        if not self.get_peer_manager().is_run_probe_peer:
            print('\n++++++++[HOPP] SEND TO ALL PROBE_PEER')
            self.get_peer_manager().is_run_probe_peer = True
            estab_peers = self.get_peer_manager().get_estab_peers()

            if len(estab_peers) > 0:
                if PEER_CONFIG['PROBE_PEER_TIMEOUT'] > 0:
                    for peer_id in estab_peers.keys():
                        await self.send_probe_peer(peer_id)
                    await self.run_probe_peer_timer()
                else:
                    await self.check_and_send_set_primary()
            else:
                self.send_gui_web_socket('ESTAB_PEER is None.')

    async def send_probe_peer(self, target_peer_id):
        probe_message = {
            'ReqCode': MessageType.REQUEST_PROBE_PEER,
            'ReqParams': {
                'operation': {
                    'ntp_time': str(datetime.now())
                }
            }
        }
        print('\n++++++++[HOPP] SEND PROBE_PEER REQUEST / ID:', target_peer_id)
        request_message = self.convert_message_to_bytes(probe_message)
        self.send_gui_web_socket('SEND PROBE_PEER / ID:' + target_peer_id)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

    async def send_set_primary(self, target_peer_id):
        primary_message = {
            'ReqCode': MessageType.REQUEST_SET_PRIMARY
        }
        print('\n++++++++[HOPP] SEND SET_PRIMARY REQUEST / ID:', target_peer_id)
        self.send_gui_web_socket('SEND SET_PRIMARY / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(primary_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

    async def send_set_primary_is_skip_probe(self, target_peer_id):
        if not self.get_peer_manager().is_first_peer_set_primary:
            self.get_peer_manager().is_first_peer_set_primary = True

            primary_message = {
                'ReqCode': MessageType.REQUEST_SET_PRIMARY
            }
            print('\n++++++++[HOPP] SEND SET_PRIMARY REQUEST(SKIP_PROBE) / ID:', target_peer_id)
            self.send_gui_web_socket('SEND SET_PRIMARY(SKIP_PROBE) / ID:' + target_peer_id)
            request_message = self.convert_message_to_bytes(primary_message)
            await self.get_rtc_data().send_async(target_peer_id, request_message)

    async def send_to_all_set_candidate(self):
        print('\n++++++++[HOPP] SEND TO ALL SET CANDIDATE')
        estab_peers = self.get_peer_manager().get_estab_peers()
        if len(estab_peers) > 0:
            for peer_id in estab_peers.keys():
                connection = self.get_peer_manager().get_peer_connection(peer_id)
                if connection is not None:
                    await self.send_set_candidate(peer_id)

        self.get_peer_manager().clear_estab_peers()

    async def send_set_candidate(self, target_peer_id):
        candidate_message = {
            'ReqCode': MessageType.REQUEST_SET_CANDIDATE
        }
        print('\n++++++++[HOPP] SEND SET_CANDIDATE REQUEST / ID:', target_peer_id)
        self.send_gui_web_socket('SEND SET_CANDIDATE / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(candidate_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

    def send_broadcast_data(self, send_data, is_ack=None):
        Factory.instance().sendto_udp_socket(send_data)

        if self.get_peer_manager().has_primary():
            operation_ack = is_ack if is_ack is not None else PEER_CONFIG['BROADCAST_OPERATION_ACK']
            bytes_data, data_length = self.convert_data_to_bytes(send_data)

            broadcast_message = {
                'ReqCode': MessageType.REQUEST_BROADCAST_DATA,
                'ReqParams': {
                    'operation': {
                        'ack': operation_ack
                    },
                    'peer': {
                        'peer_id': self.peer.peer_id
                    },
                    'payload': {
                        'length': data_length,
                        'type': 'text/plain'
                    }
                }
            }
            print('\n++++++++[HOPP] SEND BROADCAST_DATA REQUEST')
            self.send_gui_web_socket('SEND BROADCAST_DATA.')
            request_message = self.convert_message_to_bytes(broadcast_message, bytes_data)
            self.get_rtc_data().send_broadcast_message(request_message)

    async def send_release_peer(self, target_peer_id, is_ack=None):
        operation_ack = is_ack if is_ack is not None else PEER_CONFIG['RELEASE_OPERATION_ACK']
        release_message = {
            'ReqCode': MessageType.REQUEST_RELEASE_PEER,
            'ReqParams': {
                'operation': {
                    'ack': operation_ack
                }
            }
        }
        print('\n++++++++[HOPP] SEND RELEASE PEER REQUEST / ID:', target_peer_id)
        self.send_gui_web_socket('SEND RELEASE_PEER / ID:' + target_peer_id)
        request_message = self.convert_message_to_bytes(release_message)
        await self.get_rtc_data().send_async(target_peer_id, request_message)

        if not operation_ack:
            await self.get_rtc_data().disconnect_to_peer_async(target_peer_id)

    def send_to_all_release_peer(self):
        if self.get_peer_manager().is_destroy:
            return

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
            print('\n++++++++[HOPP] SEND TO ALL RELEASE_PEER REQUEST')
            request_message = self.convert_message_to_bytes(release_message)

            for peer_id in peers.keys():
                self.get_rtc_data().send(peer_id, request_message)
                if not operation_ack:
                    self.get_rtc_data().disconnect_to_peer(peer_id)

    def send_heartbeat(self, target_peer_id):
        peer_connection = self.get_peer_manager().get_peer_connection(target_peer_id)
        if peer_connection is not None and peer_connection.isDataChannelOpened:
            if (peer_connection.is_primary and self.peer.ticket_id > peer_connection.ticket_id) or \
                    peer_connection.connectedId in self.get_peer_manager().get_out_going_candidate_list():
                heartbeat_message = {
                    'ReqCode': MessageType.REQUEST_HEARTBEAT
                }
                if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                    print('\n++++++++[HOPP] SEND HEARTBEAT REQUEST / ID:', peer_connection.connectedId)
                    self.send_gui_web_socket('SEND HEARTBEAT / ID:' + peer_connection.connectedId)

                request_message = self.convert_message_to_bytes(heartbeat_message)
                self.get_rtc_data().send(target_peer_id, request_message)
        else:
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n++++++++[HOPP] HEARTBEAT -- NOT EXIST PEER', target_peer_id)

    def send_to_all_heartbeat(self):
        peers = self.get_peer_manager().get_all_peer_connection()
        if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
            print('\n----------[Heartbeat] SEND TO ALL Heartbeat')

        if self.get_peer_manager().is_send_heartbeat:
            if len(peers) > 0:
                for peer_id in peers.keys():
                    self.send_heartbeat(peer_id)
        else:
            if PEER_CONFIG['PRINT_HEARTBEAT_LOG']:
                print('\n----------[Heartbeat] NOT WORK send_heartbeat')

    def send_scan_tree(self):
        self.set_tree_sequence()
        scan_tree_message = {
            'ReqCode': MessageType.REQUEST_SCAN_TREE,
            'ReqParams': {
                'cseq': self.peer.scan_tree_sequence,
                'overlay': {
                    'overlay_id': self.peer.overlay_id,
                    'via': [[self.peer.peer_id, self.peer.get_address()]],
                    'path': []
                },
                'peer': {
                    'peer_id': self.peer.peer_id,
                    'address': self.peer.get_address(),
                    'ticket_id': self.peer.ticket_id
                }
            }
        }
        print('\n++++++++[HOPP] SEND SCAN_TREE REQUEST')
        self.send_gui_web_socket('SEND SCAN_TREE.')
        request_message = self.convert_message_to_bytes(scan_tree_message)
        self.get_rtc_data().send_broadcast_message(request_message)

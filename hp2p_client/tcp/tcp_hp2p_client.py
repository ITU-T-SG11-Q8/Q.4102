import threading

from data.factory import Factory, Peer
from config import PEER_CONFIG, CLIENT_CONFIG
from homp.homp_message_handler import HompMessageHandler
from tcp.tcp_peer_connection_manager import TcpPeerConnectionManager
from tcp.tcp_message_server import TcpMessageHandler, TcpThreadingSocketServer
from data.client_scheduler import ClientScheduler


class TcpHp2pClient:
    def __init__(self):
        self.peer: Peer = Factory.instance().get_peer()
        self.handler: HompMessageHandler = Factory.instance().get_homp_handler()
        self.peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
        self._s_flag = False
        self.retry_count = 0
        self.is_process_client = False

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

    def run_auto_client(self):
        print('Run Client')
        self.auto_creation_and_join()
        # self.simple_process_client()
        # self.process_client()

    def auto_creation_and_join(self):
        print('Creation or Join')
        if self.peer.isOwner:
            self.handler.creation(self.peer)
            self.handler.join(self.peer)
            self.handler.report(self.peer, Factory.instance().get_peer_manager())
            # self.handler.modification(self.peer)

            self.run_expires_scheduler(self.peer.peer_expires)
            TcpMessageHandler.run_heartbeat_scheduler()
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
                self.run_expires_scheduler(self.peer.peer_expires)
                TcpMessageHandler.run_heartbeat_scheduler()

                if len(join_response) > 0:
                    is_process = False
                    for peer_info in join_response:
                        target_peer_id = peer_info.get('peer_id')
                        target_address = peer_info.get('address')

                        if self.peer.peer_id == target_peer_id:
                            self.peer.is_top_peer = True
                            print("Top Peer...", flush=True)
                            is_process = True
                            break
                        else:
                            print("Join...", target_peer_id, target_address, flush=True)
                            hello_result = TcpMessageHandler.send_hello_peer(self.peer, target_address)
                            if hello_result:
                                TcpMessageHandler.run_estab_peer_timer()
                                is_process = True
                                break

                    if is_process:
                        self.simple_process_client()
                    else:
                        self.retry_join(True, "Failed Join.")
                else:
                    self.retry_join(True, "Server Error")
                    # self.handler.report(self.peer, self.peer_manager)

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
                        print('Web UI URL => localhost:{0}'.format(self.peer.gui_server_port))
                    if self.peer.public_data_port is not None:
                        print('Public Data Listening Server => localhost:{0}'.format(self.peer.public_data_port))
                    print('PRIMARY_LIST', self.peer_manager.get_primary_list())
                    print('IN_CANDIDATE_LIST', self.peer_manager.get_in_coming_candidate_list())
                    print('OUT_CANDIDATE_LIST', self.peer_manager.get_out_going_candidate_list())
                    print(
                        '*******************************************************************************************\n')
                elif input_method.lower() == '/data' or input_method.lower() == '/d':  # 데이터 전송
                    send_data = input("Message =>")
                    TcpMessageHandler.send_broadcast_data(self.peer, send_data)
                else:
                    print("")
        except Exception as e:
            print(e)
        finally:
            self.client_end()

    def run_tcp_server(self):
        try:
            print('TCP Server Start.\n')
            address = (CLIENT_CONFIG['TCP_SERVER_IP'], 0)
            server = TcpThreadingSocketServer(address, TcpMessageHandler)
            Factory.instance().set_tcp_server(server)
            self.peer.set_tcp_server_info(server.socket.getsockname()[0], server.socket.getsockname()[1])
            server.serve_forever()
        except KeyboardInterrupt:
            print('Error KeyboardInterrupt')
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

    def client_start(self):
        threading.Thread(target=self.run_tcp_server, args=(), daemon=True).start()
        threading.Timer(1, self.run_auto_client).start()

    def client_end(self):
        self.handler.leave(self.peer)
        TcpMessageHandler.send_to_all_release_peer()

        server = Factory.instance().get_tcp_server()
        if server is not None:
            print('\n TCP Server Shutdown')
            server.shutdown()
            server.server_close()

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

# if mode == "auto":
#     threading.Timer(1, self.run_auto_client).start()
# else:
#     self.peer.is_auto = False
#     self.run_client()

# def run_client(self):
#     self.creation_and_join()
#     self.process_client()
#
# def creation_and_join(self):
#     method = input("모드 선택(채널 생성:1, 채널 참가:2, 종료:0) =>")
#     if method.lower() == '0':
#         return
#     elif method.lower() == '1':
#         input_title = input("채널 Title =>")
#         input_description = input("채널 Description =>")
#         input_admin_key = input("채널 Admin Key =>")
#
#         self.peer.title = input_title
#         self.peer.description = input_description
#         self.peer.admin_key = input_admin_key
#
#         self.peer.auth_type = 'open'
#         input_auth_type = input("Auth Type (open:1 , closed:2)=>")
#         if input_auth_type == '2':
#             self.peer.auth_type = 'closed'
#             input_auth_access_key = input("채널 Access Key =>")
#             self.peer.auth_access_key = input_auth_access_key
#
#         self.handler.creation(self.peer)
#         self.handler.join(self.peer)
#         self.handler.report(self.peer, Factory.instance().get_peer_manager())
#         self.handler.modification(self.peer)
#
#         self.run_expires_scheduler(self.peer.peer_expires)
#         TcpMessageHandler.run_heartbeat_scheduler()
#     elif method.lower() == '2':
#         overlay_list = self.handler.query()
#
#         if len(overlay_list) > 0:
#             index = 0
#             for data in overlay_list:
#                 index = index + 1
#                 print("{0} => 타이들: {1}, 생성자: {2}, 채널 타입: {3}".format(index, data.get('title'),
#                                                                      data.get('owner_id'),
#                                                                      data.get('auth').get('type')), flush=True)
#
#             try:
#                 input_overlay_index = input("채널 Index =>")
#                 select_index = int(input_overlay_index)
#                 if select_index < 1 or select_index > len(overlay_list):
#                     print('없는 채널입니다.')
#                     self.creation_and_join()
#                 else:
#                     overlay = overlay_list[select_index - 1]
#                     self.peer.overlay_id = overlay.get('overlay_id')
#                     if overlay.get('auth').get('type') == 'closed':
#                         input_auth_access_key = input("채널 Access Key =>")
#                         self.peer.auth_access_key = input_auth_access_key
#                     join_response = self.handler.join(self.peer)
#
#                     if join_response is None:
#                         print('filed join...')
#                         print('\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
#                         print('++++++++[HOPP] Overlay 네트웨크에 참가 실패.')
#                         print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
#
#                         input_yes_no = input("Peer ID 를 변경하시겠습니까? (Y/N)")
#                         if input_yes_no.lower() == 'y':
#                             input_new_peer_id = input("새로운 Peer ID =>")
#                             self.peer.peer_id = input_new_peer_id
#
#                         self.creation_and_join()
#                     else:
#                         self.run_expires_scheduler(self.peer.peer_expires)
#                         TcpMessageHandler.run_heartbeat_scheduler()
#
#                         if len(join_response) > 0:
#                             is_process = False
#                             for peer_info in join_response:
#                                 target_peer_id = peer_info.get('peer_id')
#                                 target_address = peer_info.get('address')
#
#                                 if self.peer.peer_id == target_peer_id:
#                                     self.peer.is_top_peer = True
#                                     print("Top Peer...", flush=True)
#                                     is_process = True
#                                     break
#                                 else:
#                                     print("Join...", target_peer_id, target_address, flush=True)
#                                     hello_result = TcpMessageHandler.send_hello_peer(self.peer, target_address)
#                                     if hello_result:
#                                         TcpMessageHandler.run_estab_peer_timer()
#                                         is_process = True
#                                         break
#
#                             if not is_process:
#                                 print('\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
#                                 print('++++++++[HOPP] HELLO_PEER List is None... 네트웨크에 참가 실패.')
#                                 print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
#                         else:
#                             self.handler.report(self.peer, self.peer_manager)
#                             print('\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
#                             print('HELLO_PEER List is None... 네트웨크에 참가 실패. 서버 문제 발생...')
#                             print('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
#             except:
#                 print('잘못된 입력입니다.')
#                 self.creation_and_join()
#         else:
#             print('채널이 없습니다.')
#             self.creation_and_join()
#     else:
#         print('잘못된 입력입니다.')
#         self.creation_and_join()
#
# def process_client(self):
#     is_default_input_mode = True
#     try:
#         if self.peer.overlay_id is None:
#             return
#
#         while True:
#             if self.peer.overlay_id is None:
#                 input_method = input("\n작업 선택 (연결상태 확인:1, 종료:0) =>")
#             elif is_default_input_mode:
#                 input_method = input("\n작업 선택 (연결상태 확인:1, 데이터 전송:2, 채널 탈퇴:3, 종료:0) =>")
#             else:
#                 print('\n-----------------------------------------------------')
#                 print(' 종료:0, 연결상태 확인:1, 데이터 전송:2, 채널 탈퇴:3')
#                 print(' 채널 갱신: :4, Peer 갱신: :5, 리포트 전송: :6')
#                 print(' Scan Tree:7, Heartbeat:8, On/Off Heartbeat:81, P2P 연결 해제:9')
#                 print('-----------------------------------------------------')
#                 input_method = input("작업 선택 =>")
#
#             if input_method.lower() == '0':  # 종료
#                 break
#
#             elif input_method.lower() == '1':  # 연결상태 확인
#                 print(
#                     '\n*******************************************************************************************')
#                 print('Peer ID => {0}   &&&   Ticket ID => {1}'.format(self.peer.peer_id, self.peer.ticket_id))
#                 if self.peer.using_web_gui:
#                     print('GUI URL=> localhost:{0}'.format(self.peer.gui_server_port))
#                 print('PRIMARY_LIST', self.peer_manager.get_primary_list())
#                 print('IN_CANDIDATE_LIST', self.peer_manager.get_in_coming_candidate_list())
#                 print('OUT_CANDIDATE_LIST', self.peer_manager.get_out_going_candidate_list())
#                 print(
#                     '*******************************************************************************************\n')
#
#             elif input_method.lower() == '2' and self.peer.overlay_id is not None:  # 데이터 전송
#                 send_data = input("데이터 입력 =>")
#                 TcpMessageHandler.send_broadcast_data(self.peer, send_data)
#
#             elif input_method.lower() == '3' and self.peer.overlay_id is not None:  # 채널 탈퇴
#                 self.handler.leave(self.peer)
#                 TcpMessageHandler.send_to_all_release_peer()
#             # 채널 갱신
#             elif input_method.lower() == '4' and not is_default_input_mode and self.peer.overlay_id is not None:
#                 self.handler.modification(self.peer)
#             # Peer 갱신
#             elif input_method.lower() == '5' and not is_default_input_mode and self.peer.overlay_id is not None:
#                 self.handler.refresh(self.peer)
#             # 리포트 전송
#             elif input_method.lower() == '6' and not is_default_input_mode and self.peer.overlay_id is not None:
#                 self.handler.report(self.peer, self.peer_manager)
#             # Scan Tree
#             elif input_method.lower() == '7' and not is_default_input_mode and self.peer.overlay_id is not None:
#                 print('준비중입니다...')
#             # Heartbeat
#             elif input_method.lower() == '8' and not is_default_input_mode and self.peer.overlay_id is not None:
#                 input_heartbeat_peer = input("대상 ID(모두: /all)=>")
#                 if input_heartbeat_peer == '/all':
#                     TcpMessageHandler.send_to_all_heartbeat()
#                 else:
#                     TcpMessageHandler.send_heartbeat(input_heartbeat_peer)
#             # On/Off Heartbeat
#             elif input_method.lower() == '81' and not is_default_input_mode and self.peer.overlay_id is not None:
#                 self.peer_manager.is_send_heartbeat = not self.peer_manager.is_send_heartbeat
#                 print('Send Heartbeat', 'ON' if self.peer_manager.is_send_heartbeat else 'OFF')
#             # P2P 연결 해제
#             elif input_method.lower() == '9' and not is_default_input_mode and self.peer.overlay_id is not None:
#                 input_release_peer = input("연결 종료 대상 ID(모두 종료: /all)=>")
#                 if input_release_peer == '/all':
#                     TcpMessageHandler.send_to_all_release_peer()
#                 else:
#                     TcpMessageHandler.send_release_peer(input_release_peer)
#
#             elif input_method.lower() == '/c':
#                 is_default_input_mode = not is_default_input_mode
#
#             elif input_method.lower() == '':
#                 print("")
#
#             else:
#                 print("잘못된 입력입니다.")
#     except Exception as e:
#         print(e)
#     finally:
#         self.client_end()

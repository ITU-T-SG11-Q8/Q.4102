import threading

from data.factory import Factory, Peer, HompMessageHandler
from config import CLIENT_CONFIG
from data.tcp_peer_connection_manager import TcpPeerConnectionManager
from tcp.tcp_message_server import TcpMessageHandler, TcpThreadingSocketServer
from rtcdata import RTCData


def run_client_cli(peer: Peer, handler: HompMessageHandler):
    creation_and_join(peer, handler)
    process_client(peer, handler)


def creation_and_join(peer: Peer, handler: HompMessageHandler):
    method = input("모드 선택(채널 생성:1, 채널 참가:2, 종료:0) =>")
    if method.lower() == '0':
        return
    elif method.lower() == '1':
        input_title = input("채널 Title =>")
        input_description = input("채널 Description =>")
        input_admin_key = input("채널 Admin Key =>")

        peer.title = input_title
        peer.description = input_description
        peer.admin_key = input_admin_key

        peer.auth_type = 'open'
        input_auth_type = input("Auth Type (open:1 , closed:2)=>")
        if input_auth_type == '2':
            peer.auth_type = 'closed'
            input_auth_access_key = input("채널 Access Key =>")
            peer.auth_access_key = input_auth_access_key

        handler.creation(peer)
        handler.join(peer)
        handler.report(peer, Factory.instance().get_peer_manager())
        handler.modification(peer)
        # TODO => homp_handler.modification(peer) start timer expires

        TcpMessageHandler.run_heartbeat_scheduler()
    elif method.lower() == '2':
        overlay_list = handler.query()

        if len(overlay_list) > 0:
            index = 0
            for data in overlay_list:
                index = index + 1
                print("{0} => 타이들: {1}, 생성자: {2}, 채널 타입: {3}".format(index, data.get('title'), data.get('owner_id'),
                                                                     data.get('auth').get('type')), flush=True)

            try:
                input_overlay_index = input("채널 Index =>")
                select_index = int(input_overlay_index)
                if select_index < 1 or select_index > len(overlay_list):
                    print('없는 채널입니다.')
                    creation_and_join(peer, handler)
                else:
                    overlay = overlay_list[select_index - 1]
                    peer.overlay_id = overlay.get('overlay_id')
                    if overlay.get('auth').get('type') == 'closed':
                        input_auth_access_key = input("채널 Access Key =>")
                        peer.auth_access_key = input_auth_access_key
                    join_response = handler.join(peer)

                    if join_response is None:
                        print('filed join...')
                        input_yes_no = input("Peer ID 를 변경하시겠습니까? (Y/N)")
                        if input_yes_no.lower() == 'y':
                            input_new_peer_id = input("새로운 Peer ID =>")
                            peer.peer_id = input_new_peer_id

                        creation_and_join(peer, handler)
                    else:
                        TcpMessageHandler.run_heartbeat_scheduler()
                        if len(join_response) > 0:
                            for peer_info in join_response:
                                target_peer_id = peer_info.get('peer_id')
                                target_address = peer_info.get('address')
                                print("Join...", target_peer_id, target_address, flush=True)
                                try:
                                    hello_result = TcpMessageHandler.send_hello_peer(peer, target_address)
                                    if hello_result:
                                        TcpMessageHandler.run_estab_peer_timer()
                                except Exception as e:
                                    print(e)
                                    pass
                        else:
                            peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
                            handler.report(peer, peer_manager)
                            print('Peer List is None')
            except:
                print('잘못된 입력입니다.')
                creation_and_join(peer, handler)
        else:
            print('채널이 없습니다.')
            creation_and_join(peer, handler)
    else:
        print('잘못된 입력입니다.')
        creation_and_join(peer, handler)


def process_client(peer: Peer, handler: HompMessageHandler):
    is_default_input_mode = True

    try:
        while True:
            if peer.overlay_id is None:
                break

            if is_default_input_mode:
                input_method = input("\n작업 선택 (연결상태 확인:1, 데이터 전송:2, 채널 탈퇴:3, 종료:0) =>")
            else:
                print('\n-----------------------------------------------------')
                print(' 종료:0, 연결상태 확인:1, 데이터 전송:2, 채널 탈퇴:3')
                print(' 채널 갱신: :4, Peer 갱신: :5, 리포트 전송: :6')
                print(' Scan Tree:7, Heartbeat:8, On/Off Heartbeat:81, P2P 연결 해제:9')
                print('-----------------------------------------------------')
                input_method = input("작업 선택 =>")

            if input_method.lower() == '0':  # 종료
                break

            elif input_method.lower() == '1':  # 연결상태 확인
                peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
                print('\n*******************************************************************************************')
                print('Peer ID', peer.peer_id)
                print('PEERS', peer_manager.peers.keys())
                print('PRIMARY_LIST', peer_manager.primary_list)
                print('IN_CANDIDATE_LIST', peer_manager.in_candidate_list)
                print('OUT_CANDIDATE_LIST', peer_manager.out_candidate_list)
                print('*******************************************************************************************\n')

            elif input_method.lower() == '2':  # 데이터 전송
                send_data = input("데이터 입력 =>")
                TcpMessageHandler.send_broadcast_data(peer, send_data)

            elif input_method.lower() == '3':  # 채널 탈퇴
                handler.leave(peer)
                handler.removal(peer)
                TcpMessageHandler.send_to_all_release_peer()

            elif input_method.lower() == '4':  # 채널 갱신
                handler.modification(peer)

            elif input_method.lower() == '5':  # Peer 갱신
                handler.refresh(peer)

            elif input_method.lower() == '6':  # 리포트 전송
                peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
                handler.report(peer, peer_manager)

            elif input_method.lower() == '7':  # Scan Tree
                print('준비중입니다...')

            elif input_method.lower() == '8':  # Heartbeat
                input_heartbeat_peer = input("대상 ID(모두: /all)=>")
                if input_heartbeat_peer == '/all':
                    TcpMessageHandler.send_to_all_heartbeat()
                else:
                    TcpMessageHandler.send_heartbeat(input_heartbeat_peer)

            elif input_method.lower() == '81':  # On/Off Heartbeat
                peer_manager: TcpPeerConnectionManager = Factory.instance().get_peer_manager()
                peer_manager.is_send_heartbeat = not peer_manager.is_send_heartbeat
                print('Send Heartbeat', 'ON' if peer_manager.is_send_heartbeat else 'OFF')

            elif input_method.lower() == '9':  # P2P 연결 해제
                input_release_peer = input("연결 종료 대상 ID(모두 종료: /all)=>")
                if input_release_peer == '/all':
                    TcpMessageHandler.send_to_all_release_peer()
                else:
                    TcpMessageHandler.send_release_peer(input_release_peer)

            elif input_method.lower() == '/c':
                is_default_input_mode = not is_default_input_mode
            elif input_method.lower() == '':
                print("")
            else:
                print("잘못된 입력입니다.")
    except Exception as e:
        print(e)
    finally:
        TcpMessageHandler.send_to_all_release_peer()
        handler.leave(peer)
        handler.removal(peer)
        # TODO => homp_handler.modification(peer) stop timer expires

        server = Factory.instance().get_tcp_server()
        if server is not None:
            print('TCP Server Shutdown')
            server.shutdown()
            server.server_close()

        scheduler = Factory.instance().get_heartbeat_scheduler()
        if scheduler is not None:
            scheduler.stop()
            Factory.instance().set_heartbeat_scheduler(None)

        print("__END__")


def main():
    input_peer_id = None
    input_auth_password = None
    input_client_type = None

    while True:
        input_peer_id = input("\nPeer ID =>")
        input_auth_password = input("Peer Auth Password =>")

        if len(input_peer_id) > 0 and len(input_auth_password) > 0:
            break
        else:
            print('잘못된 입력입니다.')

    peer: Peer = Factory.instance().get_peer()
    peer.peer_id = input_peer_id
    peer.auth_password = input_auth_password
    handler: HompMessageHandler = Factory.instance().get_homp_handler()

    if '@' not in peer.peer_id:
        t = threading.Thread(target=run_tcp_server, args=())
        t.daemon = True
        t.start()
        run_client_cli(peer, handler)
    else:
        rtcData = RTCData(input_peer_id, 5)
        rtcData.connect_signal_server('127.0.0.1', 8899)

        toid = input('toid:')

        if toid is not None and len(toid) > 0:
            rtcData.connect_to_peer(toid)

        while True:
            msg = input('msg:')

            if msg == 'bye':
                rtcData.send(msg)
                break

            if len(msg) > 0:
                rtcData.send(msg)

        rtcData.close()

        input('')
    # if input_client_type == 1:
    #
    # elif input_client_type == 2:
    #     print('...')
    #     rtc_connection = RtcConnection(input_peer_id)
    #     rtc_connection.send_hello()
    #     Factory.instance().set_rtc_connection(rtc_connection)
    #     peer.set_web_socket_server_info(CLIENT_CONFIG['WEB_SOCKET_SERVER_IP'], CLIENT_CONFIG['WEB_SOCKET_SERVER_PORT'])


def run_tcp_server():
    server = None
    try:
        print('TCP Server Start.\n')
        address = (CLIENT_CONFIG['TCP_SERVER_IP'], 0)
        server = TcpThreadingSocketServer(address, TcpMessageHandler)
        Factory.instance().set_tcp_server(server)

        peer: Peer = Factory.instance().get_peer()
        peer.set_tcp_server_info(server.socket.getsockname()[0], server.socket.getsockname()[1])

        server.serve_forever()
    except KeyboardInterrupt:
        print('Error KeyboardInterrupt')
        print('\t\tTCP Server Shutdown')
        server.shutdown()
        server.server_close()

        scheduler = Factory.instance().get_heartbeat_scheduler()
        if scheduler is not None:
            scheduler.stop()
            Factory.instance().set_heartbeat_scheduler(None)


if __name__ == '__main__':
    main()

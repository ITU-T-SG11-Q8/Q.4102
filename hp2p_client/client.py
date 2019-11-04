import argparse
import uuid
import atexit
from data.factory import Factory, Peer, HompMessageHandler
from tcp.tcp_hp2p_client import TcpHp2pClient
from tcp.tcp_message_server import TcpMessageHandler
from rtc.rtc_hp2p_client import RtcHp2pClient


@atexit.register
def goodbye():
    TcpMessageHandler.send_to_all_release_peer()
    get_peer: Peer = Factory.instance().get_peer()
    handler: HompMessageHandler = Factory.instance().get_homp_handler()
    handler.leave(get_peer)
    handler.removal(get_peer)

    server = Factory.instance().get_tcp_server()
    if server is not None:
        print('TCP Server Shutdown')
        server.shutdown()
        server.server_close()

    scheduler = Factory.instance().get_heartbeat_scheduler()
    if scheduler is not None:
        scheduler.stop()

    input('goodbye...')


def args_parsing():
    parser = argparse.ArgumentParser(
        prog="HP2P Client",
        description="Hybrid P2P Client"
    )
    key = str(uuid.uuid1())
    keys = key.split('-')

    access_key = "etri"
    auth_password = keys[0]
    peer_id = keys[0]
    # peer_id = keys[0] + keys[1] + "-" + keys[2] + keys[3]
    admin_key = keys[1] + keys[4]

    # Peer 기본 설정
    parser.add_argument("-id", help="Peer ID를 설정한다.", dest="peer_id", type=str, default=peer_id,
                        metavar="Peer ID", required=False)
    parser.add_argument("-password", help="Peer Auth Password 을/를 설정한다.", dest="auth_password", type=str,
                        default=auth_password, metavar="Auto Creation(Optional)", required=False)
    # 채널 설정 유무 설정
    parser.add_argument("-owner", help="채널 생성을 요청한다.", dest="owner", type=bool, default=False,
                        metavar="채널 생성(Optional)", required=False)
    parser.add_argument("-overlay", help="Overlay ID를 설정한다.", dest="overlay_id", type=str, default=None,
                        metavar="채널 참가(Optional)", required=False)
    # 채널 생성 정보 설정
    parser.add_argument("-title", help="채널 타이틀을 설정한다.", dest="title", type=str, default="No Title",
                        metavar="채널 생성(Optional)", required=False)
    parser.add_argument("-desc", help="채널 설명을 설정한다.", dest="description", type=str, default="Description",
                        metavar="채널 생성(Optional)", required=False)
    parser.add_argument("-admin-key", help="채널 Admin Key 을/를 설정한다.", dest="admin_key", type=str,
                        default=admin_key, metavar="Auto Creation(Optional)", required=False)
    parser.add_argument("-auth-type", help="채널 Auth Type 을/를 설정한다.", dest="auth_type", type=str,
                        default="open", choices=['open', 'closed'], required=False)
    parser.add_argument("-access-key", help="채널 Access Key 을/를 설정한다.", dest="access_key", type=str,
                        default=access_key, metavar="Default: etri(Optional)", required=False)
    # 실행 및 연결 방식 설정0
    parser.add_argument("-mode", help="실행 방식를 설정한다.", dest="mode", type=str, default="auto",
                        choices=['auto', 'manual'], required=False)
    # parser.add_argument("-control", help="사용 방식를 설정한다.", dest="control", type=str, default="web",
    #                     choices=['web', 'cli'], required=False)
    parser.add_argument("-connection", help="연결 방식를 설정한다.(*)", dest="connection", type=str,
                        choices=['tcp', 'rtc'], required=True)
    return parser.parse_args()


if __name__ == '__main__':
    arg_results = args_parsing()

    try:
        peer: Peer = Factory.instance().get_peer()
        peer.peer_id = arg_results.peer_id
        peer.auth_password = arg_results.auth_password

        if arg_results.owner:
            peer.isOwner = True
            peer.title = arg_results.title
            peer.description = arg_results.description
            peer.admin_key = arg_results.admin_key
            peer.auth_type = arg_results.auth_type
            if peer.auth_type == 'closed':
                peer.auth_access_key = arg_results.access_key
        else:
            peer.overlay_id = arg_results.overlay_id

        if arg_results.connection == 'rtc':
            print('')
            client = RtcHp2pClient()
            client.start()
        elif arg_results.connection == 'tcp':
            client = TcpHp2pClient()
            client.start(arg_results.mode)

    except ValueError:
        print("Parameter Error")

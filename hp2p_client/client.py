import argparse
import uuid
from data.factory import Factory, Peer


def args_parsing():
    parser = argparse.ArgumentParser(
        prog="HP2P Client",
        description="Hybrid P2P Client"
    )
    key = str(uuid.uuid1())
    keys = key.split('-')

    auth_password = keys[0]
    admin_key = keys[4]
    access_key = keys[1] + keys[2] + keys[3]

    # Peer 기본 설정
    parser.add_argument("-id", help="Peer ID를 설정한다.(*)", dest="peer_id", type=str,
                        metavar="Peer ID", required=True)
    parser.add_argument("-password", help="Peer Auth Password 을/를 설정한다.", dest="auth_password", type=str,
                        default=auth_password, metavar="Auto Creation, Optional", required=False)
    # 채널 설정 유무 설정
    parser.add_argument("-owner", help="채널 생성을 요청한다.", dest="owner", type=bool, default=False,
                        metavar="Optional", required=False)
    parser.add_argument("-overlay", help="Overlay ID를 설정한다.", dest="overlay_id", type=str, default=None,
                        metavar="Optional", required=False)
    # 채널 생성 정보 설정
    parser.add_argument("-title", help="채널 타이틀을 설정한다.", dest="title", type=str, default="No Title",
                        metavar="Optional", required=False)
    parser.add_argument("-desc", help="채널 설명을 설정한다.", dest="description", type=str, default="Description",
                        metavar="Optional", required=False)
    parser.add_argument("-admin-key", help="채널 Admin Key 을/를 설정한다.", dest="admin_key", type=str,
                        default=admin_key, metavar="Auto Creation, Optional", required=False)
    parser.add_argument("-auth-type", help="채널 Auth Type 을/를 설정한다.", dest="auth_type", type=str,
                        default="open", choices=['open', 'closed'], required=False)
    parser.add_argument("-access-key", help="채널 Access Key 을/를 설정한다.", dest="access_key", type=str,
                        default=access_key, metavar="Auto Creation, Optional", required=False)
    # 실행 및 연결 방식 설정
    parser.add_argument("-mode", help="실행 방식를 설정한다.(*)", dest="mode", type=str,
                        choices=['auto', 'web', 'cli'], required=True)
    parser.add_argument("-connection", help="연결 방식를 설정한다.(*)", dest="connection", type=str,
                        choices=['tcp', 'webrtc'], required=True)
    return parser.parse_args()


if __name__ == '__main__':
    arg_results = args_parsing()

    try:
        if not arg_results.owner and arg_results.overlay_id is None:
            raise ValueError

        peer: Peer = Factory.instance().get_peer()

        peer.peer_id = arg_results.peer_id
        peer.auth_password = arg_results.auth_password

        if arg_results.owner:
            peer.title = arg_results.title
            peer.description = arg_results.description
            peer.admin_key = arg_results.admin_key
            peer.auth_type = arg_results.auth_type
            if peer.auth_type == 'closed':
                peer.auth_access_key = arg_results.access_key
        else:
            peer.overlay_id = arg_results.overlay_id

        peer.mode = arg_results.mode
        # peer.set_tcp_server_info or set_web_socket_server_info

        if arg_results.connection == 'webrtc':
            print('')
        elif arg_results.connection == 'tcp':
            print('')

    except ValueError:
        print("Parameter Error")

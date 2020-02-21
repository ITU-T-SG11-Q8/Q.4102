import argparse
import uuid
import atexit
import os.path
import threading
import socket
from flask import Flask, Response

from public_data.public_data_listener import PublicDataListener
from config import GUI_CONFIG, CLIENT_CONFIG
from data.factory import Factory, Peer
from tcp.tcp_hp2p_client import TcpHp2pClient
from rtc.rtc_hp2p_client import RtcHp2pClient
from web_socket.web_socket_server import Hp2pWebSocketServer
from homp.homp_message_handler import HompMessageHandler
from tcp.tcp_peer_connection_manager import TcpPeerConnectionManager
from data.client_scheduler import ClientScheduler

app = Flask(__name__)
app.static_folder = GUI_CONFIG['WEB_ROOT']

root_path = None


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/<path:filename>')
def static_file(filename):
    splitext = os.path.splitext(filename)
    ext = splitext[len(splitext) - 1]
    if ext == ".js":
        path = filename.replace("/", "\\")
        complete_path = os.path.join(root_path, GUI_CONFIG['WEB_ROOT'], path)
        content = get_file(complete_path)
        return Response(content, mimetype="application/javascript")
    else:
        return app.send_static_file(filename)


@app.route('/api/InitData')
def info():
    get_peer: Peer = Factory.instance().get_peer()
    if get_peer.is_tcp:
        has_primary = Factory.instance().get_peer_manager().has_primary()
    else:
        has_primary = Factory.instance().get_rtc_hp2p_client().get_peer_manager().has_primary()

    result = {
        'WEB_SOCKET_PORT': get_peer.gui_web_socket_port,
        'PEER_ID': get_peer.peer_id,
        'TICKET_ID': get_peer.ticket_id,
        'OVERLAY_ID': get_peer.overlay_id,
        'IS_OWNER': get_peer.isOwner,
        'HAS_CONNECTION': has_primary,
        'HAS_UDP_CONNECTION': get_peer.has_udp_connection
    }
    return result


def get_file(filename, is_encoding=False):
    try:
        src = os.path.join(root_path, GUI_CONFIG['WEB_ROOT'], filename)
        if is_encoding:
            return open(src, 'r', encoding='UTF-8').read()
        else:
            return open(src).read()
    except IOError as exc:
        return str(exc)


@atexit.register
def goodbye():
    print('goodbye...')


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
    parser.add_argument("-id", help="Peer ID 를 설정한다.", dest="peer_id", type=str, default=peer_id,
                        required=False)
    parser.add_argument("-password", help="Peer Auth Password 를 설정한다.", dest="auth_password", type=str,
                        default=auth_password, metavar="Auto Creation", required=False)

    # 채널 생성 및 참가 설정
    parser.add_argument("-owner", help="채널 생성을 요청한다.", dest="owner", type=bool, default=False,
                        required=False)
    parser.add_argument("-overlay", help="Overlay ID 를 설정한다.", dest="overlay_id", type=str, default=None,
                        metavar="입력이 없을 경우 최근 생성된 Overlay", required=False)

    # 채널 생성 정보 설정
    parser.add_argument("-title", help="채널 타이틀을 설정한다.", dest="title", type=str, default="No Title",
                        metavar="Default: No Title", required=False)
    parser.add_argument("-desc", help="채널 설명을 설정한다.", dest="description", type=str, default="Description",
                        metavar="Default: Description", required=False)
    parser.add_argument("-admin-key", help="채널 Admin Key 를 설정한다.", dest="admin_key", type=str, default=admin_key,
                        metavar="Auto Creation", required=False)
    parser.add_argument("-auth-type", help="채널 Auth Type 을 설정한다.", dest="auth_type", type=str, default="open",
                        choices=['open', 'closed'], metavar="Default: open", required=False)
    parser.add_argument("-access-key", help="채널 Access Key 를 설정한다.", dest="access_key", type=str,
                        default=access_key, metavar="Default: etri", required=False)

    # 실행 및 연결 방식 설정
    parser.add_argument("-connection", help="연결 방식를 설정한다.(*)", dest="connection", type=str,
                        choices=['tcp', 'rtc'], required=True)

    # GUI 설정
    parser.add_argument("-gui-port", help="WebServer Port 를 설정한다.", dest="gui_port", type=int, default=None,
                        metavar="입력하지 않으면 사용하지 않음, 0 을 입력하면 Port 자동 설정", required=False)

    # 공공데이터 수신 설정
    parser.add_argument("-public-port", help="공공데이터 수신을 위한 Tcp Port 를 설정한다.", dest="public_port", type=int,
                        default=None, metavar="입력하지 않으면 사용하지 않음, 0 을 입력하면 Port 자동 설정", required=False)

    # uPREP PEER 설정
    parser.add_argument("-uprep-addr", help="데이터를 공유할 uPREP Peer 주소를 설정한다.", dest="uprep_address", type=str,
                        default=None, metavar="예) 127.0.0.1:1234", required=False)

    return parser.parse_args()


def get_new_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    sock.listen(1)
    new_port_number = sock.getsockname()[1]
    sock.close()
    return new_port_number


def start_web_server(web_server_port):
    app.run(host=GUI_CONFIG['HOST'], port=web_server_port, debug=False)


if __name__ == '__main__':
    root_path = os.path.abspath(os.path.dirname(__file__))

    try:
        arg_results = args_parsing()

        handler = HompMessageHandler()
        Factory.instance().set_homp_handler(handler)

        peer: Peer = Factory.instance().get_peer()
        peer.peer_id = arg_results.peer_id
        peer.auth_password = arg_results.auth_password

        if arg_results.gui_port is not None:
            peer.using_web_gui = True

            peer.gui_server_port = arg_results.gui_port
            if peer.gui_server_port < 1:
                peer.gui_server_port = get_new_port()

            t = threading.Thread(target=start_web_server, args=(peer.gui_server_port,), daemon=True)
            t.start()

            peer.gui_web_socket_port = get_new_port()
            web_socket_server = Hp2pWebSocketServer(peer.gui_web_socket_port)
            web_socket_server.start()

        if arg_results.uprep_address is not None:
            print("Relay uPREP Peer Address:", arg_results.uprep_address)
            uprep_ip, uprep_port = arg_results.uprep_address.split(":")
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            Factory.instance().set_udp_socket_client(udp_sock, uprep_ip, int(uprep_port))
            peer.has_udp_connection = True

        if arg_results.public_port is not None:
            if arg_results.public_port < 1:
                arg_results.public_port = get_new_port()

            peer.public_data_port = arg_results.public_port
            public_data_listener = PublicDataListener(arg_results.public_port)
            Factory.instance().set_public_data_listener(public_data_listener)
            public_data_listener.start()

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

        client_ip = CLIENT_CONFIG['TCP_SERVER_IP']
        if client_ip == '0.0.0.0' or client_ip == '127.0.0.1' or client_ip == 'localhost':
            CLIENT_CONFIG['TCP_SERVER_IP'] = socket.gethostbyname(socket.getfqdn())

        scheduler = ClientScheduler()
        scheduler.start()
        Factory.instance().set_client_scheduler(scheduler)

        if arg_results.connection == 'tcp':
            client = TcpHp2pClient()
            client.client_start()
        elif arg_results.connection == 'rtc':
            client = RtcHp2pClient()
            client.client_start()

    except ValueError:
        print("Parameter Error")

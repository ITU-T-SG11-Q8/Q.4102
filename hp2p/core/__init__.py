import socketserver
import threading
import json
import math
import socket

from core.factory import Factor
from core.hp2p_core import Hp2pCore
from core.classes import RequestMessageType

lock = threading.Lock()

PEER_MANAGER = None
TCP_SERVER = None
HP2P_CORE = None


def convert_bytes_to_message(conn):
    received_size_buffer = conn.recv(4)
    received_size = int.from_bytes(received_size_buffer, 'little')
    received_buffer = conn.recv(received_size)
    message = str(received_buffer, encoding='utf=8')
    try:
        return json.loads(message)
    except:
        return None


def convert_message_to_bytes(message):
    bytes_data = bytes(json.dumps(message), encoding='utf-8')
    bytes_size = len(bytes_data).to_bytes(4, 'little')
    return bytes_data, bytes_size


# import atexit
# def at_exit_func():
#     print("exited.", flush=True)
#
#
# atexit.register(at_exit_func)

# import argparse
# def args_parsing():
#     parser = argparse.ArgumentParser(
#         prog="Hybrid P2P",
#         description="copyright by ETRI"
#     )
#     parser.add_argument("-pid", help="EcoGrid Project ID *required", dest="projectId", metavar="Project ID", type=int,
#                         required=False, choices=range(0, 65536))
#     parser.add_argument("-cid", help="PV Compoent ID *required", dest="componentId", metavar="PV Compoent ID", type=int,
#                         required=True, choices=range(0, 1000))
#     results = parser.parse_args()
#     if results:
#         Factor.instance().properties.address = results.projectId


class PeerManager:
    def __init__(self):
        self.peers = {}
        self.max_capacity = Factor.instance().properties.max_capacity
        self.primary_list = []
        self.out_candidate_list = []
        self.in_candidate_list = []

    def get_available_capacity(self):
        return self.max_capacity - len(self.primary_list) - len(self.out_candidate_list) - len(self.in_candidate_list)

    def add_peer(self, peer_id, conn, address, is_primary, is_parent):
        if peer_id in self.peers:
            # bye_message = bytes('BYE...', encoding='utf-8')
            # conn.send(bye_message)
            conn.close()
            return False

        lock.acquire()
        self.peers[peer_id] = (conn, address, is_primary, is_parent)
        lock.release()
        # self.broadcast_message(peer_id, message)
        # print('Add Peer [{0}]'.format(len(self.peers)))

    def remove_peer(self, peer_id):
        if peer_id not in self.peers:
            return False

        lock.acquire()
        del self.peers[peer_id]
        lock.release()
        # self.broadcast_message(peer_id, message)
        # print('Remove Peer [{0}]'.format(len(self.peers)))

    def broadcast_message(self, sender, message):
        bytes_data, bytes_size = convert_message_to_bytes(message)

        for peer_id in self.peers:
            if sender != peer_id:
                conn, address, is_primary, is_parent = self.peers[peer_id]
                if is_primary:
                    conn.send(bytes_size)
                    conn.send(bytes_data)

    def broadcast_message_to_children(self, message):
        bytes_data, bytes_size = convert_message_to_bytes(message)

        for conn, address, is_primary, is_parent in self.peers.values():
            if is_primary and not is_parent:
                conn.send(bytes_size)
                conn.send(bytes_data)

    def get_children_length(self):
        count = 0
        for conn, address, is_primary, is_parent in self.peers.values():
            if is_primary and not is_parent:
                count = count + 1

        return count

    def message_handler(self, peer_id, message):
        if message[0] != '/':
            self.broadcast_message(peer_id, '[{0}] {1}'.format(peer_id, message))
            return

        if message.strip() == '/quit':
            self.remove_peer(peer_id)
            return -1


class TcpHandler(socketserver.BaseRequestHandler):
    peer_manager = PeerManager()
    global PEER_MANAGER
    PEER_MANAGER = peer_manager

    def handle(self):
        print('[{0}:{1}] CONNECT'.format(self.client_address[0], self.client_address[1]))

        try:
            request_message = convert_bytes_to_message(self.request)
            print('[CLIENT] REQUEST_MESSAGE', request_message)

            while request_message:
                method = request_message.get('method')

                if RequestMessageType.HELLO_PEER == method:
                    print('[CLIENT] RECEIVE HELLO_PEER', request_message)
                    response_message = {
                        'response': 202
                    }

                    bytes_data, bytes_size = convert_message_to_bytes(response_message)
                    self.request.send(bytes_size)
                    self.request.send(bytes_data)

                    self.request.close()

                    capacity_count = self.peer_manager.get_available_capacity()
                    if capacity_count > 0:
                        target_peer_id = request_message.get('peer_info').get('peer_id')
                        target_address = request_message.get('peer_info').get('address')
                        establish_socket = send_establish(target_address, HP2P_CORE.peer_id, HP2P_CORE.overlay_id)
                        if establish_socket:
                            self.peer_manager.add_peer(target_peer_id, establish_socket, target_address, False, False)
                    # operation_info = request_message.get('operation_info')
                    # ttl = operation_info['ttl']
                    # operation_info['ttl'] = ttl - 1
                    #
                    # capacity_count = self.peer_manager.get_available_capacity()
                    #
                    # children_length = self.peer_manager.get_children_length()
                    # if children_length > 0:
                    #     conn_num = operation_info['conn_num']
                    #
                    #     assignment = 1 if capacity_count > 0 else 0
                    #     operation_info['conn_num'] = math.ceil((conn_num - assignment) / children_length)
                    #
                    #     self.peer_manager.broadcast_message_to_children(request_message)

                    break
                if RequestMessageType.ESTAB_PEER == method:
                    print('[CLIENT] RECEIVE ESTAB_PEER', request_message)
                    response_message = {
                        'response': 200
                    }

                    bytes_data, bytes_size = convert_message_to_bytes(response_message)
                    self.request.send(bytes_size)
                    self.request.send(bytes_data)

                request_message = convert_bytes_to_message(self.request)

        except Exception as e:
            print('[CLIENT] Error\n', e)

        print('[{0}:{1}] DISCONNECT'.format(self.client_address[0], self.client_address[1]))
        # self.peer_manager.remove_peer(peer_id)


class TcpThreadingSocketServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def main():
    global HP2P_CORE

    input_peer_id = input("input Peer ID:")
    peer = Hp2pCore(input_peer_id)
    HP2P_CORE = peer

    t = threading.Thread(target=start_tcp_server, args=(peer,))
    t.daemon = True
    t.start()

    method = input("Call(creation:c, query:q, end:/end) =>")
    if method.lower() == '/end':
        return
    elif method.lower() == 'creation' or method.lower() == 'c':
        input_title = input("Title =>")
        input_description = input("Description =>")
        input_admin_key = input("Admin Key =>")
        peer.creation(input_title, input_description, input_admin_key)
        peer.join(None)
        peer.report(PEER_MANAGER.max_capacity, PEER_MANAGER.primary_list, PEER_MANAGER.out_candidate_list,
                    PEER_MANAGER.in_candidate_list)
    elif method.lower() == 'query' or method.lower() == 'q':
        peer.query()

    try:
        while True:
            input_method = input("Call(join:j, refresh:r, leave:l, send:s, end:/end) =>")

            if input_method.lower() == '/end':
                break
            elif input_method.lower() == 'join' or input_method.lower() == 'j':
                if peer.isJoinOverlay:
                    print('[CLIENT] Already to join')
                else:
                    input_overlay_id = input("Overlay ID =>")
                    if len(input_overlay_id.strip()) > 0:
                        peer_info_list = peer.join(input_overlay_id)

                        if len(peer_info_list) > 0:
                            for peer_info in peer_info_list:
                                target_peer_id = peer_info.get('peer_id')
                                target_address = peer_info.get('address')
                                print("[CLIENT] Join...", target_peer_id, target_address, flush=True)
                                try:
                                    hello_result = send_hello(target_address, peer.address, peer.peer_id,
                                                              peer.overlay_id)
                                    if hello_result:
                                        break
                                except:
                                    pass
                        else:
                            peer.report(PEER_MANAGER.max_capacity, PEER_MANAGER.primary_list,
                                        PEER_MANAGER.out_candidate_list,
                                        PEER_MANAGER.in_candidate_list)
                            print('[CLIENT] Peer List is None')

            elif input_method.lower() == 'refresh' or input_method.lower() == 'r':
                peer.refresh()
            elif input_method.lower() == 'leave' or input_method.lower() == 'l':
                peer.leave()
            elif input_method.lower() == 'send' or input_method.lower() == 's':
                send_data = input("Send =>")
                if PEER_MANAGER is not None:
                    PEER_MANAGER.broadcast_message('', send_data)
            else:
                print("[CLIENT] not matched..", input_method)
    finally:
        peer.leave()
        peer.removal()

        print('[CLIENT] TCP Server Shutdown')
        TCP_SERVER.shutdown()
        TCP_SERVER.server_close()
        print("[CLIENT] __END__")


def start_tcp_server(peer):
    global TCP_SERVER
    try:
        print('[CLIENT] TCP Server Start.\n')
        address = (Factor.instance().properties.tcp_server_ip, 0)
        server = TcpThreadingSocketServer(address, TcpHandler)
        peer.address = 'tcp://{0}:{1}'.format(server.socket.getsockname()[0], server.socket.getsockname()[1])
        print(peer.address)

        TCP_SERVER = server
        server.serve_forever()
    except KeyboardInterrupt:
        print('[CLIENT] Error KeyboardInterrupt')
        print('\t\t\tTCP Server Shutdown')
        server.shutdown()
        server.server_close()


# def received_message(sock):
#     while True:
#         try:
#             received_size_buffer = sock.recv(4)
#             received_size = str(received_size_buffer, encoding='utf=8')
#             received_buffer = sock.recv(int(received_size))
#             message = str(received_buffer, encoding='utf=8')
#
#             if not message:
#                 break
#
#             print("received_message: ", json.loads(message))
#         except:
#             pass


def send_hello(target_address, address, peer_id, overlay_id):
    if 'tcp://' in target_address:
        _target_address = target_address.replace('tcp://', '')
        ip_port = _target_address.split(':')
        ip = ip_port[0]
        port = int(ip_port[1])

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))

        hello_message = {
            'method': 1,
            'operation_info': {
                'overlay_id': overlay_id,
                'ttl': Factor.instance().properties.ttl,
                'conn_num': Factor.instance().properties.conn_num
            },
            'peer_info': {
                'peer_id': peer_id,
                'address': address
            }
        }
        print('[CORE] SEND HELLO ', hello_message)

        bytes_data, bytes_size = convert_message_to_bytes(hello_message)

        sock.send(bytes_size)
        sock.send(bytes_data)
        response_message = convert_bytes_to_message(sock)
        print('[CORE] HELLO RESPONSE ', response_message)
        sock.close()
        return True if response_message.get('response') == 202 else False


def send_establish(target_address, peer_id, overlay_id):
    if 'tcp://' in target_address:
        _target_address = target_address.replace('tcp://', '')
        ip_port = _target_address.split(':')
        ip = ip_port[0]
        port = int(ip_port[1])

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, port))

        establish_message = {
            'method': 2,
            'operation_info': {
                'overlay_id': overlay_id
            },
            'peer_info': {
                'peer_id': peer_id
            }
        }
        print('[CORE] SEND ESTABLISH ', establish_message)

        bytes_data, bytes_size = convert_message_to_bytes(establish_message)

        sock.send(bytes_size)
        sock.send(bytes_data)
        response_message = convert_bytes_to_message(sock)
        print('[CORE] ESTABLISH RESPONSE ', response_message)
        if response_message.get('response') == 200:
            return sock
        elif response_message.get('response') == 603:
            sock.close()
            return None
        else:
            sock.close()
            return None


if __name__ == '__main__':
    # args_parsing()
    main()

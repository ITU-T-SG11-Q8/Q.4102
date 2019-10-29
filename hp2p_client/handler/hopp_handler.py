# import socket
# import json
# from config import PEER_CONFIG
# from data.factory import Peer
# from classes.hopp_message import HoppMessage
# from classes.constants import RequestMessageType
#
#
# class HoppHandler:
#     def __init__(self):
#         print("[CORE] __init__", flush=True)
#         self._byteorder = 'little'
#         self._encoding = 'utf=8'
#
#     def __del__(self):
#         print("[CORE] __del__", flush=True)
#
#     def convert_bytes_to_message(self, conn):
#         try:
#             hopp_message = HoppMessage()
#
#             received_buffer = conn.recv(1)
#             hopp_message.version = int.from_bytes(received_buffer, self._byteorder)
#
#             received_buffer = conn.recv(1)
#             hopp_message.type = int.from_bytes(received_buffer, self._byteorder)
#
#             received_buffer = conn.recv(2)
#             hopp_message.length = int.from_bytes(received_buffer, self._byteorder)
#
#             received_buffer = conn.recv(hopp_message.length)
#             hopp_message.header = json.loads(str(received_buffer, encoding=self._encoding))
#
#             if hopp_message.type == RequestMessageType.BROADCAST_DATA:
#                 content_length = hopp_message.header.get('payload').get('length')
#                 received_buffer = conn.recv(content_length)
#                 hopp_message.content = str(received_buffer, encoding=self._encoding)
#
#             return hopp_message
#         except Exception as e:
#             print('[HOPP] Error convert_bytes_to_message\n', e)
#             return None
#
#     def convert_data_to_bytes(self, data):
#         try:
#             bytes_data = bytes(data, encoding=self._encoding)
#             bytes_length = len(bytes_data)
#             return bytes_data, bytes_length
#         except Exception as e:
#             print('[HOPP] Error convert_data_to_bytes\n', e)
#             return None
#
#     def convert_message_to_bytes(self, message_type, message, bytes_data=None):
#         try:
#             bytes_version = RequestMessageType.VERSION.to_bytes(1, self._byteorder)
#             bytes_type = message_type.to_bytes(1, self._byteorder)
#             bytes_header = bytes(json.dumps(message), encoding=self._encoding)
#             bytes_length = len(bytes_header).to_bytes(2, self._byteorder)
#             if bytes_data is None:
#                 return bytes_version + bytes_type + bytes_length + bytes_header
#             else:
#                 return bytes_version + bytes_type + bytes_length + bytes_header + bytes_data
#         except Exception as e:
#             print('[HOPP] Error convert_message_to_bytes\n', e)
#             return None
#
#     def send_hello_peer(self, peer: Peer, target_address):
#         if 'tcp://' in target_address:
#             try:
#                 _target_address = target_address.replace('tcp://', '')
#                 ip_port = _target_address.split(':')
#                 ip = ip_port[0]
#                 port = int(ip_port[1])
#
#                 sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 sock.connect((ip, port))
#                 print('[{0}:{1}] CONNECT OUT GOING SOCKET'.format(sock.getsockname()[0], sock.getsockname()[1]))
#
#                 hello_message = {
#                     'ReqCode': 1,
#                     'operation': {
#                         'overlay_id': peer.overlay_id,
#                         'conn_num': PEER_CONFIG['ESTAB_PEER_MAX_COUNT'],
#                         'ttl': PEER_CONFIG['HELLO_PEER_TTL']
#                     },
#                     'peer': {
#                         'peer_id': peer.peer_id,
#                         'address': peer.get_address(),
#                         'ticket_id': peer.ticket_id
#                     }
#                 }
#
#                 print('[CORE] SEND HELLO REQUEST', hello_message)
#                 request_message = self.convert_message_to_bytes(RequestMessageType.HELLO_PEER, hello_message)
#                 sock.send(request_message)
#
#                 response_message: HoppMessage = self.convert_bytes_to_message(sock)
#                 print('[CORE] RECEIVED HELLO RESPONSE ', response_message.header)
#                 print('[{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0], sock.getsockname()[1]))
#                 sock.close()
#
#                 return True if response_message.header.get('RspCode') == 1202 else False
#             except Exception as e:
#                 print('[HOPP] Error send_hello\n', e)
#                 return None
#         else:
#             return None
#
#     def send_estab_peer(self, peer: Peer, target_address):
#         if 'tcp://' in target_address:
#             try:
#                 _target_address = target_address.replace('tcp://', '')
#                 ip_port = _target_address.split(':')
#                 ip = ip_port[0]
#                 port = int(ip_port[1])
#
#                 sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#                 sock.connect((ip, port))
#                 print('[{0}:{1}] CONNECT OUT GOING SOCKET'.format(sock.getsockname()[0], sock.getsockname()[1]))
#
#                 establish_message = {
#                     'ReqCode': 2,
#                     'operation': {
#                         'overlay_id': peer.overlay_id
#                     },
#                     'peer': {
#                         'peer_id': peer.peer_id,
#                         'ticket_id': peer.ticket_id
#                     }
#                 }
#
#                 print('[CORE] SEND ESTABLISH REQUEST', establish_message)
#                 request_message = self.convert_message_to_bytes(RequestMessageType.ESTAB_PEER, establish_message)
#                 sock.send(request_message)
#
#                 response_message: HoppMessage = self.convert_bytes_to_message(sock)
#                 print('[CORE] RECEIVED ESTABLISH RESPONSE', response_message.header)
#
#                 if response_message.header.get('RspCode') == 2200:
#                     return sock
#                 elif response_message.header.get('RspCode') == 2603:
#                     print('[{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0], sock.getsockname()[1]))
#                     sock.close()
#                     return None
#                 else:
#                     print('[{0}:{1}] DISCONNECT OUT GOING SOCKET'.format(sock.getsockname()[0], sock.getsockname()[1]))
#                     sock.close()
#                     return None
#             except Exception as e:
#                 print('[HOPP] Error send_establish\n', e)
#                 return None
#         else:
#             return None

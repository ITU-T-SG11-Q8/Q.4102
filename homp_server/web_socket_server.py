#!/usr/bin/env python
#
# Simple websocket server to perform signaling.
#

import asyncio
import binascii
import os
import websockets

import json
from config import WEB_SOCKET_CONFIG

peer_connections = {}


async def handler(web_socket, path):
    peer_id = None

    try:
        async for message in web_socket:
            print(message)
            json_data = json.loads(message)

            if 'action' in json_data:
                action = json_data.get('action')
                if action == 'hello':
                    peer_id = json_data.get('peer_id')
                    result = peer_id not in peer_connections.keys()
                    if result:
                        peer_connections[peer_id] = web_socket
                        print('Add Connection...', peer_id)
                        print(peer_connections.keys())

                    result_message = {
                        'action': 'hello',
                        'result': result
                    }
                    await web_socket.send(json.dumps(result_message))
                elif action == 'bye':
                    print('bye ...', peer_id)
                    break
                elif action == 'hello_peer':
                    to_peer_id = json_data.get('to_peer_id')
                    if to_peer_id in peer_connections.keys():
                        connection = peer_connections[to_peer_id]
                        await connection.send(message)
                    else:
                        result_message = {
                            'action': 'hello_peer',
                            'result': False
                        }
                        await web_socket.send(json.dumps(result_message))
            else:
                from_id = json_data.get('fromid')
                to_id = json_data.get('toid')
                if from_id in peer_connections and to_id in peer_connections:
                    connection = peer_connections[to_id]
                    await connection.send(message)
    finally:
        if peer_id is not None:
            peer_connections.pop(peer_id)
            print('Remove Connection...', peer_id)
            print(peer_connections.keys())


if __name__ == '__main__':
    try:
        host = WEB_SOCKET_CONFIG['HOST']
        port = WEB_SOCKET_CONFIG['PORT']
        print("[WebSocketServer] Start... {0}:{1}".format(host, port), flush=True)
        asyncio.get_event_loop().run_until_complete(websockets.serve(handler, host, port))
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print("[WebSocketServer] Stop...", flush=True)
        asyncio.get_event_loop().close()
        print("[WebSocketServer] Close...", flush=True)

# class WebSocketServer:
#     def __init__(self):
#         self.clients = {}
#
#     async def echo(self, web_socket, path):
#         client_id = binascii.hexlify(os.urandom(8))
#         self.clients[client_id] = web_socket
#
#         try:
#             async for message in web_socket:
#                 for client in self.clients.values():
#                     if client != web_socket:
#                         print(message)
#                         await client.send(message)
#         finally:
#             self.clients.pop(client_id)
#
#     def run_server(self):
#         print("[WebSocketServer] run...", flush=True)
#         asyncio.get_event_loop().run_until_complete(websockets.serve(self.echo, '0.0.0.0', 8899))
#         asyncio.get_event_loop().run_forever()
#
#     def start(self):
#         print("[WebSocketServer] Start...", flush=True)
#         t = threading.Thread(target=self.run_server, args=())
#         t.start()

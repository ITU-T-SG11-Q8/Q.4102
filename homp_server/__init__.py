import sys
import json
import threading
import os.path
from flask import Flask, Response
from flask_restful import Api
from config import SERVER_CONFIG, WEB_SOCKET_CONFIG
from util.utils import Utils
from datetime import datetime
from data.factory import Factory, Overlay
from classes.peer import Peer
from handler.overlay_handler import HybridOverlayCreation, HybridOverlayModification, HybridOverlayQuery, \
    HybridOverlayRemoval, ApiHybridOverlayRemoval
from handler.peer_handler import HybridOverlayJoin, HybridOverlayLeave, HybridOverlayRefresh, HybridOverlayReport
from simple_websocket_server import WebSocketServer, WebSocket
from expires_scheduler import ExpiresScheduler

app = Flask(__name__)
# app.config.from_object('config')
app.static_folder = SERVER_CONFIG['WEB_ROOT']
api = Api(app)


def root_dir():
    return os.path.abspath(os.path.dirname(__file__))


def get_file(filename, is_encoding=False):
    try:
        src = os.path.join(root_dir(), SERVER_CONFIG['WEB_ROOT'], filename)
        if is_encoding:
            return open(src, 'r', encoding='UTF-8').read()
        else:
            return open(src).read()
    except IOError as exc:
        return str(exc)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/<path:filename>')
def static_file(filename):
    splitext = os.path.splitext(filename)
    ext = splitext[len(splitext) - 1]
    if ext == ".js":
        path = filename.replace("/", "\\")
        complete_path = os.path.join(root_dir(), SERVER_CONFIG['WEB_ROOT'], path)
        content = get_file(complete_path)
        return Response(content, mimetype="application/javascript")
    # elif ext == ".ico":
    #     path = filename.replace("/", "\\")
    #     complete_path = os.path.join(root_dir(), SERVER_CONFIG['WEB_ROOT'], path)
    #     content = get_file(complete_path, True)
    #     return Response(content, mimetype="image/x-icon")
    else:
        return app.send_static_file(filename)


# @app.route('/', methods=['GET'])
# def metrics():
#     content = get_file('index.html')
#     return Response(content, mimetype="text/html")


# @app.route('/<path:path>')
# def get_resource(path):  # pragma: no cover
#     mime_types = {
#         ".css": "text/css",
#         ".html": "text/html",
#         ".js": "application/javascript"
#     }
#     path = path.replace("/", "\\")
#     complete_path = os.path.join(root_dir(), SERVER_CONFIG['WEB_ROOT'], path)
#     splitext = os.path.splitext(path)
#     ext = splitext[len(splitext) - 1]
#     mime_type = mime_types.get(ext, "text/plain")
#     content = get_file(complete_path)
#     return Response(content, mimetype=mime_type)


api.add_resource(HybridOverlayCreation, '/HybridOverlayCreation')
api.add_resource(HybridOverlayQuery, '/HybridOverlayQuery')
api.add_resource(HybridOverlayModification, '/HybridOverlayModification')
api.add_resource(HybridOverlayRemoval, '/HybridOverlayRemoval')

api.add_resource(HybridOverlayJoin, '/HybridOverlayJoin')
api.add_resource(HybridOverlayReport, '/HybridOverlayReport')
api.add_resource(HybridOverlayRefresh, '/HybridOverlayRefresh')
api.add_resource(HybridOverlayLeave, '/HybridOverlayLeave')

api.add_resource(ApiHybridOverlayRemoval, '/api/HybridOverlayRemoval')


def checked_expires():
    overlay_dic = Factory.instance().get_overlay_dict()
    print("Run scheduler", datetime.now())
    for item in overlay_dic.values():
        overlay: Overlay = item
        print("Overlay ID:", overlay.overlay_id)
        peer_dict = overlay.get_peer_dict()
        for p_item in peer_dict.values():
            peer: Peer = p_item
            print("     Peer ID:", peer.peer_id)


class WebSocketHandler(WebSocket):
    def handle(self):
        print(self.address, 'message', self.data)
        try:
            data_dic = json.loads(self.data)
            if 'server' in data_dic:
                if data_dic.get('action') == 'hello':
                    Factory.instance().get_web_socket_handler().append_web_socket_client(self)
                elif data_dic.get('action') == 'get' and data_dic.get('overlay_id') is not None:
                    overlay = Factory.instance().get_overlay(data_dic.get('overlay_id'))
                    if overlay is not None:
                        message = Factory.instance().get_web_socket_handler().create_overlay_cost_map_message(overlay)
                        self.send_message(json.dumps(message))
            else:
                if 'peer_id' in data_dic:
                    peer_id = data_dic.get('peer_id')
                    if data_dic.get('action') == 'hello':
                        Factory.instance().get_web_socket_handler().add_web_socket_peer(peer_id, self)
                    elif data_dic.get('action') == 'bye':
                        Factory.instance().get_web_socket_handler().delete_web_socket_peer(self)
                elif 'to_peer_id' in data_dic:
                    to_peer_id = data_dic.get('to_peer_id')
                    if data_dic.get('action') == 'hello_peer':
                        result = Factory.instance().get_web_socket_handler().send_message_to_peer(to_peer_id, data_dic)
                        if not result:
                            self.send_message(json.dumps({'action': 'failed_hello_peer'}))
                elif 'toid' in data_dic:
                    to_id = data_dic.get('toid')
                    Factory.instance().get_web_socket_handler().send_message_to_peer(to_id, data_dic)
                else:
                    print('Error...')
        except:
            pass

    def connected(self):
        print(self.address, 'connected')

    def handle_close(self):
        print(self.address, 'closed')
        Factory.instance().get_web_socket_handler().remove_web_socket_client(self)
        Factory.instance().get_web_socket_handler().delete_web_socket_peer(self)


def run_web_socket_server():
    print("[SERVER] Start Web Socket Server...", flush=True)
    server = WebSocketServer(WEB_SOCKET_CONFIG['HOST'], WEB_SOCKET_CONFIG['PORT'], WebSocketHandler)
    Factory.instance().get_web_socket_handler().set_web_socket_server(server)
    server.serve_forever()


if __name__ == '__main__':
    Utils.create_overlay_map()
    debug_mode = SERVER_CONFIG['DEBUG']
    if len(sys.argv) > 1 and sys.argv[1] == '--prod':
        debug_mode = False
        print("[SERVER] mode is production", flush=True)
    else:
        print("[SERVER] mode is development", flush=True)

    # TODO - expires 관리자 싷행
    # scheduler = ExpiresScheduler()
    # scheduler.start(checked_expires)

    t = threading.Thread(target=run_web_socket_server)
    t.daemon = True
    t.start()

    print("[SERVER] Start Server...", flush=True)
    app.run(host=SERVER_CONFIG['HOST'], port=SERVER_CONFIG['PORT'], debug=debug_mode)

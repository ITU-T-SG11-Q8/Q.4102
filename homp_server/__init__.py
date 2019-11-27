import sys
import os.path
import atexit

from flask import Flask, Response
from flask_restful import Api

from config import SERVER_CONFIG
from service.service import Service
from database.db_connector import DBConnector
from database.db_manager import DBManager
from handler.overlay_handler import HybridOverlayCreation, HybridOverlayModification, HybridOverlayQuery, \
    HybridOverlayRemoval, ApiHybridOverlayRemoval, GetInitData, GetOverlayCostMap
from handler.peer_handler import HybridOverlayJoin, HybridOverlayLeave, HybridOverlayRefresh, HybridOverlayReport
from web_socket.web_socket_server import Hp2pWebSocketServer
from expires_scheduler import ExpiresScheduler

# Set Flask Api
app = Flask(__name__)
app.static_folder = SERVER_CONFIG['WEB_ROOT']
api = Api(app)


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
    else:
        return app.send_static_file(filename)


api.add_resource(HybridOverlayCreation, '/HybridOverlayCreation')
api.add_resource(HybridOverlayQuery, '/HybridOverlayQuery')
api.add_resource(HybridOverlayModification, '/HybridOverlayModification')
api.add_resource(HybridOverlayRemoval, '/HybridOverlayRemoval')
api.add_resource(HybridOverlayJoin, '/HybridOverlayJoin')
api.add_resource(HybridOverlayReport, '/HybridOverlayReport')
api.add_resource(HybridOverlayRefresh, '/HybridOverlayRefresh')
api.add_resource(HybridOverlayLeave, '/HybridOverlayLeave')
api.add_resource(ApiHybridOverlayRemoval, '/api/HybridOverlayRemoval')
api.add_resource(GetInitData, '/api/InitData')
api.add_resource(GetOverlayCostMap, '/api/OverlayCostMap')


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


def remove_expires_peer_callback(overlay_id, peer_id):
    db_connector = DBConnector()
    try:
        db_connector.delete("DELETE FROM hp2p_peer WHERE peer_id = %s AND overlay_id = %s", (peer_id, overlay_id))
        Service.get().get_overlay(overlay_id).delete_peer(peer_id)
        Service.get().get_web_socket_handler().send_log_message(overlay_id, peer_id, "Overlay Leave.")
        print("\n[ExpiresScheduler] Remove Peer...", overlay_id, peer_id)

        get_overlay = Service.get().get_overlay(overlay_id)
        if get_overlay.get_peer_dict_len() < 1:
            db_connector.delete("DELETE FROM hp2p_auth_peer WHERE overlay_id = %s", (overlay_id,))
            db_connector.delete("DELETE FROM hp2p_peer WHERE overlay_id = %s", (overlay_id,))
            db_connector.delete("DELETE FROM hp2p_overlay WHERE overlay_id = %s", (overlay_id,))

            Service.get().delete_overlay(overlay_id)
            Service.get().get_web_socket_handler().send_remove_overlay_message(overlay_id)
            Service.get().get_web_socket_handler().send_log_message(overlay_id, peer_id, "Overlay Removal.")
            print("\n[ExpiresScheduler] Remove Overlay (Peers is None)", overlay_id, peer_id)
        else:
            Service.get().get_web_socket_handler().send_delete_peer_message(overlay_id, peer_id)

        db_connector.commit()
    except:
        db_connector.rollback()


scheduler = None


@atexit.register
def goodbye():
    if scheduler is not None:
        print('[STOP] ExpiresScheduler...')
        scheduler.stop()

    input('goodbye...')


if __name__ == '__main__':

    debug_mode = SERVER_CONFIG['DEBUG'] if 'DEBUG' in SERVER_CONFIG else False
    if len(sys.argv) > 1 and sys.argv[1] == '--prod':
        debug_mode = False
        print("[SERVER] mode is production", flush=True)
    else:
        print("[SERVER] mode is development", flush=True)

    db_manager = DBManager()
    db_init = db_manager.init()

    if db_init:
        if 'CLEAR_DATABASE' in SERVER_CONFIG and SERVER_CONFIG['CLEAR_DATABASE']:
            db_manager.clear_database()
        elif 'RECOVERY_DATABASE' in SERVER_CONFIG and SERVER_CONFIG['RECOVERY_DATABASE']:
            db_manager.create_overlay_map()

        if 'USING_EXPIRES_SCHEDULER' in SERVER_CONFIG and SERVER_CONFIG['USING_EXPIRES_SCHEDULER']:
            scheduler = ExpiresScheduler()
            scheduler.start(SERVER_CONFIG['EXPIRES_SCHEDULER_INTERVAL'], remove_expires_peer_callback)

        web_socket_server = Hp2pWebSocketServer()
        web_socket_server.start()

        print("[SERVER] Start Server...", flush=True)
        app.run(host=SERVER_CONFIG['HOST'], port=SERVER_CONFIG['PORT'], debug=debug_mode)
    else:
        print("[DATABASE] Create Error...", flush=True)
        print("[END] ...", flush=True)

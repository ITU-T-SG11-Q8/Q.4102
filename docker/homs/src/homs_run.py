import os.path
import atexit
from flask import Flask, Response
from flask_restful import Api
import argparse

from config import SERVER_CONFIG, WEB_SOCKET_CONFIG
from data.server_scheduler import ServerScheduler
from database.db_manager import DBManager
from handler.overlay_handler import HybridOverlayCreation, HybridOverlayModification, HybridOverlayQuery, \
    HybridOverlayRemoval, ApiHybridOverlayRemoval, GetInitData, GetOverlayCostMap
from handler.peer_handler import HybridOverlayJoin, HybridOverlayLeave, HybridOverlayRefresh, HybridOverlayReport
from web_socket.web_socket_server import Hp2pWebSocketServer

app = Flask(__name__)
app.static_folder = SERVER_CONFIG['WEB_ROOT']
api = Api(app)
scheduler = None


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


@atexit.register
def goodbye():
    if scheduler is not None:
        print('[STOP] ExpiresScheduler...')
        scheduler.stop()

    input('goodbye...')


def args_parsing():
    parser = argparse.ArgumentParser(
        prog="Data Collector"
    )
    parser.add_argument("-port", help="HOMS Port 정보를 설정한다.", dest="port", type=int, default=8081,
                        metavar="HOMS Port", required=False)
    parser.add_argument("-ws-port", help="HOMS WebSocket Port 정보를 설정한다.", dest="ws_port", type=int, default=8082,
                        metavar="HOMS WebSocket Port", required=False)
    return parser.parse_args()


if __name__ == '__main__':
    debug_mode = SERVER_CONFIG['DEBUG'] if 'DEBUG' in SERVER_CONFIG else False

    arg_results = args_parsing()
    SERVER_CONFIG['PORT'] = arg_results.port
    WEB_SOCKET_CONFIG['PORT'] = arg_results.ws_port

    db_manager = DBManager()
    db_init = db_manager.init()

    if db_init:
        if 'CLEAR_DATABASE' in SERVER_CONFIG and SERVER_CONFIG['CLEAR_DATABASE']:
            db_manager.clear_database()
        elif 'RECOVERY_DATABASE' in SERVER_CONFIG and SERVER_CONFIG['RECOVERY_DATABASE']:
            db_manager.create_overlay_map()

        if 'USING_EXPIRES_SCHEDULER' in SERVER_CONFIG and SERVER_CONFIG['USING_EXPIRES_SCHEDULER']:
            scheduler = ServerScheduler()
            scheduler.start(SERVER_CONFIG['EXPIRES_SCHEDULER_INTERVAL'])

        web_socket_server = Hp2pWebSocketServer()
        web_socket_server.start()

        print("[SERVER] START...")
        app.run(host=SERVER_CONFIG['HOST'], port=SERVER_CONFIG['PORT'], debug=debug_mode)
    else:
        print("[SERVER] END...")

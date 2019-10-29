from config import SERVER_CONFIG
from util.utils import Utils
from handler.overlay_handler import *
from handler.peer_handler import *
from flask import Flask
from flask_restful import Api
from expires_scheduler import ExpiresScheduler
import sys

app = Flask(__name__)
# app.config.from_object('config')
app.static_folder = SERVER_CONFIG['WEB_ROOT']
api = Api(app)


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/<path:filename>')
def static_file(filename):
    return app.send_static_file(filename)


api.add_resource(HybridOverlayCreation, '/HybridOverlayCreation')
api.add_resource(HybridOverlayQuery, '/HybridOverlayQuery')
api.add_resource(HybridOverlayModification, '/HybridOverlayModification')
api.add_resource(HybridOverlayRemoval, '/HybridOverlayRemoval')

api.add_resource(HybridOverlayJoin, '/HybridOverlayJoin')
api.add_resource(HybridOverlayReport, '/HybridOverlayReport')
api.add_resource(HybridOverlayRefresh, '/HybridOverlayRefresh')
api.add_resource(HybridOverlayLeave, '/HybridOverlayLeave')


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


if __name__ == '__main__':

    Utils.create_overlay_map()

    debug_mode = SERVER_CONFIG['DEBUG']
    if len(sys.argv) > 1 and sys.argv[1] == '--prod':
        debug_mode = False
        print("[SERVER] mode is production", flush=True)
    else:
        print("[SERVER] mode is development", flush=True)

    # scheduler = ExpiresScheduler()
    # scheduler.start(checked_expires)

    print("[SERVER] Start Server...", flush=True)
    app.run(host=SERVER_CONFIG['HOST'], port=SERVER_CONFIG['PORT'], debug=debug_mode)

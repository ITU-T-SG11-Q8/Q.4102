from server.config import SERVER_CONFIG
from server.utils import Utils
import server.overlay_handler as Overlay
import server.peer_handler as Peer
from flask import Flask
from flask_restful import Api
from server.factory import Factory

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


api.add_resource(Overlay.HybridOverlayCreation, '/HybridOverlayCreation')
api.add_resource(Overlay.HybridOverlayQuery, '/HybridOverlayQuery')
api.add_resource(Overlay.HybridOverlayModification, '/HybridOverlayModification')
api.add_resource(Overlay.HybridOverlayRemoval, '/HybridOverlayRemoval')

api.add_resource(Peer.HybridOverlayJoin, '/HybridOverlayJoin')
api.add_resource(Peer.HybridOverlayReport, '/HybridOverlayReport')
api.add_resource(Peer.HybridOverlayRefresh, '/HybridOverlayRefresh')
api.add_resource(Peer.HybridOverlayLeave, '/HybridOverlayLeave')

if __name__ == '__main__':
    Utils.CreateOverlayMap()

    print("[SERVER] Start Server...", flush=True)
    app.run(host=SERVER_CONFIG['HOST'], port=SERVER_CONFIG['PORT'], debug=SERVER_CONFIG['DEBUG'])
    # x = {
    #     "name": "John",
    #     "age": 30,
    #     "city": "New York"
    # }
    # y = json.dumps(x)
    # z = json.loads(y)
    #
    # print(x)
    # print(y)
    # print(z)
    #
    # a = str(x)
    # b = str(y)
    # c = str(z)
    # print(a)
    # print(b)
    # print(c)

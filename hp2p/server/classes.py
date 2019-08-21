# from datetime import datetime


class Overlay:
    def __init__(self, overlay_id):
        self.overlay_id = overlay_id
        self.peer_index = 0
        self.peer_id_list = []


class Peer:
    def __init__(self):
        self.overlay_id = None
        self.peer_id = None
        self.peer_index = 0
        # self.expires = 0
        # self.expires_time = datetime.now()

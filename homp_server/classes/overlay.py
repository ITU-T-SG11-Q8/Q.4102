class Overlay:
    def __init__(self):
        self.overlay_id = None
        self.current_ticket_id = 0
        self.expires = 0
        self.heartbeat_interval = 0
        self.heartbeat_timeout = 0
        self._peer_dic = {}
        self.update_time = None

    def add_peer(self, key, peer):
        self._peer_dic[key] = peer

    def get_peer(self, key):
        return self._peer_dic[key] if key in self._peer_dic else None

    def delete_peer(self, key):
        del self._peer_dic[key]

    def get_peer_dict_len(self):
        return len(self._peer_dic)

    def get_peer_dict(self):
        return self._peer_dic

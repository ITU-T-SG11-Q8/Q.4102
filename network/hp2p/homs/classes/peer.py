class Peer:
    def __init__(self):
        self.overlay_id = None
        self.peer_id = None
        self.ticket_id = 0
        self.expires = 0
        self.update_time = None

        self.num_primary = 0
        self.num_out_candidate = 0
        self.num_in_candidate = 0
        self.costmap = {}

from datetime import datetime


class PeerConnection:
    def __init__(self, peer_id, ticket_id, is_primary, is_parent, connection, address):
        self.peer_id = peer_id
        self.ticket_id = ticket_id
        self.is_primary = is_primary
        self.is_parent = is_parent
        self.connection = connection
        self.address = address
        self.update_time = datetime.now()

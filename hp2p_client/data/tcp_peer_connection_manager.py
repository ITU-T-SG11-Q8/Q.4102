import threading
from config import PEER_CONFIG
from classes.peer_connection_manager import PeerConnectionManager, PeerConnection

lock = threading.Lock()


class TcpPeerConnectionManager(PeerConnectionManager):
    def get_peer_id_by_connection(self, connection):
        result_peer_id = None
        for peer_id in self.peers:
            connection: PeerConnection = self.peers[peer_id]
            if connection.connection == connection:
                result_peer_id = peer_id
                break

        return result_peer_id

    def send_message(self, message):
        for p_value in self.peers.values():
            if type(p_value) == PeerConnection:
                connection: PeerConnection = p_value
                if connection.is_primary:
                    connection.connection.send(message)

    def broadcast_message(self, sender, message):
        for p_value in self.peers.values():
            if type(p_value) == PeerConnection:
                connection: PeerConnection = p_value
                if connection.peer_id != sender and connection.is_primary:
                    connection.connection.send(message)

    def broadcast_message_to_children(self, message):
        for p_value in self.peers.values():
            if type(p_value) == PeerConnection:
                connection: PeerConnection = p_value
                if connection.is_primary and not connection.is_parent:
                    connection.connection.send(message)

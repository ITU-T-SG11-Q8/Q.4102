from classes.peer_connection_manager import PeerConnectionManager, PeerConnection
import threading

lock = threading.Lock()


class TcpPeerConnectionManager(PeerConnectionManager):

    def get_peer_id_by_connection(self, connection):
        lock.acquire()

        result_peer_id = None
        for peer_id in self._peers:
            peer_connection: PeerConnection = self._peers[peer_id]
            if peer_connection.connection == connection:
                result_peer_id = peer_id
                break
        lock.release()

        return result_peer_id

    def send_message(self, message):
        lock.acquire()
        failed_connections = []

        for p_value in self._peers.values():
            if type(p_value) == PeerConnection:
                connection: PeerConnection = p_value
                if connection.is_primary:
                    try:
                        connection.connection.sendall(message)
                    except:
                        failed_connections.append(connection)

        if len(failed_connections) > 0:
            for remove_peer_connection in failed_connections:
                remove_peer_connection.connection.close()
                # self.clear_peer(remove_peer_connection.peer_id)

        lock.release()

    def send_message_to_peer(self, peer_id, message):
        lock.acquire()
        connection: PeerConnection = self.get_peer_connection(peer_id)

        if connection is not None:
            try:
                connection.connection.sendall(message)
            except:
                connection.connection.close()

        lock.release()

    def broadcast_message(self, sender, message):
        lock.acquire()
        failed_connections = []

        for p_value in self._peers.values():
            if type(p_value) == PeerConnection:
                connection: PeerConnection = p_value
                if connection.peer_id != sender and connection.is_primary:
                    try:
                        connection.connection.sendall(message)
                    except:
                        failed_connections.append(connection)

        if len(failed_connections) > 0:
            for remove_peer_connection in failed_connections:
                remove_peer_connection.connection.close()
                # self.clear_peer(remove_peer_connection.peer_id)

        lock.release()

    def broadcast_message_to_children(self, message):
        lock.acquire()
        failed_connections = []

        for p_value in self._peers.values():
            if type(p_value) == PeerConnection:
                connection: PeerConnection = p_value
                if connection.is_primary and not connection.is_parent:
                    try:
                        connection.connection.sendall(message)
                    except:
                        failed_connections.append(connection)

        if len(failed_connections) > 0:
            for remove_peer_connection in failed_connections:
                remove_peer_connection.connection.close()
                # self.clear_peer(remove_peer_connection.peer_id)

        lock.release()

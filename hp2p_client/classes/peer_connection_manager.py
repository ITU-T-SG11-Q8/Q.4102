from abc import *
import threading
from config import PEER_CONFIG
from classes.peer_connection import PeerConnection

lock = threading.Lock()


class PeerConnectionManager(metaclass=ABCMeta):
    def __init__(self):
        self.peers = {}

        self.max_primary_connection = PEER_CONFIG['MAX_PRIMARY_CONNECTION']
        self.max_in_candidate = PEER_CONFIG['MAX_INCOMING_CANDIDATE']
        self.max_out_candidate = PEER_CONFIG['MAX_OUTGOING_CANDIDATE']

        self.primary_list = []
        self.out_candidate_list = []
        self.in_candidate_list = []

        self.is_run_probe_peer = False
        self.estab_peers = {}
        self.is_run_primary_peer = False

        self.is_send_heartbeat = True
        self.is_destroy = False

    def get_children_count(self):
        count = 0
        for connection in self.peers.values():
            if connection.is_primary and not connection.is_parent:
                count = count + 1
        return count

    def get_in_candidate_remove_peer_id(self, target_peer_id, target_ticket_id):
        remove_peer_id = None
        lock.acquire()
        if self.max_in_candidate <= len(self.in_candidate_list) and target_peer_id not in self.in_candidate_list:
            max_ticket_id = 0
            for peer_id in self.in_candidate_list:
                connection: PeerConnection = self.peers[peer_id]
                if connection.ticket_id > target_ticket_id:
                    max_ticket_id = max(max_ticket_id, connection.ticket_id)
                    if max_ticket_id == connection.ticket_id:
                        remove_peer_id = connection.peer_id

        if remove_peer_id is not None:
            self.in_candidate_list.remove(remove_peer_id)
            self.in_candidate_list.append(target_peer_id)

        lock.release()
        return remove_peer_id

    def get_estab_peers(self):
        lock.acquire()
        estab_peers = self.estab_peers.copy()
        lock.release()
        return estab_peers

    def establish_peer(self, peer_id):
        result = False
        lock.acquire()

        if self.max_out_candidate - len(self.out_candidate_list) > 0 and peer_id not in self.out_candidate_list:
            self.out_candidate_list.append(peer_id)
            self.estab_peers[peer_id] = None
            result = True

        lock.release()
        return result

    def un_establish_peer(self, peer_id):
        lock.acquire()
        self.out_candidate_list.remove(peer_id)
        lock.release()

    def assignment_peer(self, peer_id):
        result = False
        lock.acquire()

        if self.max_in_candidate - len(self.in_candidate_list) > 0 and peer_id not in self.in_candidate_list:
            self.in_candidate_list.append(peer_id)
            result = True

        lock.release()
        return result

    def un_assignment_peer(self, peer_id):
        lock.acquire()
        self.in_candidate_list.remove(peer_id)
        lock.release()

    def set_primary_peer(self, peer_id, is_out_going):
        result = False

        if peer_id not in self.peers:
            return result

        lock.acquire()
        if self.max_primary_connection - len(self.primary_list) > 0:
            if is_out_going and peer_id in self.out_candidate_list:
                self.out_candidate_list.remove(peer_id)
                result = True
            elif not is_out_going and peer_id in self.in_candidate_list:
                self.in_candidate_list.remove(peer_id)
                result = True

            if result:
                connection: PeerConnection = self.peers[peer_id]
                connection.is_primary = True
                self.primary_list.append(peer_id)
                print('SET_PRIMARY_PEER', peer_id)
                print('     ', self.primary_list)
        lock.release()

        return result

    def add_peer(self, peer_id, ticket_id, is_primary, is_parent, connection, address=None):
        if peer_id in self.peers:
            return False

        if peer_id in self.in_candidate_list or peer_id in self.out_candidate_list:
            lock.acquire()
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ADD PEER', peer_id)
            self.peers[peer_id] = PeerConnection(peer_id, ticket_id, is_primary, is_parent, connection, address)
            lock.release()
            return True

        return False

    def remove_peer(self, peer_id):
        if peer_id not in self.peers:
            return False

        lock.acquire()
        del self.peers[peer_id]
        lock.release()

        return True

    def clear_peer(self, peer_id):
        print('$$$$CLEAR PEER', peer_id)
        lock.acquire()

        if peer_id in self.peers:
            del self.peers[peer_id]

        if peer_id in self.primary_list:
            self.primary_list.remove(peer_id)

        if peer_id in self.in_candidate_list:
            self.in_candidate_list.remove(peer_id)

        if peer_id in self.out_candidate_list:
            self.out_candidate_list.remove(peer_id)

        lock.release()

    def get_peer_connection(self, peer_id):
        if peer_id in self.peers:
            return self.peers[peer_id]
        return None

    def get_all_peer_connection(self):
        return self.peers

    @abstractmethod
    def get_peer_id_by_connection(self, connection):
        pass

    @abstractmethod
    def send_message(self, message):
        pass

    @abstractmethod
    def broadcast_message(self, sender, message):
        pass

    @abstractmethod
    def broadcast_message_to_children(self, message):
        pass

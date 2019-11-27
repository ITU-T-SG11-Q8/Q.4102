from abc import *
import threading
from config import PEER_CONFIG
from classes.peer_connection import PeerConnection

lock = threading.Lock()


class PeerConnectionManager(metaclass=ABCMeta):
    def __init__(self):
        self._peers = {}

        self.max_primary_connection = PEER_CONFIG['MAX_PRIMARY_CONNECTION']
        self.max_in_candidate = PEER_CONFIG['MAX_INCOMING_CANDIDATE']
        self.max_out_candidate = PEER_CONFIG['MAX_OUTGOING_CANDIDATE']

        self._primary_list = []
        self._out_going_candidate_list = []
        self._in_coming_candidate_list = []

        self._estab_peers = {}
        self._failed_primary_list = []

        self.is_run_probe_peer = False
        self.is_run_primary_peer = False
        self.is_send_heartbeat = True
        self.is_destroy = False
        self.is_first_peer_set_primary = False

    def get_in_coming_candidate_list(self):
        lock.acquire()
        _in_coming_candidate_list = self._in_coming_candidate_list.copy()
        lock.release()
        return _in_coming_candidate_list

    def get_out_going_candidate_list(self):
        lock.acquire()
        _out_going_candidate_list = self._out_going_candidate_list.copy()
        lock.release()
        return _out_going_candidate_list

    def get_primary_list(self):
        lock.acquire()
        _primary_list = self._primary_list.copy()
        lock.release()
        return _primary_list

    def is_in_primary_list(self, peer_id):
        lock.acquire()
        result = peer_id in self._primary_list
        lock.release()
        return result

    def has_primary(self):
        lock.acquire()
        result = len(self._primary_list) > 0
        lock.release()
        return result

    def append_failed_primary_list(self, peer_id):
        lock.acquire()

        if peer_id is not None and peer_id not in self._failed_primary_list:
            self._failed_primary_list.append(peer_id)

        lock.release()

    def clear_failed_primary_list(self):
        lock.acquire()
        self._failed_primary_list.clear()
        lock.release()

    def is_peer_in_failed_primary_list(self, peer_id):
        lock.acquire()
        result = peer_id in self._failed_primary_list
        lock.release()
        return result

    def get_children_count(self):
        count = 0
        lock.acquire()

        for connection in self._peers.values():
            if connection.is_primary and not connection.is_parent:
                count = count + 1

        lock.release()
        return count

    # def is_leaf(self):
    #     result = False
    #     lock.acquire()
    #
    #     if len(self._primary_list) == 0:
    #
    #
    #     lock.release()
    #     return result

    def get_in_candidate_remove_peer_id(self, target_peer_id, target_ticket_id):
        remove_peer_id = None
        lock.acquire()

        if self.max_in_candidate <= len(
                self._in_coming_candidate_list) and target_peer_id not in self._in_coming_candidate_list:
            max_ticket_id = 0
            for peer_id in self._in_coming_candidate_list:
                connection: PeerConnection = self._peers[peer_id]
                if connection.ticket_id > target_ticket_id:
                    max_ticket_id = max(max_ticket_id, connection.ticket_id)
                    if max_ticket_id == connection.ticket_id:
                        remove_peer_id = connection.peer_id

        if remove_peer_id is not None:
            self._in_coming_candidate_list.remove(remove_peer_id)
            self._in_coming_candidate_list.append(target_peer_id)

        lock.release()
        return remove_peer_id

    def set_estab_peers_probe_time(self, peer_id, probe_time):
        lock.acquire()
        if peer_id in self._estab_peers.keys():
            self._estab_peers[peer_id] = probe_time
        lock.release()

    def get_estab_peers(self):
        lock.acquire()
        _estab_peers = self._estab_peers.copy()
        lock.release()
        return _estab_peers

    def clear_estab_peers(self):
        lock.acquire()
        self._estab_peers.clear()
        lock.release()

    def delete_establish_peer(self, peer_id):
        lock.acquire()

        if peer_id in self._estab_peers.keys():
            del self._estab_peers[peer_id]

        lock.release()

    def establish_peer(self, peer_id):
        result = False
        lock.acquire()

        if self.max_out_candidate - len(
                self._out_going_candidate_list) > 0 and peer_id not in self._out_going_candidate_list:
            self._out_going_candidate_list.append(peer_id)
            self._estab_peers[peer_id] = None
            result = True

        lock.release()
        return result

    def un_establish_peer(self, peer_id):
        lock.acquire()
        self._out_going_candidate_list.remove(peer_id)
        lock.release()

    def assignment_peer(self, peer_id):
        result = False
        lock.acquire()

        if self.max_in_candidate - len(
                self._in_coming_candidate_list) > 0 and peer_id not in self._in_coming_candidate_list:
            self._in_coming_candidate_list.append(peer_id)
            result = True

        lock.release()
        return result

    def un_assignment_peer(self, peer_id):
        lock.acquire()
        self._in_coming_candidate_list.remove(peer_id)
        lock.release()

    def set_primary_peer(self, peer_id, is_out_going):
        result = False
        lock.acquire()

        if peer_id in self._peers and self.max_primary_connection - len(self._primary_list) > 0:
            if is_out_going and peer_id in self._out_going_candidate_list:
                self._out_going_candidate_list.remove(peer_id)
                result = True
            elif not is_out_going and peer_id in self._in_coming_candidate_list:
                self._in_coming_candidate_list.remove(peer_id)
                result = True

            if result:
                connection: PeerConnection = self._peers[peer_id]
                connection.is_primary = True
                self._primary_list.append(peer_id)
                print('SET_PRIMARY_PEER', peer_id)
                print('     ', self._primary_list)

        lock.release()
        return result

    def add_peer(self, peer_id, ticket_id, is_primary, is_parent, connection, address=None):
        result = False
        lock.acquire()

        if peer_id not in self._peers and peer_id in self._in_coming_candidate_list or peer_id in self._out_going_candidate_list:
            print('\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ADD PEER', peer_id)
            self._peers[peer_id] = PeerConnection(peer_id, ticket_id, is_primary, is_parent, connection, address)
            result = True

        lock.release()
        return result

    def remove_peer(self, peer_id):
        result = False
        lock.acquire()

        if peer_id in self._peers:
            del self._peers[peer_id]
            result = True

        lock.release()
        return result

    def clear_peer(self, peer_id):
        print('\n$$$$CLEAR PEER', peer_id)
        lock.acquire()

        if peer_id in self._peers:
            del self._peers[peer_id]

        if peer_id in self._primary_list:
            self._primary_list.remove(peer_id)

        if peer_id in self._in_coming_candidate_list:
            self._in_coming_candidate_list.remove(peer_id)

        if peer_id in self._out_going_candidate_list:
            self._out_going_candidate_list.remove(peer_id)

        lock.release()

    def get_peer_connection(self, peer_id):
        get_connection = None
        lock.acquire()

        if peer_id in self._peers:
            get_connection = self._peers[peer_id]

        lock.release()
        return get_connection

    def get_all_peer_connection(self):
        lock.acquire()
        _peers = self._peers.copy()
        lock.release()
        return _peers

    @abstractmethod
    def get_peer_id_by_connection(self, connection):
        pass

    @abstractmethod
    def send_message(self, message):
        pass

    @abstractmethod
    def send_message_to_peer(self, message, peer_id):
        pass

    @abstractmethod
    def broadcast_message(self, sender, message):
        pass

    @abstractmethod
    def broadcast_message_to_children(self, message):
        pass

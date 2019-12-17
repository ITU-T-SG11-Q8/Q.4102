from rtc.rtcdatapeer import RTCDataPeer
from pyee import EventEmitter
from config import PEER_CONFIG
import threading

lock = threading.Lock()


class RTCDataPeerCollection(EventEmitter):
    def __init__(self, _id):
        super().__init__()
        self.__id = _id
        self.__ticket_id = None

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

    @property
    def id(self):
        return self.__id

    @property
    def ticket_id(self):
        return self.__ticket_id

    def set_ticket_id(self, ticket_id):
        self.__ticket_id = ticket_id

    def __on_message(self, sender, msg):
        # print(sender.connectedId + ' : ' + msg)
        self.emit('message', sender, msg)

    def __on_connection(self, sender):
        self.emit('connection', sender)

    async def close(self):
        lock.acquire()
        for key in self._peers:
            peer = self._peers[key]
            await peer.close()
        self._peers.clear()
        lock.release()

    # def getPeer(self, toid):
    #     pc = None
    #
    #     if toid is not None and toid in self._peers:
    #         pc = self._peers[toid]
    #
    #     return pc

    #################################################
    #####################################
    def is_none_connection(self):
        lock.acquire()
        result = len(self._peers) == 0 and len(self._primary_list) == 0 and len(
            self._out_going_candidate_list) == 0 and len(self._in_coming_candidate_list) == 0
        lock.release()
        return result

    def get_in_coming_candidate_list(self):
        lock.acquire()
        _in_coming_candidate_list = self._in_coming_candidate_list.copy()
        lock.release()
        return _in_coming_candidate_list

    def is_in_in_coming_candidate_list(self, peer_id):
        lock.acquire()
        result = peer_id in self._in_coming_candidate_list
        lock.release()
        return result

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
        lock.acquire()
        count = 0

        for connection in self._peers.values():
            if connection.is_primary and not connection.is_parent:
                count = count + 1

        lock.release()
        return count

    def is_leaf(self, sender):
        lock.acquire()
        result = sender in self._primary_list and len(self._primary_list) == 1
        lock.release()
        return result

    def get_in_candidate_remove_peer_id(self, target_peer_id, target_ticket_id):
        lock.acquire()
        remove_peer_id = None

        if self.max_in_candidate <= len(
                self._in_coming_candidate_list) and target_peer_id not in self._in_coming_candidate_list:
            max_ticket_id = 0
            for peer_id in self._in_coming_candidate_list:
                connection = self._peers[peer_id]
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
        estab_peers = self._estab_peers.copy()
        lock.release()
        return estab_peers

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
        lock.acquire()
        result = False

        if self.max_out_candidate - len(
                self._out_going_candidate_list) > 0 and peer_id not in self._out_going_candidate_list:
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! MANAGED PEER', peer_id)
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
        lock.acquire()
        result = False

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

    def has_parent_primary(self):
        lock.acquire()
        result = False

        for peer_id in self._primary_list:
            connection = self._peers[peer_id]
            if connection.is_primary and connection.is_parent:
                result = True
                break

        lock.release()
        return result

    def set_primary_peer(self, peer_id, is_out_going):
        lock.acquire()
        result = False

        if peer_id in self._peers and self.max_primary_connection - len(self._primary_list) > 0:
            if is_out_going and peer_id in self._out_going_candidate_list:
                self._out_going_candidate_list.remove(peer_id)
                result = True
            elif not is_out_going and peer_id in self._in_coming_candidate_list:
                self._in_coming_candidate_list.remove(peer_id)
                result = True

            if result:
                connection = self._peers[peer_id]
                connection.is_primary = True
                self._primary_list.append(peer_id)
                print('SET_PRIMARY_PEER', peer_id)
                print('     ', self._primary_list)

        lock.release()
        return result

    async def add_peer(self, peer_id, ticket_id, is_primary, is_parent):
        lock.acquire()
        rtc_peer = None

        if peer_id in self._peers:
            rtc_peer = self._peers[peer_id]
        else:
            rtc_peer = RTCDataPeer(self.id, self.ticket_id, peer_id, ticket_id, is_primary, is_parent)
            rtc_peer.on('message', self.__on_message)
            rtc_peer.on('connection', self.__on_connection)

            if peer_id in self._primary_list or peer_id in self._in_coming_candidate_list or peer_id in self._out_going_candidate_list:
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ADD PEER', peer_id)
                self._peers[peer_id] = rtc_peer
            else:
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! UNMANAGED ADD PEER', peer_id)
                self._peers[peer_id] = rtc_peer
                # is_established = self.establish_peer(peer_id)
                # if is_established:
                #     if peer_id in self.out_candidate_list:
                #         lock.acquire()
                #         print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ADD PEER', peer_id)
                #         self._peers[peer_id] = pc
                #         lock.release()
                # else:
                #     print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! unmanaged  PEER', peer_id)

        lock.release()
        return rtc_peer

    def delete_peer(self, peer_id):
        lock.acquire()
        result = False

        if peer_id not in self._peers:
            del self._peers[peer_id]
            result = True

        lock.release()
        return result

    async def remove_peer(self, toid):
        if toid is None:
            return None

        if toid in self._peers:
            pc = self._peers[toid]
            await pc.close()
            # del self._peers[toid]
            self.clear_peer(toid)
            print('disconnected from ' + toid)
            # print('now connected to ', end='')
            # for key in self._peers:
            #     print(key, end=',')
            # print('')

    def clear_peer(self, peer_id):
        lock.acquire()
        print('$$$$CLEAR PEER', peer_id)

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
        lock.acquire()
        get_connection = None

        if peer_id in self._peers:
            get_connection = self._peers[peer_id]

        lock.release()
        return get_connection

    def get_all_peer_connection(self):
        lock.acquire()
        _peers = self._peers.copy()
        lock.release()
        return _peers

    ####################################################
    ############################################
    async def set_signal_message(self, msg):
        pc = None

        if msg.fromid in self._peers:
            pc = self._peers[msg.fromid]
        else:
            # incoming
            pc = await self.add_peer(msg.fromid, msg.fromticketid, False, True)

        return await pc.setSignalMessage(msg)

    async def send_message(self, toid, msg):
        for key in self._peers:
            peer = self._peers[key]
            if toid == peer.connectedId:
                peer.sendMessage(msg)
                break
            # if toid is None or toid == peer.connectedId:
            #     peer.sendMessage(msg)

    # async def sendMessageOther(self, fromid, msg):
    #     for key in self._peers:
    #         peer = self._peers[key]
    #         if fromid is None or fromid != peer.connectedId:
    #             peer.sendMessage(msg)

    async def broadcast_message(self, msg):
        for key in self._peers:
            peer = self._peers[key]
            if peer.is_primary:
                peer.sendMessage(msg)

    async def broadcast_message_other(self, sender_id, msg):
        for key in self._peers:
            peer = self._peers[key]
            if peer.connectedId != sender_id and peer.is_primary:
                peer.sendMessage(msg)

    async def broadcast_message_to_children(self, msg):
        for key in self._peers:
            peer = self._peers[key]
            if peer.is_primary and not peer.is_parent:
                peer.sendMessage(msg)

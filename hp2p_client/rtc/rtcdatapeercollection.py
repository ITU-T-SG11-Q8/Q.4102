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
        self.__peerList = {}

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
        for key in self.__peerList:
            peer = self.__peerList[key]
            await peer.close()
        self.__peerList.clear()

    async def removePeer(self, toid):
        if toid is None:
            return None

        if toid in self.__peerList:
            pc = self.__peerList[toid]
            await pc.close()
            del self.__peerList[toid]
            print('disconnected from ' + toid)
            print('now connected to ', end='')
            for key in self.__peerList:
                print(key, end=',')
            print('')

    def getPeer(self, toid):
        pc = None

        if toid is not None and toid in self.__peerList:
            pc = self.__peerList[toid]

        return pc

    def get_children_count(self):
        count = 0
        for connection in self.__peerList.values():
            if connection.is_primary and not connection.is_parent:
                count = count + 1
        return count

    def get_in_candidate_remove_peer_id(self, target_peer_id, target_ticket_id):
        remove_peer_id = None
        lock.acquire()
        if self.max_in_candidate <= len(self.in_candidate_list) and target_peer_id not in self.in_candidate_list:
            max_ticket_id = 0
            for peer_id in self.in_candidate_list:
                connection = self.__peerList[peer_id]
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
            if peer_id in self.__peerList:
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! MANAGED PEER', peer_id)
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

        if peer_id not in self.__peerList:
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
                connection = self.__peerList[peer_id]
                connection.is_primary = True
                self.primary_list.append(peer_id)
                print('SET_PRIMARY_PEER', peer_id)
                print('     ', self.primary_list)
        lock.release()

        return result

    def add_peer(self, peer_id, ticket_id, is_primary, is_parent):
        if peer_id in self.__peerList:
            return None
        pc = None

        if peer_id in self.__peerList:
            pc = self.__peerList[peer_id]
        else:
            pc = RTCDataPeer(self.id, self.ticket_id, peer_id, ticket_id, is_primary, is_parent)
            pc.on('message', self.__on_message)
            pc.on('connection', self.__on_connection)

            if peer_id in self.in_candidate_list or peer_id in self.out_candidate_list:
                lock.acquire()
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ADD PEER', peer_id)
                self.__peerList[peer_id] = pc
                lock.release()
            else:
                lock.acquire()
                print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! UNMANAGED ADD PEER', peer_id)
                self.__peerList[peer_id] = pc
                lock.release()
                # is_established = self.establish_peer(peer_id)
                # if is_established:
                #     if peer_id in self.out_candidate_list:
                #         lock.acquire()
                #         print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!ADD PEER', peer_id)
                #         self.__peerList[peer_id] = pc
                #         lock.release()
                # else:
                #     print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! unmanaged  PEER', peer_id)

        return pc

    def remove_peer(self, peer_id):
        if peer_id not in self.__peerList:
            return False

        lock.acquire()
        del self.__peerList[peer_id]
        lock.release()

        return True

    def clear_peer(self, peer_id):
        print('$$$$CLEAR PEER', peer_id)
        lock.acquire()

        if peer_id in self.__peerList:
            del self.__peerList[peer_id]

        if peer_id in self.primary_list:
            self.primary_list.remove(peer_id)

        if peer_id in self.in_candidate_list:
            self.in_candidate_list.remove(peer_id)

        if peer_id in self.out_candidate_list:
            self.out_candidate_list.remove(peer_id)

        lock.release()

    def get_peer_connection(self, peer_id):
        if peer_id in self.__peerList:
            return self.__peerList[peer_id]
        return None

    def get_all_peer_connection(self):
        return self.__peerList

    async def setSignalMessage(self, msg):
        pc = None

        if msg.fromid in self.__peerList:
            pc = self.__peerList[msg.fromid]
        else:
            # outgoing
            pc = self.add_peer(msg.fromid, msg.fromticketid, False, False)

        return await pc.setSignalMessage(msg)

    async def sendMessage(self, toid, msg):
        for key in self.__peerList:
            peer = self.__peerList[key]
            if toid == peer.connectedId:
                peer.sendMessage(msg)
                break
            # if toid is None or toid == peer.connectedId:
            #     peer.sendMessage(msg)

    async def broadcast_message(self, msg):
        for key in self.__peerList:
            peer = self.__peerList[key]
            if peer.is_primary:
                peer.sendMessage(msg)

    async def broadcast_message_other(self, sender_id, msg):
        for key in self.__peerList:
            peer = self.__peerList[key]
            if peer.connectedId != sender_id and peer.is_primary:
                peer.sendMessage(msg)

    async def broadcast_message_to_children(self, msg):
        for key in self.__peerList:
            peer = self.__peerList[key]
            if peer.is_primary and not peer.is_parent:
                peer.sendMessage(msg)

    async def sendMessageOther(self, fromid, msg):
        for key in self.__peerList:
            peer = self.__peerList[key]
            if fromid is None or fromid != peer.connectedId:
                peer.sendMessage(msg)

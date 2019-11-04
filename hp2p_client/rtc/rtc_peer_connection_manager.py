# from classes.peer_connection_manager import PeerConnectionManager, PeerConnection
# from rtc.rtcdatapeer import RTCDataPeer
# from pyee import EventEmitter
#
#
# class RtcPeerConnectionManager(PeerConnectionManager, EventEmitter):
#     def __init__(self, _id, _max):
#         PeerConnectionManager.__init__(self)
#         EventEmitter.__init__(self)
#         self.__id = _id
#         self.__max = _max
#         self.__peerList = {}
#
#     @property
#     def id(self):
#         return self.__id
#
#     @property
#     def max(self):
#         return self.__max
#
#     async def close(self):
#         for key in self.__peerList:
#             peer = self.__peerList[key]
#             await peer.close()
#         self.__peerList.clear()
#
#     def __on_message(self, sender, msg):
#         # print(sender.connectedId + ' : ' + msg)
#         self.emit('message', sender, msg)
#
#     def __on_connection(self, sender):
#         self.emit('connection', sender)
#
#     def addPeer(self, toid):
#         if toid is None:
#             return None
#
#         pc = None
#
#         if toid in self.__peerList:
#             pc = self.__peerList[toid]
#         else:
#             pc = RTCDataPeer(self.__id, toid)
#             self.__peerList[toid] = pc
#             pc.on('message', self.__on_message)
#             pc.on('connection', self.__on_connection)
#
#         return pc
#
#     async def removePeer(self, toid):
#         if toid is None:
#             return None
#
#         if toid in self.__peerList:
#             pc = self.__peerList[toid]
#             await pc.close()
#             del self.__peerList[toid]
#             print('disconnected from ' + toid)
#             print('now connected to ', end='')
#             for key in self.__peerList:
#                 print(key, end=',')
#             print('')
#
#     def getPeer(self, toid):
#         pc = None
#
#         if toid is not None and toid in self.__peerList:
#             pc = self.__peerList[toid];
#
#         return pc
#
#     async def setSignalMessage(self, msg):
#         pc = None
#
#         if msg.fromid in self.__peerList:
#             pc = self.__peerList[msg.fromid]
#         else:
#             pc = self.addPeer(msg.fromid)
#
#         return await pc.setSignalMessage(msg)
#
#     async def sendMessage(self, toid, msg):
#         for key in self.__peerList:
#             peer = self.__peerList[key]
#             if toid is None or toid == peer.connectedId:
#                 peer.sendMessage(msg)
#
#     async def sendMessageOther(self, fromid, msg):
#         for key in self.__peerList:
#             peer = self.__peerList[key]
#             if fromid is None or fromid != peer.connectedId:
#                 peer.sendMessage(msg)
#
#     def get_peer_id_by_connection(self, connection):
#         pass
#
#     def send_message(self, message):
#         pass
#
#     def broadcast_message(self, sender, message):
#         pass
#
#     def broadcast_message_to_children(self, message):
#         pass

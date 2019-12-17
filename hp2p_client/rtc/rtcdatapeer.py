from pyee import EventEmitter
from aiortc import RTCPeerConnection
from rtc.rtcsessiondescriptionex import RTCSessionDescriptionEx
from datetime import datetime


class RTCDataPeer(EventEmitter):
    def __init__(self, _id, from_ticket_id, to_id, ticket_id, is_primary, is_parent):
        super().__init__()
        self.__id = _id
        self.__from_ticket_id = from_ticket_id
        self.__connectedId = to_id
        self.__isDataChannelOpened = False
        self.__is_outgoing = False

        self.ticket_id = ticket_id
        self.is_primary = is_primary
        self.is_parent = is_parent
        self.priority = None
        self.update_time = datetime.now()

        self.__peerConnection = RTCPeerConnection()
        self.__dataChannel = None
        self.__peerConnection.on('datachannel', self.__on_dataChannel)

        @self.__peerConnection.on('iceconnectionstatechange')
        def on_iceconnectionstatechange():
            print('iceconnectionstatechange : ' + self.__peerConnection.iceConnectionState)
            if self.__peerConnection.iceConnectionState == 'failed':
                print(self.__connectedId + ' disconnected!!!!')
                self.__isDataChannelOpened = False
                self.__handle_connection()

        @self.__peerConnection.on('track')
        def on_track(track):
            print('track : ' + track)

        @self.__peerConnection.on('signalingstatechange')
        def on_signalingstatechange():
            print('signalingstatechange : ' + self.__peerConnection.signalingState)

        @self.__peerConnection.on('icegatheringstatechange')
        def on_icegatheringstatechange():
            print('icegatheringstatechange : ' + self.__peerConnection.iceGatheringState)

    @property
    def id(self):
        return self.__id

    @property
    def connectedId(self):
        return self.__connectedId

    @property
    def isDataChannelOpened(self):
        return self.__isDataChannelOpened

    @property
    def is_outgoing(self):
        return self.__is_outgoing

    @property
    def from_ticket_id(self):
        return self.__from_ticket_id

    def update_status(self, is_outgoing, ticket_id=None):
        self.__is_outgoing = is_outgoing
        self.is_parent = is_outgoing
        if ticket_id is not None:
            self.ticket_id = ticket_id
        print('[Connection Update] => {0}'.format(self.to_information()))

    def to_print(self):
        print(self.to_information())

    def to_information(self):
        return "ID:{0}, Ticket ID:{1}, Outgoing:{2}, Primary:{3}, Is Parent:{4}".format(
            self.connectedId, self.ticket_id, self.is_outgoing, self.is_primary, self.is_parent)

    def __handle_data(self, msg):
        # print(self.__connectedId + ' : ' + msg)
        # while (self.__dataChannel.bufferedAmount <= self.__dataChannel.bufferedAmountLowThreshold):
        #    self.__dataChannel.send(name)
        self.emit('message', self, msg)

    def __handle_connection(self):
        # print(self.__connectedId + ' : ' + msg)
        # while (self.__dataChannel.bufferedAmount <= self.__dataChannel.bufferedAmountLowThreshold):
        #    self.__dataChannel.send(name)
        self.emit('connection', self)

    def __setEventDataChannel(self):
        @self.__dataChannel.on('open')
        def on_open():
            print('DataChannel opened with ' + self.__connectedId)
            self.__isDataChannelOpened = True
            self.__handle_connection()

        @self.__dataChannel.on('ended')
        def on_ended():
            print('DataChannel ended with ' + self.__connectedId)
            self.__isDataChannelOpened = False
            self.__handle_connection()

        self.__dataChannel.on('message', self.__handle_data)

        # self.__dataChannel.on('bufferedamountlow', self.__handle_data)

    def __on_dataChannel(self, channel):
        self.__dataChannel = channel
        self.__setEventDataChannel()
        print('DataChannel opened with ' + self.__connectedId)
        self.__isDataChannelOpened = True
        self.__is_outgoing = True
        self.__handle_connection()

    def createDataChannel(self, channelName='datachannel'):
        self.__dataChannel = self.__peerConnection.createDataChannel(channelName)
        self.__setEventDataChannel()

    async def getSDP(self):
        await self.__peerConnection.setLocalDescription(await self.__peerConnection.createOffer())

        rsde = RTCSessionDescriptionEx.copy(self.__peerConnection.localDescription)
        rsde.fromid = self.__id
        rsde.toid = self.__connectedId
        rsde.fromticketid = self.__from_ticket_id

        return rsde

    async def setSignalMessage(self, msg):

        await self.__peerConnection.setRemoteDescription(msg)

        if msg.type == 'offer':
            await self.__peerConnection.setLocalDescription(await self.__peerConnection.createAnswer())
            rsde = RTCSessionDescriptionEx.copy(self.__peerConnection.localDescription)
            rsde.fromid = self.__id
            rsde.toid = msg.fromid
            rsde.fromticketid = self.__from_ticket_id
            return rsde

    def sendMessage(self, msg):
        if self.isDataChannelOpened:
            self.__dataChannel.send(msg)

    async def close(self):
        if self.__dataChannel is not None:
            self.__dataChannel.close()
            await self.__peerConnection.close()
            self.__isDataChannelOpened = False
            self.__handle_connection()

from pyee import EventEmitter
from aiortc import RTCPeerConnection
from rtc.rtcsessiondescriptionex import RTCSessionDescriptionEx


class RTCDataPeer(EventEmitter):
    def __init__(self, id, toId):
        super().__init__()
        self.__id = id
        self.__connectedId = toId
        self.__isDataChannelOpened = False
        self.__peerConnection = RTCPeerConnection()
        self.__dataChannel = None
        self.__peerConnection.on('datachannel', self.__on_dataChannel)

        @self.__peerConnection.on('iceconnectionstatechange')
        def on_iceconnectionstatechange():
            print('iceconnectionstatechange : ' + self.__peerConnection.iceConnectionState)
            if self.__peerConnection.iceConnectionState == 'failed':
                print(self.__connectedId + ' disconnected!!!!')
                self.__isDataChannelOpened = False

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

    def __handle_data(self, msg):
        # print(self.__connectedId + ' : ' + msg)
        # while (self.__dataChannel.bufferedAmount <= self.__dataChannel.bufferedAmountLowThreshold):
        #    self.__dataChannel.send(name)
        self.emit('message', self, msg)

    def __setEventDataChannel(self):
        @self.__dataChannel.on('open')
        def on_open():
            print('DataChannel opened with ' + self.__connectedId)
            self.__isDataChannelOpened = True

        @self.__dataChannel.on('ended')
        def on_ended():
            print('DataChannel ended with ' + self.__connectedId)
            self.__isDataChannelOpened = False

        self.__dataChannel.on('message', self.__handle_data)

        # self.__dataChannel.on('bufferedamountlow', self.__handle_data)

    def __on_dataChannel(self, channel):
        self.__dataChannel = channel
        self.__setEventDataChannel()
        print('DataChannel opened with ' + self.__connectedId)
        self.__isDataChannelOpened = True

    def createDataChannel(self, channelName='datachannel'):
        self.__dataChannel = self.__peerConnection.createDataChannel(channelName)
        self.__setEventDataChannel()

    async def getSDP(self):
        await self.__peerConnection.setLocalDescription(await self.__peerConnection.createOffer())

        rsde = RTCSessionDescriptionEx.copy(self.__peerConnection.localDescription)
        rsde.fromid = self.__id
        rsde.toid = self.__connectedId

        return rsde

    async def setSignalMessage(self, msg):

        await self.__peerConnection.setRemoteDescription(msg)

        if msg.type == 'offer':
            await self.__peerConnection.setLocalDescription(await self.__peerConnection.createAnswer())
            rsde = RTCSessionDescriptionEx.copy(self.__peerConnection.localDescription)
            rsde.fromid = self.__id
            rsde.toid = msg.fromid
            return rsde

    def sendMessage(self, msg):
        if self.isDataChannelOpened:
            self.__dataChannel.send(msg)

    async def close(self):
        if self.__dataChannel is not None:
            self.__dataChannel.close()
            await self.__peerConnection.close()

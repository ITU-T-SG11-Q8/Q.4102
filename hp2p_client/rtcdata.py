from pyee import EventEmitter
import asyncio
import os
os.environ['AIORTC_SPECIAL_MODE'] = 'DC_ONLY'

from rtcdatapeercollection import RTCDataPeerCollection
from rtcsessiondescriptionex import RTCSessionDescriptionEx
from aiortc import RTCPeerConnection, RTCSessionDescription
from signalingex import create_ws_signaling
import threading



class RTCData(EventEmitter):
    def __init__(self, id, max_peer):
        super().__init__()
        self.__id = id
        self.__max_peer = max_peer
        self.__signaling_host = None
        self.__signaling_port = None
        self.__signaling = None
        self.__signaling_thread = None
        self.__rtcPeerCollection = RTCDataPeerCollection(id, max)
        self.__rtcPeerCollection.on('message', self.__on_message)
        self.__close = False
        self.__event_loop = asyncio.new_event_loop()
        self.__event_loop_thread = threading.Thread(target=self.__event_thread_main, daemon=True)
        self.__event_loop_thread.start()

    @property
    def id(self):
        return self.__id

    @property
    def max(self):
        return self.__max

    async def __on_message(self, sender, msg):
        #self.__wait_async(self.__rtcPeerCollection.sendMessageOther(sender.connectedId, msg))
        if msg == 'bye':
            await self.__disconnect_to_peer(sender.connectedId)
        else:
            await self.__rtcPeerCollection.sendMessageOther(sender.connectedId, msg)

    def __event_thread_main(self):
        asyncio.set_event_loop(self.__event_loop)
        
        try:
            self.__event_loop.run_forever()
        finally:
            self.__event_loop.run_until_complete(self.__event_loop.shutdown_asyncgens())
            self.__event_loop.close()

    def __wait_async(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.__event_loop)
        return future.result()

    async def __connect_signal_server(self):
        self.__signaling = create_ws_signaling(self.__signaling_host, self.__signaling_port)
        await self.__signaling.connect()

    def connect_signal_server(self, signaling_host, signaling_port):
        self.__signaling_host = signaling_host
        self.__signaling_port = signaling_port
        #evloop = asyncio.new_event_loop()
        #evloop.run_until_complete(self.__connect_signal_server())
        #evloop.close()
        self.__wait_async(self.__connect_signal_server())
        asyncio.run_coroutine_threadsafe(self.__consume_signaling(), self.__event_loop)

    async def __consume_signaling(self):
        
        while not self.__close:
            obj = await self.__signaling.receive()
            if isinstance(obj, RTCSessionDescriptionEx):
                if obj.toid == self.__id:
                    print("recv sdp " + obj.type + " from " + obj.fromid)

                    answer = await self.__rtcPeerCollection.setSignalMessage(obj)

                    #answer = self.__wait_async(self.__rtcPeerCollection.setSignalMessage(obj))

                    #future = asyncio.run_coroutine_threadsafe(self.__rtcPeerCollection.setSignalMessage(obj), self.__event_loop)
                    #answer = future.result()

                    if isinstance(answer, RTCSessionDescriptionEx):
                        await self.__signaling.send(answer)
            else:
                print('unknown signaling')

    #def __signaling_thread_main(self, evloop):
        #loop = asyncio.new_event_loop()
        #asyncio.set_event_loop(loop)
        #loop.run_until_complete(self.__connect_signal_server())
        #loop.run_until_complete(self.__consume_signaling())
        #loop.close()

        #asyncio.set_event_loop(self.__event_loop)
        #self.__event_loop.run_until_complete(self.__connect_signal_server())
        #self.__event_loop.run_until_complete(self.__consume_signaling())

    #def start_rtc(self):
        #evloop = asyncio.new_event_loop()
        #self.__signaling_thread = threading.Thread(target=self.__signaling_thread_main, args=(self.__event_loop,), daemon=True)
        #self.__signaling_thread.start()
        #asyncio.ensure_future(self.__consume_signaling())
        #self.__event_loop.run_until_complete(self.__consume_signaling())

    async def __connect_to_peer(self, toid):
        pc = self.__rtcPeerCollection.addPeer(toid)
        pc.createDataChannel()
        rsde = await pc.getSDP()
        await self.__signaling.send(rsde)

    async def __disconnect_to_peer(self, toid):
        await self.__rtcPeerCollection.removePeer(toid)

    def connect_to_peer(self, toid):
        self.__wait_async(self.__connect_to_peer(toid))

    def disconnect_to_peer(self, toid):
        self.__wait_async(self.__disconnect_to_peer(toid))        

    def send(self, msg):
        self.__wait_async(self.__rtcPeerCollection.sendMessage(None, msg))

    def close(self):
        self.__close = True
        self.__wait_async(self.__signaling.close())
        self.__wait_async(self.__rtcPeerCollection.close())
        self.__event_loop.stop()
        
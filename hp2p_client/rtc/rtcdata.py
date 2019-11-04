from pyee import EventEmitter
import asyncio
import os
import threading

os.environ['AIORTC_SPECIAL_MODE'] = 'DC_ONLY'

from rtc.rtcdatapeercollection import RTCDataPeerCollection
from rtc.rtcsessiondescriptionex import RTCSessionDescriptionEx
from rtc.signalingex import create_ws_signaling
from data.factory import Factory
from classes.constants import MessageType


# from rtc.rtc_peer_connection_manager import RtcPeerConnectionManager


class RTCData(EventEmitter):
    def __init__(self, peer_id):
        super().__init__()
        self.__peer_id = peer_id
        self.__ticket_id = None
        self.__signaling_host = None
        self.__signaling_port = None
        self.__signaling = None
        self.__signaling_thread = None
        self.__rtcPeerCollection = RTCDataPeerCollection(peer_id)
        # self.__rtcPeerCollection = RtcPeerConnectionManager(peer_id, max_peer)
        self.__rtcPeerCollection.on('message', self.__on_message)
        self.__rtcPeerCollection.on('connection', self.__on_connection)
        self.__callback_event_emitter = None
        self.__close = False
        self.__event_loop = asyncio.new_event_loop()
        self.__event_loop_thread = threading.Thread(target=self.__event_thread_main, daemon=True)
        self.__event_loop_thread.start()

    @property
    def id(self):
        return self.__peer_id

    @property
    def ticket_id(self):
        return self.__ticket_id

    def set_ticket_id(self, ticket_id):
        self.__ticket_id = ticket_id
        self.__rtcPeerCollection.set_ticket_id(ticket_id)

    def get_collection(self):
        return self.__rtcPeerCollection

    def set_callback_event_emitter(self, callback_event_emitter):
        self.__callback_event_emitter = callback_event_emitter

    def __on_connection(self, sender):
        self.emit('connection', sender)

    async def __on_message(self, sender, msg):
        # self.__wait_async(self.__rtcPeerCollection.sendMessageOther(sender.connectedId, msg))
        self.emit('message', sender, msg)
        # if msg == 'bye':
        #     await self.__disconnect_to_peer(sender.connectedId)
        # else:
        #     await self.__rtcPeerCollection.sendMessageOther(sender.connectedId, msg)

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
        # evloop = asyncio.new_event_loop()
        # evloop.run_until_complete(self.__connect_signal_server())
        # evloop.close()
        self.__wait_async(self.__connect_signal_server())
        asyncio.run_coroutine_threadsafe(self.__consume_signaling(), self.__event_loop)

    async def __consume_signaling(self):

        while not self.__close:
            obj = await self.__signaling.receive()
            if isinstance(obj, RTCSessionDescriptionEx):
                if obj.toid == self.__peer_id:
                    print("recv sdp " + obj.type + " from " + obj.fromid)

                    answer = await self.__rtcPeerCollection.setSignalMessage(obj)
                    if isinstance(answer, RTCSessionDescriptionEx):
                        await self.__signaling.send(answer)

                    # answer = self.__wait_async(self.__rtcPeerCollection.setSignalMessage(obj))

                    # future = asyncio.run_coroutine_threadsafe(
                    #   self.__rtcPeerCollection.setSignalMessage(obj), self.__event_loop)
                    # answer = future.result()
            elif 'action' in obj:
                self.message_handler(obj)
                # self.__callback_event_emitter.emit('receive_message', obj)
            else:
                print('unknown signaling')

    # def __signaling_thread_main(self, evloop):
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(self.__connect_signal_server())
    # loop.run_until_complete(self.__consume_signaling())
    # loop.close()

    # asyncio.set_event_loop(self.__event_loop)
    # self.__event_loop.run_until_complete(self.__connect_signal_server())
    # self.__event_loop.run_until_complete(self.__consume_signaling())

    # def start_rtc(self):
    # evloop = asyncio.new_event_loop()
    # self.__signaling_thread = threading.Thread(target=self.__signaling_thread_main,
    #       args=(self.__event_loop,), daemon=True)
    # self.__signaling_thread.start()
    # asyncio.ensure_future(self.__consume_signaling())
    # self.__event_loop.run_until_complete(self.__consume_signaling())

    def message_handler(self, message):
        print('\nWebSocket message_handler...')
        if message.get('to_peer_id') != self.id:
            return

        if message.get('action') == 'failed_hello_peer':
            print('received... failed_hello_peer', message)
            rtc_hp2p_client = Factory.instance().get_rtc_hp2p_client()
            rtc_hp2p_client.run_send_hello_peer()

        elif message.get('action') == 'hello_peer':
            received_message = message.get('message')
            rtc_hp2p_client = Factory.instance().get_rtc_hp2p_client()

            if 'ReqCode' in received_message:
                req_code = received_message.get('ReqCode')
                if req_code == MessageType.REQUEST_HELLO_PEER:
                    rtc_hp2p_client.received_hello_peer(received_message)

            elif 'RspCode' in received_message:
                rsp_code = received_message.get('RspCode')
                if rsp_code == MessageType.RESPONSE_HELLO_PEER:
                    rtc_hp2p_client.received_response_hello_peer(True)

    def send_to_server(self, message):
        self.__wait_async(self.__signaling.send(message))

    async def __connect_to_peer(self, toid, ticket_id):
        # incoming
        pc = self.__rtcPeerCollection.add_peer(toid, ticket_id, False, True)
        pc.createDataChannel()
        rsde = await pc.getSDP()
        await self.__signaling.send(rsde)

    async def __disconnect_to_peer(self, toid):
        await self.__rtcPeerCollection.removePeer(toid)

    def connect_to_peer(self, toid, ticket_id):
        self.__wait_async(self.__connect_to_peer(toid, ticket_id))

    def disconnect_to_peer(self, toid):
        self.__wait_async(self.__disconnect_to_peer(toid))

    def send(self, to_peer_id, msg):
        self.__wait_async(self.__rtcPeerCollection.sendMessage(to_peer_id, msg))

    def send_broadcast_message(self, msg):
        self.__wait_async(self.__rtcPeerCollection.broadcast_message(msg))

    def send_broadcast_message_other(self, sender_id, msg):
        self.__wait_async(self.__rtcPeerCollection.broadcast_message_other(sender_id, msg))

    def send_broadcast_message_to_children(self, msg):
        self.__wait_async(self.__rtcPeerCollection.broadcast_message_to_children(msg))

    def close(self):
        self.__close = True
        self.__wait_async(self.__signaling.close())
        self.__wait_async(self.__rtcPeerCollection.close())
        self.__event_loop.stop()

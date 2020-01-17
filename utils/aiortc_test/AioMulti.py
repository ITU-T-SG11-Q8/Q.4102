import argparse
import asyncio
import logging
import time
import sys
import os
import threading

os.environ['AIORTC_SPECIAL_MODE'] = 'DC_ONLY'

from aiortc import RTCPeerConnection, RTCSessionDescription
from signalingex import create_ws_signaling

from rtcsessiondescriptionex import RTCSessionDescriptionEx

pclist = {}

async def newdc(rdse, signaling, name):
    global pclist

    print("recv rdse ", rdse.type)
    print("recv rdse ", rdse.fromid)

    pc = None

    if rdse.fromid in pclist:
        print("pc in list")
        pc = pclist[rdse.fromid]
        print(pc.signalingState)
        await pc.setRemoteDescription(rdse)
        print(pc.signalingState)

    if rdse.type == 'offer': # run on receiver
        print("send local sdp (answer)")

        if pc is None:
            print("pc is none")
            pc = RTCPeerConnection()
            pclist[rdse.fromid] = pc

            @pc.on('datachannel')
            def on_datachannel(channel):
                start = time.time()
                octets = 0

                @channel.on('message')
                async def on_message(message):
                    nonlocal octets

                    if message:
                        octets += len(message)
                        print('received message : ', message)
                    else:
                        elapsed = time.time() - start
                        print('received %d bytes in %.1f s (%.3f Mbps)' % (octets, elapsed, octets * 8 / elapsed / 1000000))

                        # say goodbye
                        #await signaling.send(None)

                @channel.on('ended')
                def on_ended():
                    print('ended')

            @pc.on('iceconnectionstatechange')
            def on_iceconnectionstatechange():
                print('iceconnectionstatechange')
                print(pc.iceConnectionState)
                if pc.iceConnectionState == 'failed':
                    print(name, 'disconnected!!!!')
        

            @pc.on('track')
            def on_track(track):
                print('track')
                print(track)

            @pc.on('signalingstatechange')
            def on_signalingstatechange():
                print('signalingstatechange')
                print(pc.signalingState)

            @pc.on('icegatheringstatechange')
            def on_icegatheringstatechange():
                print('icegatheringstatechange')
                print(pc.iceGatheringState)

            await pc.setRemoteDescription(rdse)

        await pc.setLocalDescription(await pc.createAnswer())
        rsde = RTCSessionDescriptionEx.copy(pc.localDescription)
        rsde.fromid = name
        rsde.toid = rdse.fromid
        await signaling.send(rsde)

async def consume_signaling(signaling, name):
    while True:
        obj = await signaling.receive()
        if isinstance(obj, RTCSessionDescriptionEx):
            if obj.toid == name:
                print("recv remote sdp")

                await newdc(obj, signaling, name)
        else:
            print('Exiting')
            


async def run_answer(signaling, name):
    

    
        

    await consume_signaling(signaling, name)


async def run_offer(signaling, name):
    global pclist

    done_reading = False

    pc = RTCPeerConnection()
    pclist['server'] = pc

    channel = pc.createDataChannel('filexfer')

    print(pc.signalingState)

    def send_data():
        nonlocal done_reading

        while (channel.bufferedAmount <= channel.bufferedAmountLowThreshold) and not done_reading:
            channel.send(name)
            done_reading = True

    channel.on('bufferedamountlow', send_data)
    channel.on('open', send_data)

    # send offer
    await pc.setLocalDescription(await pc.createOffer())
    print(pc.signalingState)
    print("send local sdp (offer)")
    #await signaling.send(pc.localDescription)
    rsde = RTCSessionDescriptionEx.copy(pc.localDescription)
    rsde.fromid = name
    rsde.toid = 'server'
    await signaling.send(rsde)

    await consume_signaling(signaling, name)

async def start_rtc(isServer, host, port, name):
    signaling = create_ws_signaling(host, port)
    await signaling.connect()

    if isServer:
        await run_answer(signaling, name)
    else:
        await run_offer(signaling, name)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Data channel test')
    parser.add_argument('role', choices=['server', 'peer'])
    parser.add_argument('name')
    args = parser.parse_args()

    #logging.basicConfig(level=logging.DEBUG)

    coro = start_rtc(args.role == 'server', '127.0.0.1', 8765, args.name)

    # run event loop
    loop = asyncio.get_event_loop()

    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    except KeyboardInterrupt:
        pass
    #finally:
    #    loop.run_until_complete(pc.close())
    #    loop.run_until_complete(signaling.close())


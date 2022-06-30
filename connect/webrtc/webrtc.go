
// The MIT License

// Copyright (c) 2022 ETRI

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.

package webrtc

import (
	"connect"
	"encoding/json"
	"log"
)

type WebrtcConnect struct {
	connect.Common

	recvChan      chan interface{}
	sendChan      chan interface{}
	signalHandler SignalHandler

	peerMap map[string]*Peer
}

func (self *WebrtcConnect) Init(peerId string) {
	self.CommonInit(peerId)

	self.recvChan = make(chan interface{})
	self.sendChan = make(chan interface{})

	self.peerMap = make(map[string]*Peer)

	var wsaddr string = self.Config.SignalingServerAddr

	go self.signalSend()
	go self.signalReceive()
	self.signalHandler.Start(wsaddr, &self.recvChan)
}

func (self *WebrtcConnect) signalSend() {
	for {
		select {
		case send := <-self.sendChan:
			var obj interface{}

			switch send.(type) {
			case connect.RTCSessionDescription:
				sdp := send.(connect.RTCSessionDescription)
				sdp.Fromid = self.PeerId()
				obj = sdp
			case connect.RTCIceCandidate:
				ice := send.(connect.RTCIceCandidate)
				ice.Fromid = self.PeerId()
				obj = ice
			}

			buf, err := json.Marshal(obj)
			if err != nil {
				log.Println("json marshal:", err)
			} else {
				self.signalHandler.Send(buf)
			}
		}
	}
}

func (self *WebrtcConnect) signalReceive() {
	for {
		select {
		case recv := <-self.recvChan:
			switch recv.(type) {
			case connect.RTCSessionDescription:
				sdp := recv.(connect.RTCSessionDescription)
				//fmt.Println(sdp)

				if sdp.Toid == self.PeerId() {
					peer, ok := self.peerMap[sdp.Fromid]

					if ok {
						if sdp.Type == "answer" {
							log.Printf("receive answer from %s", sdp.Fromid)
							peer.SetSdp(sdp)
						}
					} else {
						if sdp.Type == "offer" {
							log.Printf("receive offer from %s", sdp.Fromid)
							peer = NewPeer(sdp.Fromid, true, &self.sendChan)
							self.peerMap[sdp.Fromid] = peer
							peer.ReceiveOffer(sdp)
						}
					}
				}

			case connect.RTCIceCandidate:
				ice := recv.(connect.RTCIceCandidate)
				//fmt.Println(ice)

				if ice.Toid == self.PeerId() {
					peer, ok := self.peerMap[ice.Fromid]

					if ok {
						log.Printf("receive iceCandidate from %s", ice.Fromid)
						peer.AddIceCandidate(ice)
					}
				}
			}
		}
	}
}

func (self *WebrtcConnect) ConnectTo(peerId string) {
	peer := NewPeer(peerId, false, &self.sendChan)

	self.peerMap[peerId] = peer

	peer.CreateOffer()
}

func (self *WebrtcConnect) BroadcastMessage(msg string) {
	for _, val := range self.peerMap {
		val.SendMessage(msg)
	}
}

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
	"fmt"
	"log"
	"sync"

	pwebrtc "github.com/pion/webrtc/v3"
)

type Peer struct {
	ToPeerId    string
	IsIncomming bool

	signalSend *chan interface{}

	candidatesMux     sync.Mutex
	pendingCandidates []*pwebrtc.ICECandidate

	config         pwebrtc.Configuration
	peerConnection *pwebrtc.PeerConnection
	dataChannel    *pwebrtc.DataChannel
}

func NewPeer(toPeerId string, isIncomming bool, signalSend *chan interface{}) *Peer {
	peer := new(Peer)
	peer.ToPeerId = toPeerId
	peer.IsIncomming = isIncomming
	peer.signalSend = signalSend

	peer.config = pwebrtc.Configuration{
		ICEServers: []pwebrtc.ICEServer{
			{
				URLs: []string{"stun:stun.l.google.com:19302"},
			},
		},
	}
	peer.pendingCandidates = make([]*pwebrtc.ICECandidate, 0)

	return peer
}

func (self *Peer) Close() {
	if cErr := self.peerConnection.Close(); cErr != nil {
		log.Printf("cannot close peerConnection: %v\n", cErr)
	}
}

func (self *Peer) signalCandidate(c *pwebrtc.ICECandidate) error {
	//payload := []byte(c.ToJSON().Candidate)
	candi := connect.RTCIceCandidate{}
	candi.Candidate = c.ToJSON().Candidate
	candi.Toid = self.ToPeerId
	candi.Type = "candidate"

	log.Printf("send iceCandidate to %s", self.ToPeerId)
	*self.signalSend <- candi

	return nil
}

func (self *Peer) AddIceCandidate(ice connect.RTCIceCandidate) {
	/*buf, err := json.Marshal(ice.Candidate)
	if err != nil {
		panic(err)
	}*/

	err := self.peerConnection.AddICECandidate(pwebrtc.ICECandidateInit{Candidate: ice.Candidate})

	if err != nil {
		panic(err)
	}
}

func (self *Peer) SetSdp(rsdp connect.RTCSessionDescription) {
	err := self.peerConnection.SetRemoteDescription(rsdp.Sdp)
	if err != nil {
		panic(err)
	}
}

func (self *Peer) newPeerConnection(createDataChannel bool) {
	peerConnection, err := pwebrtc.NewPeerConnection(self.config)
	if err != nil {
		panic(err)
	}

	self.peerConnection = peerConnection

	peerConnection.OnICECandidate(func(c *pwebrtc.ICECandidate) {
		if c == nil {
			return
		}

		self.candidatesMux.Lock()
		defer self.candidatesMux.Unlock()

		desc := peerConnection.RemoteDescription()
		if desc == nil {
			self.pendingCandidates = append(self.pendingCandidates, c)
		} else if onICECandidateErr := self.signalCandidate(c); onICECandidateErr != nil {
			panic(onICECandidateErr)
		}
	})

	if createDataChannel {
		dataChannel, err := self.peerConnection.CreateDataChannel("data", nil)
		if err != nil {
			panic(err)
		}
		self.dataChannel = dataChannel

		peerConnection.OnConnectionStateChange(func(s pwebrtc.PeerConnectionState) {
			fmt.Printf("Peer Connection State has changed: %s\n", s.String())

			if s == pwebrtc.PeerConnectionStateFailed {
				// Wait until PeerConnection has had no network activity for 30 seconds or another failure. It may be reconnected using an ICE Restart.
				// Use webrtc.PeerConnectionStateDisconnected if you are interested in detecting faster timeout.
				// Note that the PeerConnection may come back from PeerConnectionStateDisconnected.
				panic("Peer Connection has gone to failed exiting")

			}
		})

		self.dataChannel.OnOpen(func() {
			self.OnDataChannelOpen()
		})

		self.dataChannel.OnMessage(func(msg pwebrtc.DataChannelMessage) {
			self.OnDataChannelMessage(msg)
		})
	} else {
		self.peerConnection.OnDataChannel(func(d *pwebrtc.DataChannel) {
			self.dataChannel = d

			self.dataChannel.OnOpen(func() {
				self.OnDataChannelOpen()
			})

			self.dataChannel.OnMessage(func(msg pwebrtc.DataChannelMessage) {
				self.OnDataChannelMessage(msg)
			})
		})
	}

}

func (self *Peer) OnDataChannelOpen() {
	fmt.Printf("Data channel '%s'-'%d' open.\n", self.dataChannel.Label(), self.dataChannel.ID())
}

func (self *Peer) OnDataChannelMessage(msg pwebrtc.DataChannelMessage) {
	fmt.Printf("Message from DataChannel '%s': '%s'\n", self.dataChannel.Label(), string(msg.Data))
}

func (self *Peer) CreateOffer() {
	self.newPeerConnection(true)

	offer, err := self.peerConnection.CreateOffer(nil)
	if err != nil {
		panic(err)
	}

	if err = self.peerConnection.SetLocalDescription(offer); err != nil {
		panic(err)
	}

	rsdp := connect.RTCSessionDescription{}
	rsdp.Toid = self.ToPeerId
	rsdp.Type = "offer"
	rsdp.Sdp = offer

	log.Printf("send offer to %s", self.ToPeerId)
	*self.signalSend <- rsdp
}

func (self *Peer) ReceiveOffer(rsdp connect.RTCSessionDescription) {
	self.newPeerConnection(false)

	if err := self.peerConnection.SetRemoteDescription(rsdp.Sdp); err != nil {
		panic(err)
	}

	answer, err := self.peerConnection.CreateAnswer(nil)
	if err != nil {
		panic(err)
	}

	ranswer := connect.RTCSessionDescription{}
	ranswer.Sdp = answer
	ranswer.Toid = self.ToPeerId
	ranswer.Type = "answer"

	*self.signalSend <- ranswer

	err = self.peerConnection.SetLocalDescription(answer)
	if err != nil {
		panic(err)
	}

	self.candidatesMux.Lock()
	for _, c := range self.pendingCandidates {
		onICECandidateErr := self.signalCandidate(c)
		if onICECandidateErr != nil {
			panic(onICECandidateErr)
		}
	}
	self.candidatesMux.Unlock()
}

func (self *Peer) SendMessage(msg string) {
	if self.dataChannel != nil {
		self.dataChannel.SendText(msg)
	}
}

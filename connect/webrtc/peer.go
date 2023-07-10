//
// The MIT License
//
// Copyright (c) 2022 ETRI
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
// THE SOFTWARE.
//

package webrtc

import (
	"connect"
	"consts"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"logger"
	"strings"
	"sync"
	"time"

	"github.com/pion/rtcp"
	pwebrtc "github.com/pion/webrtc/v3"
)

type Peer struct {
	ToPeerId   string
	ToOriginId string
	//ToInstanceId     string
	//ToPeerInstanceId string
	ToTicketId int
	Info       *connect.Common
	IsOutGoing bool
	Position   connect.PeerPosition

	signalSend       *chan interface{}
	ppChan           chan interface{}
	connectChan      *chan bool
	broadcastChan    *chan interface{}
	buffermapResChan *chan *connect.BuffermapResponse

	candidatesMux sync.Mutex

	pendingCandidates []*pwebrtc.ICECandidate

	webRtcConfig   pwebrtc.Configuration
	peerConnection *pwebrtc.PeerConnection
	dataChannel    *pwebrtc.DataChannel
	ConnectObj     *WebrtcConnect

	heartbeatCount int
	releasePeer    bool

	MediaReceive bool

	probeTime *int64

	isVerticalCandidate bool
}

func NewPeer(toPeerId string, position connect.PeerPosition, connectChan *chan bool, conn *WebrtcConnect) *Peer {
	peer := new(Peer)

	peer.ToPeerId = toPeerId
	if strings.Contains(toPeerId, ";") {
		peer.ToOriginId = strings.Split(toPeerId, ";")[0]
	}

	peer.Position = position
	peer.ConnectObj = conn

	peer.Info = &conn.Common
	peer.signalSend = &conn.sendChan
	peer.connectChan = connectChan
	peer.broadcastChan = &conn.broadcastChan

	peer.ppChan = make(chan interface{})
	peer.releasePeer = false
	peer.heartbeatCount = 0
	peer.MediaReceive = false

	peer.webRtcConfig = pwebrtc.Configuration{
		ICEServers: []pwebrtc.ICEServer{
			{
				URLs: []string{"stun:stun.l.google.com:19302"},
			},
		},
	}
	peer.pendingCandidates = make([]*pwebrtc.ICECandidate, 0)

	peer.peerConnection = nil

	peer.isVerticalCandidate = false

	return peer
}

func (self *Peer) Close() {

	if self.releasePeer {
		return
	}

	self.releasePeer = true

	if self.peerConnection.ConnectionState() <= pwebrtc.PeerConnectionStateConnected {
		if cErr := self.peerConnection.Close(); cErr != nil {
			log.Printf("cannot close peerConnection: %v\n", cErr)
		}
	}

	close(*self.connectChan)
	close(self.ppChan)
}

func (self *Peer) InitConnection(position connect.PeerPosition) {
	if self.peerConnection.ConnectionState() <= pwebrtc.PeerConnectionStateConnected {
		if cErr := self.peerConnection.Close(); cErr != nil {
			log.Printf("cannot close peerConnection: %v\n", cErr)
		}
	}
	self.peerConnection = nil

	self.Position = position

}

func (self *Peer) signalCandidate(c *pwebrtc.ICECandidate) error {
	candi := connect.RTCIceCandidate{}
	candi.Candidate = c.ToJSON().Candidate
	candi.Toid = self.ToPeerId
	candi.Type = "candidate"

	logger.Println(logger.INFO, "send iceCandidate to", self.ToPeerId)
	*self.signalSend <- candi

	return nil
}

func (self *Peer) AddIceCandidate(ice connect.RTCIceCandidate) {

	if self.releasePeer {
		return
	}

	err := self.peerConnection.AddICECandidate(pwebrtc.ICECandidateInit{Candidate: ice.Candidate})

	if err != nil {
		//panic(err)
		logger.Println(logger.ERROR, err)
	}
}

func (self *Peer) SetSdp(rsdp connect.RTCSessionDescription) {
	err := self.peerConnection.SetRemoteDescription(rsdp.Sdp)
	if err != nil {
		panic(err)
	}

	self.candidatesMux.Lock()
	for _, c := range self.pendingCandidates {
		if self.releasePeer {
			break
		}

		onICECandidateErr := self.signalCandidate(c)
		if onICECandidateErr != nil {
			panic(onICECandidateErr)
		}
	}
	self.candidatesMux.Unlock()
}

func (self *Peer) newPeerConnection(createDataChannel bool) {
	peerConnection, err := pwebrtc.NewPeerConnection(self.webRtcConfig)
	if err != nil {
		panic(err)
	}

	self.peerConnection = peerConnection

	peerConnection.OnICECandidate(func(c *pwebrtc.ICECandidate) {
		if c == nil {
			return
		}

		if self.releasePeer {
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
		self.peerConnection.OnTrack(func(tr *pwebrtc.TrackRemote, r *pwebrtc.RTPReceiver) {
			logger.Println(logger.INFO, self.ToPeerId, "OnTrack!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! create", tr.Kind())
			self.setLocalTrack(tr, r)
		})

		dataChannel, err := self.peerConnection.CreateDataChannel("data", nil)
		if err != nil {
			panic(err)
		}
		self.dataChannel = dataChannel

		peerConnection.OnConnectionStateChange(func(s pwebrtc.PeerConnectionState) {
			logger.Printf(logger.WORK, self.ToPeerId, "Peer Connection State has changed: ", s.String())

			if !self.releasePeer && s >= pwebrtc.PeerConnectionStateFailed {
				self.Info.DelConnectionInfo(self.Position, self.ToPeerId)
				self.ConnectObj.DisconnectFrom(self)
			}
		})

		self.dataChannel.OnOpen(func() {
			self.OnDataChannelOpen()
		})

		self.dataChannel.OnMessage(func(msg pwebrtc.DataChannelMessage) {
			self.OnDataChannelMessage(msg)
		})
	} else {
		self.peerConnection.OnConnectionStateChange(func(s pwebrtc.PeerConnectionState) {
			logger.Println(logger.WORK, self.ToPeerId, "Connection State has changed:", s.String())

			if !self.releasePeer && s >= pwebrtc.PeerConnectionStateFailed {
				self.Info.DelConnectionInfo(self.Position, self.ToPeerId)
				self.ConnectObj.DisconnectFrom(self)
			}
		})

		self.peerConnection.OnTrack(func(tr *pwebrtc.TrackRemote, r *pwebrtc.RTPReceiver) {
			logger.Println(logger.WORK, self.ToPeerId, "OnTrack!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!", tr.Kind())

			self.setLocalTrack(tr, r)
		})

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

func (self *Peer) setLocalTrack(tr *pwebrtc.TrackRemote, r *pwebrtc.RTPReceiver) {

	if self.Info.OverlayInfo.OwnerId == self.Info.PeerId() {
		return
	}

	self.MediaReceive = true

	go func() {
		if self.releasePeer {
			return
		}

		ticker := time.NewTicker(time.Second * 3)
		for range ticker.C {
			if self.releasePeer {
				return
			}

			if !self.MediaReceive {
				return
			}

			if rtcpSendErr := self.peerConnection.WriteRTCP([]rtcp.Packet{&rtcp.PictureLossIndication{MediaSSRC: uint32(tr.SSRC())}}); rtcpSendErr != nil {
				logger.Println(logger.ERROR, self.ToPeerId, "WriteRTCP error:", rtcpSendErr)
			}
		}
	}()

	codecType := tr.Kind()

	var lTrack *pwebrtc.TrackLocalStaticRTP = nil

	if codecType == pwebrtc.RTPCodecTypeVideo {
		lTrack = self.Info.GetTrack("video")

		if lTrack == nil {
			localTrack, newTrackErr := pwebrtc.NewTrackLocalStaticRTP(tr.Codec().RTPCodecCapability, "video", "pion")
			if newTrackErr != nil {
				panic(newTrackErr)
			}
			lTrack = localTrack
		}

		self.ConnectObj.OnTrack(self.ToPeerId, "video", lTrack)
	} else {
		lTrack = self.Info.GetTrack("audio")

		if lTrack == nil {
			localTrack, newTrackErr := pwebrtc.NewTrackLocalStaticRTP(tr.Codec().RTPCodecCapability, "audio", "pion")
			if newTrackErr != nil {
				panic(newTrackErr)
			}
			lTrack = localTrack
		}

		self.ConnectObj.OnTrack(self.ToPeerId, "audio", lTrack)
	}

	rtpBuf := make([]byte, 1400)
	for {
		if self.releasePeer {
			break
		}

		if !self.MediaReceive {
			break
		}

		if lTrack == nil {
			continue
		}

		tr.SetReadDeadline(time.Now().Add(time.Second * 5))
		//logger.Println(logger.INFO, self.ToPeerId, "!!!!!!!! read start !!!!!!!!")
		i, _, readErr := tr.Read(rtpBuf)
		//logger.Println(logger.INFO, self.ToPeerId, "!!!!!!!! read end !!!!!!!!", i)
		if readErr != nil {
			logger.Println(logger.ERROR, self.ToPeerId, "localtrack read error:", readErr)
			continue
		}

		//logger.Println(logger.INFO, self.ToPeerId, "!!!!!!!! write !!!!!!!!", i)

		// ErrClosedPipe means we don't have any subscribers, this is ok if no peers have connected yet
		if _, err := lTrack.Write(rtpBuf[:i]); err != nil && !errors.Is(err, io.ErrClosedPipe) {
			//panic(err)
			logger.Println(logger.ERROR, self.ToPeerId, "localtrack write error:", err)
			continue
		}
	}
}

func (self *Peer) OnDataChannelOpen() {
	logger.Printf(logger.INFO, "Data channel '%s'-'%d' open.\n", self.dataChannel.Label(), self.dataChannel.ID())

	*self.connectChan <- true
}

func (self *Peer) OnDataChannelMessage(msg pwebrtc.DataChannelMessage) {
	length := binary.BigEndian.Uint16(msg.Data[2:4])
	var unknown interface{}
	err := json.Unmarshal(msg.Data[4:length+4], &unknown)

	if err != nil {
		logger.Println(logger.ERROR, "datachannel msg parsing error :", err)
		return
	}

	hstruct := unknown.(map[string]interface{})

	//logger.Println(logger.INFO, self.ToPeerId, "DataChannel recv :", hstruct)

	if c, ok := hstruct["req-code"]; ok {
		code := int(c.(float64))

		switch code {
		case connect.ReqCode_Hello:
			header := connect.HelloPeer{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvHello(&header)

		case connect.ReqCode_Estab:
			header := connect.EstabPeer{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvEstab(&header)

		case connect.ReqCode_Probe:
			header := connect.ProbePeerRequest{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvProbe(&header)

		case connect.ReqCode_Primary:
			header := connect.PrimaryPeer{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvPrimary(&header)

		case connect.ReqCode_Candidate:
			header := connect.CandidatePeer{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvCandidate(&header)

		case connect.ReqCode_BroadcastData:
			header := connect.BroadcastData{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvBroadcastData(&header, msg.Data[length+4:])

		case connect.ReqCode_Release:
			header := connect.ReleasePeer{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvRelease(&header)

		case connect.ReqCode_HeartBeat:
			header := connect.HeartBeat{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvHeartBeat(&header)

		case connect.ReqCode_ScanTree:
			header := connect.ScanTree{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvScanTree(&header)

		case connect.ReqCode_Buffermap:
			header := connect.Buffermap{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvBuffermap(&header)

		case connect.ReqCode_GetData:
			header := connect.GetData{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvGetData(&header)
		}
	}

	if c, ok := hstruct["rsp-code"]; ok {
		code := int(c.(float64))

		switch code {
		case connect.RspCode_Hello:
			header := connect.HelloPeerResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvHelloResponse(&header)

		case connect.RspCode_Estab_Yes, connect.RspCode_Estab_No:
			header := connect.EstabPeerResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvEstabResponse(&header)

		case connect.RspCode_Probe:
			header := connect.ProbePeerResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvProbeResponse(&header)

		case connect.RspCode_Primary_Yes, connect.RspCode_Primary_No:
			header := connect.PrimaryPeerResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvPrimaryResponse(&header)

		case connect.RspCode_Candidate:
			header := connect.CandidatePeerResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvCandidateResponse(&header)

		case connect.RspCode_BroadcastData:
			header := connect.BroadcastDataResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvBroadcastDataResponse(&header)

		case connect.RspCode_Release:
			header := connect.ReleasePeerResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvReleaseAck(&header)

		case connect.RspCode_HeartBeat:
			header := connect.HeartBeatResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvHeartBeatResponse(&header)

		case connect.RspCode_ScanTreeLeaf, connect.RspCode_ScanTreeNonLeaf:
			header := connect.ScanTreeResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvScanTreeResponse(&header)

		case connect.RspCode_Buffermap:
			header := connect.BuffermapResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			self.recvBuffermapResponse(&header)

		case connect.RspCode_GetData:
			header := connect.GetDataResponse{}
			json.Unmarshal(msg.Data[4:length+4], &header)
			go self.recvGetDataResponse(&header, msg.Data[length+4:])
		}
	}
}

func (self *Peer) CreateOffer() {
	if self.peerConnection == nil {
		self.newPeerConnection(true)
	}

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

	//log.Printf("send offer to %s", self.ToPeerId)
	*self.signalSend <- rsdp
}

func (self *Peer) ReceiveOffer(rsdp connect.RTCSessionDescription) {
	if self.peerConnection == nil {
		self.newPeerConnection(false)
	} else {
		trs := self.peerConnection.GetTransceivers()

		if trs != nil && len(trs) > 0 {
			for _, tr := range trs {
				if tr != nil && tr.Sender() != nil {
					self.peerConnection.RemoveTrack(tr.Sender())
				}
			}
		}
	}

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
		if self.releasePeer {
			break
		}

		onICECandidateErr := self.signalCandidate(c)
		if onICECandidateErr != nil {
			panic(onICECandidateErr)
		}
	}
	self.candidatesMux.Unlock()
}

func (self *Peer) SendDataChannelString(msg string) {
	if self.dataChannel != nil {
		self.dataChannel.SendText(msg)
	}
}

func (self *Peer) SendDataChannelBytes(msg []byte) error {
	if self.dataChannel != nil {
		return self.dataChannel.Send(msg)
	}

	return fmt.Errorf("dataChannel is nil")
}

func (self *Peer) sendPPMessage(msg *connect.PPMessage) error {
	if self.dataChannel != nil {

		if self.dataChannel.ReadyState() >= pwebrtc.DataChannelStateClosing {
			logger.Println(logger.ERROR, self.ToPeerId, "dataChannel closed")
			return fmt.Errorf("dataChannel closed")
		}

		buf := []byte{}
		buf = append(buf, msg.Ver)
		buf = append(buf, msg.Type)
		lenbytes := [2]byte{}
		binary.BigEndian.PutUint16(lenbytes[:], msg.Length)
		buf = append(buf, lenbytes[:]...)
		buf = append(buf, []byte(msg.Header)...)

		if msg.Payload != nil && len(msg.Payload) > 0 {
			buf = append(buf, msg.Payload...)
		}

		return self.dataChannel.Send(buf)
	}

	logger.Println(logger.ERROR, self.ToPeerId, "dataChannel is nil")

	return fmt.Errorf("dataChannel is nil")
}

func (self *Peer) AddConnectionInfo(position connect.PeerPosition) {
	self.Position = position

	self.Info.AddConnectionInfo(position, self.ToPeerId)
}

func (self *Peer) sendHello() bool {
	hello := connect.HelloPeer{}

	hello.ReqCode = connect.ReqCode_Hello
	hello.ReqParams.Operation.OverlayId = self.Info.OverlayInfo.OverlayId
	hello.ReqParams.Operation.ConnNum = self.Info.PeerConfig.EstabPeerMaxCount //TODO check
	hello.ReqParams.Operation.Ttl = self.Info.PeerConfig.HelloPeerTTL

	hello.ReqParams.Peer.PeerId = self.Info.PeerId()
	hello.ReqParams.Peer.Address = self.Info.PeerInfo.Address
	hello.ReqParams.Peer.TicketId = self.Info.PeerInfo.TicketId

	msg := connect.GetPPMessage(&hello, nil)
	self.sendPPMessage(msg)
	logger.Println(logger.WORK, self.ToPeerId, "Send Hello :", msg)

	timeout := time.NewTimer(time.Second * 5)

	select {
	case res := <-self.ppChan:
		if !timeout.Stop() {
			<-timeout.C
		}

		if hres, ok := res.(*connect.HelloPeerResponse); ok {
			if hres.RspCode != connect.RspCode_Hello {
				logger.Println(logger.ERROR, self.ToPeerId, "Wrong response:", res)
				return false
			}

			logger.Println(logger.WORK, self.ToPeerId, "Recv Hello response:", hres)
		} else {
			logger.Println(logger.ERROR, self.ToPeerId, "Wrong response:", res)
			return false
		}

		return true

	case <-timeout.C:
		return false
	}
}

func (self *Peer) sendVerticalHello() bool {
	hello := connect.HelloPeer{}

	hello.ReqCode = connect.ReqCode_Hello
	hello.ReqParams.Operation.OverlayId = self.Info.OverlayInfo.OverlayId
	hello.ReqParams.Operation.ConnNum = self.Info.PeerConfig.EstabPeerMaxCount
	hello.ReqParams.Operation.Ttl = 1
	vc := true
	hello.ReqParams.Operation.VerticalCandidate = &vc

	hello.ReqParams.Peer.PeerId = self.Info.PeerId()
	hello.ReqParams.Peer.Address = self.Info.PeerInfo.Address
	hello.ReqParams.Peer.TicketId = self.Info.PeerInfo.TicketId

	msg := connect.GetPPMessage(&hello, nil)
	self.sendPPMessage(msg)
	logger.Println(logger.WORK, self.ToPeerId, "Send vertical-hello :", msg)

	timeout := time.NewTimer(time.Second * 5)

	select {
	case res := <-self.ppChan:
		if !timeout.Stop() {
			<-timeout.C
		}

		if hres, ok := res.(*connect.HelloPeerResponse); ok {
			if hres.RspCode != connect.RspCode_Hello {
				logger.Println(logger.ERROR, self.ToPeerId, "Wrong response:", res)
				return false
			}

			logger.Println(logger.WORK, self.ToPeerId, "Recv Hello response:", hres)
		} else {
			logger.Println(logger.ERROR, self.ToPeerId, "Wrong response:", res)
			return false
		}

		return true

	case <-timeout.C:
		return false
	}
}

func (self *Peer) RelayHello(hello *connect.HelloPeer) bool {
	msg := connect.GetPPMessage(&hello, nil)
	self.sendPPMessage(msg)
	logger.Println(logger.WORK, self.ToPeerId, "Send Hello :", msg)

	select {
	case res := <-self.ppChan:
		if hres, ok := res.(*connect.HelloPeerResponse); ok {
			logger.Println(logger.WORK, self.ToPeerId, "Recv Hello response:", hres)
			if hres.RspCode != connect.RspCode_Hello {
				return false
			}
		} else {
			logger.Println(logger.ERROR, self.ToPeerId, "Wrong response:", res)
			return false
		}

		return true

	case <-time.After(time.Second * 5):
		return false
	}
}

func (self *Peer) recvHello(hello *connect.HelloPeer) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv Hello :", hello)

	if hello.ReqParams.Peer.TicketId < self.Info.PeerInfo.TicketId {
		logger.Println(logger.WORK, "TicketId less then mine. ignore.")

		if self.Position == connect.InComing {
			self.SendRelease()
			self.ConnectObj.DisconnectFrom(self)
		}

		return
	}

	self.sendHelloResponse()
	<-time.After(time.Millisecond * 200)

	logger.Println(logger.INFO, self.ToPeerId, "position :", self.Position)

	if self.Position == connect.InComing {
		self.SendRelease()
		self.ConnectObj.DisconnectFrom(self)
	}

	*self.broadcastChan <- hello
}

func (self *Peer) sendHelloResponse() {
	hello := connect.HelloPeerResponse{}
	hello.RspCode = connect.RspCode_Hello

	logger.Println(logger.WORK, self.ToPeerId, "Send Hello resp :", hello)

	msg := connect.GetPPMessage(&hello, nil)
	self.sendPPMessage(msg)
}

func (self *Peer) recvHelloResponse(res *connect.HelloPeerResponse) bool {
	logger.Println(logger.WORK, self.ToPeerId, "recvHelloResponse:", res)
	self.ppChan <- res
	return true
}

func (self *Peer) SendEstab(allowPrimary bool) bool {
	estab := connect.EstabPeer{}
	estab.ReqCode = connect.ReqCode_Estab
	estab.ReqParams.Operation.OverlayId = self.Info.OverlayInfo.OverlayId
	estab.ReqParams.Peer.PeerId = self.Info.PeerId()
	estab.ReqParams.Peer.TicketId = self.Info.PeerInfo.TicketId
	estab.ReqParams.AllowPrimaryReq = allowPrimary

	msg := connect.GetPPMessage(&estab, nil)
	self.sendPPMessage(msg)
	logger.Println(logger.WORK, self.ToPeerId, "Send Estab :", msg)

	select {
	case res := <-self.ppChan:
		if hres, ok := res.(*connect.EstabPeerResponse); ok {
			logger.Println(logger.WORK, self.ToPeerId, "Recv Estab response:", hres)
			if hres.RspCode != connect.RspCode_Estab_Yes {
				return false
			}
		} else {
			return false
		}

		return true

	case <-time.After(time.Second * 5):
		return false
	}
}

func (self *Peer) recvEstab(estab *connect.EstabPeer) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv Estab :", estab)

	if self.Info.OverlayInfo.OverlayId != estab.ReqParams.Operation.OverlayId {
		logger.Println(logger.WORK, self.ToPeerId, "Estab OverlayId not match")
		self.SendEstabResponse(false)
		self.ConnectObj.DisconnectFrom(self)
		return
	}

	self.ToTicketId = estab.ReqParams.Peer.TicketId
	self.isVerticalCandidate = estab.ReqParams.Peer.PeerId == self.Info.GrandParentId

	logger.Println(logger.INFO, self.ToPeerId, "----------------------------------------------------------------")
	logger.Println(logger.INFO, self.ToPeerId, "estab.ReqParams.Peer.PeerId:", estab.ReqParams.Peer.PeerId)
	logger.Println(logger.INFO, self.ToPeerId, "self.Info.GrandParentId:", self.Info.GrandParentId)
	logger.Println(logger.INFO, self.ToPeerId, "self.isVerticalCandidate:", self.isVerticalCandidate)
	logger.Println(logger.INFO, self.ToPeerId, "----------------------------------------------------------------")

	if self.Info.PeerConfig.ProbePeerTimeout > 0 {
		if self.Info.PeerConfig.EstabPeerMaxCount <= self.Info.EstabPeerCount && !self.isVerticalCandidate {
			logger.Println(logger.WORK, self.ToPeerId, "EstabPeerMaxCount <= EstabPeerCount")
			self.SendEstabResponse(false)
			self.ConnectObj.DisconnectFrom(self)
		} else {
			self.Info.EstabPeerCount++
			self.Position = connect.Established
			self.SendEstabResponse(true)
			go self.sendHeartBeat()
		}
	} else {
		self.Info.OutGoingPrimaryMux.Lock()
		if self.Info.HaveOutGoingPrimary {
			if self.candidateCheck(true) {
				go self.sendHeartBeat()
			}
		} else {
			self.SendEstabResponse(true)
			if estab.ReqParams.AllowPrimaryReq && self.setPrimary() {
				go self.sendHeartBeat()
			} else {
				if self.candidateCheck(false) {
					go self.sendHeartBeat()
				}
			}
		}
		self.Info.OutGoingPrimaryMux.Unlock()
	}
}

func (self *Peer) TryPrimary() {
	defer self.Info.OutGoingPrimaryMux.Unlock()

	self.Info.OutGoingPrimaryMux.Lock()
	if self.Info.HaveOutGoingPrimary {
		self.candidateCheck(false)
	} else {
		if !self.setPrimary() {
			self.candidateCheck(false)
		}
	}
}

func (self *Peer) closeLowestOutGoingCandidate() {
	logger.Println(logger.INFO, "closeLowestOutGoingCandidate!!!!!!!!!!!!!!!!!!!!!!!!!!")
	peer := self.ConnectObj.lowestOutGoingCandidate()
	if peer != nil {
		logger.Println(logger.INFO, "!!!!!!!!!!!!!!!!!!!LowestOutGoingCandidate", peer.ToPeerId)
		self.Info.DelConnectionInfo(peer.Position, peer.ToPeerId)
		self.ConnectObj.DisconnectFrom(peer)
	}
}

func (self *Peer) candidateCheck(sendres bool) bool {
	if self.Info.PeerStatus.NumOutCandidate >= self.Info.PeerConfig.MaxOutgoingCandidate {
		if self.isVerticalCandidate {
			self.closeLowestOutGoingCandidate()
			return self.candidateCheck(sendres)
		}
		if sendres {
			self.SendEstabResponse(false)
		}

		self.SendRelease()
		<-time.After(time.Second * 1)
		self.ConnectObj.DisconnectFrom(self)

		return false
	} else {
		if sendres {
			self.SendEstabResponse(true)
		}
		self.AddConnectionInfo(connect.OutGoingCandidate)

		if self.Info.PeerConfig.SendCandidate {
			self.setCandidate()
		}

		return true
	}
}

func (self *Peer) SendEstabResponse(ok bool) {
	res := connect.EstabPeerResponse{}

	if ok {
		res.RspCode = connect.RspCode_Estab_Yes
	} else {
		res.RspCode = connect.RspCode_Estab_No
	}

	logger.Println(logger.WORK, self.ToPeerId, "Send Estab resp :", res)

	msg := connect.GetPPMessage(&res, nil)
	self.sendPPMessage(msg)
}

func (self *Peer) recvEstabResponse(res *connect.EstabPeerResponse) {
	self.ppChan <- res
}

func (self *Peer) setPrimary() bool {
	primary := connect.PrimaryPeer{}
	primary.ReqCode = connect.ReqCode_Primary

	if self.Info.OverlayInfo.CrPolicy != nil && self.Info.OverlayInfo.CrPolicy.RecoveryBy == connect.RecoveryByPush {
		primary.ReqParams.Buffermap = self.ConnectObj.GetBuffermap()
	}

	msg := connect.GetPPMessage(&primary, nil)
	self.sendPPMessage(msg)
	logger.Println(logger.WORK, self.ToPeerId, "Set primary:", msg)

	timeout := time.NewTimer(time.Second * 5)

	select {
	case res := <-self.ppChan:

		if !timeout.Stop() {
			<-timeout.C
		}

		var hres *connect.PrimaryPeerResponse = nil
		var ok bool

		if hres, ok = res.(*connect.PrimaryPeerResponse); ok {
			logger.Println(logger.WORK, self.ToPeerId, "Recv Primary response:", hres)
			if hres.RspCode != connect.RspCode_Primary_Yes {
				return false
			}
		} else {
			return false
		}

		self.AddConnectionInfo(connect.OutGoingPrimary)

		if self.Info.OverlayInfo.CrPolicy != nil {
			if self.Info.OverlayInfo.CrPolicy.RecoveryBy == connect.RecoveryByPush {
				self.ConnectObj.checkBuffermapForBroadcast(hres.RspParams.Buffermap)
			} else if self.Info.OverlayInfo.CrPolicy.RecoveryBy == connect.RecoveryByPull {
				self.ConnectObj.recoveryDataForPull()
			}
		}

		if hres.RspParams.ParentPeer != nil {
			logger.Println(logger.INFO, self.ToPeerId, "Parent peer !!!!!!!!!!!!!")
			logger.Println(logger.INFO, self.ToPeerId, "--->", hres.RspParams.ParentPeer.PeerId, hres.RspParams.ParentPeer.Address)

			self.Info.GrandParentId = hres.RspParams.ParentPeer.PeerId

			go self.ConnectObj.sendVerticalHello(hres.RspParams.ParentPeer.PeerId)
		}

		return true

	case <-timeout.C:
		logger.Println(logger.WORK, self.ToPeerId, "Recv Primary timeout!!!")
		return false
	}
}

func (self *Peer) recvPrimary(primary *connect.PrimaryPeer) {
	self.Info.CommunicationMux.Lock()
	logger.Println(logger.WORK, self.ToPeerId, "Recv primary :", primary)

	if self.Info.PeerConfig.MaxPrimaryConnection <= self.Info.PeerStatus.NumPrimary {
		self.Info.CommunicationMux.Unlock()
		self.sendPrimaryResponse(false)
	} else {
		self.sendPrimaryResponse(true)
		self.AddConnectionInfo(connect.InComingPrimary)

		self.Info.CommunicationMux.Unlock()

		if self.Info.OverlayInfo.CrPolicy != nil {
			if self.Info.OverlayInfo.CrPolicy.RecoveryBy == connect.RecoveryByPush {
				self.ConnectObj.checkBuffermapForBroadcast(primary.ReqParams.Buffermap)
			}
		}

		needReOffer := false

		if self.Info.VideoTrack != nil {
			_, err := self.peerConnection.AddTrack(self.Info.VideoTrack)

			if err != nil {
				panic(err)
			}

			needReOffer = true
		}

		if self.Info.AudioTrack != nil {
			_, err := self.peerConnection.AddTrack(self.Info.AudioTrack)

			if err != nil {
				panic(err)
			}

			needReOffer = true
		}

		if needReOffer {
			self.CreateOffer()
		}
	}

}

func (self *Peer) sendPrimaryResponse(ok bool) {
	pres := connect.PrimaryPeerResponse{}

	if ok {
		pres.RspCode = connect.RspCode_Primary_Yes

		if self.Info.OverlayInfo.CrPolicy.RecoveryBy == connect.RecoveryByPush {
			pres.RspParams.Buffermap = self.ConnectObj.GetBuffermap()
		}

		if self.Info.HaveOutGoingPrimary {
			parent := self.ConnectObj.outGoingPrimary()
			pres.RspParams.ParentPeer = new(connect.ParentPeer)
			pres.RspParams.ParentPeer.PeerId = parent.ToPeerId
			pres.RspParams.ParentPeer.Address = parent.Info.PeerInfo.Address
		}
	} else {
		pres.RspCode = connect.RspCode_Primary_No
	}

	logger.Println(logger.WORK, self.ToPeerId, "Send Primary resp :", pres)

	msg := connect.GetPPMessage(&pres, nil)
	self.sendPPMessage(msg)
}

func (self *Peer) recvPrimaryResponse(res *connect.PrimaryPeerResponse) {
	self.ppChan <- res
}

func (self *Peer) setCandidate() {
	candi := connect.CandidatePeer{}
	candi.ReqCode = connect.ReqCode_Candidate

	msg := connect.GetPPMessage(&candi, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Set candidate:", msg)
}

func (self *Peer) recvCandidate(res *connect.CandidatePeer) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv candidate:", res)

	self.sendCandidateResponse()
}

func (self *Peer) sendCandidateResponse() {
	candi := connect.CandidatePeerResponse{}
	candi.RspCode = connect.RspCode_Candidate

	msg := connect.GetPPMessage(&candi, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send candidate resp:", msg)
}

func (self *Peer) recvCandidateResponse(res *connect.CandidatePeerResponse) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv candidate resp:", res)
}

func (self *Peer) SendProbe() {
	pro := connect.ProbePeerRequest{}
	pro.ReqCode = connect.ReqCode_Probe
	pro.ReqParams.Operation.NtpTime = time.Now().Format("2006-01-02 15:04:05.000")

	msg := connect.GetPPMessage(&pro, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send probe:", msg)
}

func (self *Peer) recvProbe(req *connect.ProbePeerRequest) {
	res := connect.ProbePeerResponse{}
	res.RspCode = connect.RspCode_Probe
	res.RspParams.Operation.NtpTime = req.ReqParams.Operation.NtpTime

	//<-time.After(time.Second * time.Duration(1))

	msg := connect.GetPPMessage(&res, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send probe response:", msg)
}

func (self *Peer) recvProbeResponse(res *connect.ProbePeerResponse) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv probe response:", res)

	loc, _ := time.LoadLocation("Asia/Seoul")
	prbtime, err := time.ParseInLocation("2006-01-02 15:04:05.000", res.RspParams.Operation.NtpTime, loc)
	if err != nil {
		logger.Println(logger.ERROR, self.ToPeerId, "probetime parse error:", err)
		self.probeTime = nil
	} else {
		now := time.Now().In(loc)
		duration := int64(now.Sub(prbtime) / time.Millisecond)
		self.probeTime = &duration
		logger.Println(logger.WORK, self.ToPeerId, "probe time:", duration, "ms")
	}
}

func (self *Peer) SendRelease() {
	rel := connect.ReleasePeer{}
	rel.ReqCode = connect.ReqCode_Release
	rel.ReqParams.Operation.Ack = self.Info.PeerConfig.ReleaseOperationAck

	msg := connect.GetPPMessage(&rel, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send release peer:", msg)
}

func (self *Peer) recvRelease(req *connect.ReleasePeer) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv release peer:", req)

	if req.ReqParams.Operation.Ack {
		self.sendReleaseAck()
	}

	self.Info.DelConnectionInfo(self.Position, self.ToPeerId)
	self.ConnectObj.DisconnectFrom(self)
}

func (self *Peer) sendReleaseAck() {
	res := connect.ReleasePeerResponse{}
	res.RspCode = connect.RspCode_Release

	msg := connect.GetPPMessage(&res, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send release ack:", msg)
}

func (self *Peer) recvReleaseAck(res *connect.ReleasePeerResponse) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv release ack:", res)

	self.releasePeer = true

}

func (self *Peer) sendHeartBeat() {
	interval := float32(self.Info.OverlayInfo.HeartbeatInterval) * 0.9

	for range time.Tick(time.Second * time.Duration(interval)) {
		if self.releasePeer {
			return
		}

		req := connect.HeartBeat{}
		req.ReqCode = connect.ReqCode_HeartBeat
		msg := connect.GetPPMessage(&req, nil)
		err := self.sendPPMessage(msg)

		if err != nil {
			logger.Println(logger.WORK, self.ToPeerId, "Send heartbeat failed!", err)
			self.Info.DelConnectionInfo(self.Position, self.ToPeerId)
			self.ConnectObj.DisconnectFrom(self)
		} else {
			//logger.Println(logger.WORK, self.ToPeerId, "Send heartbeat:", msg)
		}
	}
}

func (self *Peer) CheckHeartBeatRecved() {
	go func() {
		for range time.Tick(time.Second * 1) {
			if self.releasePeer {
				return
			}

			self.heartbeatCount++

			if self.heartbeatCount > self.Info.OverlayInfo.HeartbeatTimeout {
				logger.Println(logger.WORK, self.ToPeerId, "Heartbeat timeout!")
				self.Info.DelConnectionInfo(self.Position, self.ToPeerId)
				self.ConnectObj.DisconnectFrom(self)
			}

		}
	}()
}

func (self *Peer) recvHeartBeat(req *connect.HeartBeat) {
	//logger.Println(logger.WORK, self.ToPeerId, "recv heartbeat:", req)
	self.heartbeatCount = 0
	self.sendHeartBeatResponse()
}

func (self *Peer) sendHeartBeatResponse() {
	res := connect.HeartBeatResponse{}
	res.RspCode = connect.RspCode_HeartBeat
	msg := connect.GetPPMessage(&res, nil)
	self.sendPPMessage(msg)

	//logger.Println(logger.WORK, self.ToPeerId, "Send heartbeat response:", msg)
}

func (self *Peer) recvHeartBeatResponse(res *connect.HeartBeatResponse) {
	//logger.Println(logger.WORK, self.ToPeerId, "recv heartbeat response:", res)
}

func (self *Peer) sendScanTree(cseq int) {
	req := connect.ScanTree{}
	req.ReqCode = connect.ReqCode_ScanTree
	req.ReqParams.CSeq = cseq
	req.ReqParams.Overlay.OverlayId = self.Info.OverlayInfo.OverlayId
	req.ReqParams.Overlay.Via = append(req.ReqParams.Overlay.Via, []string{self.Info.PeerId(), self.Info.PeerInfo.Address})
	//req.ReqParams.Overlay.Path = append(req.ReqParams.Overlay.Path, []string{self.Info.PeerId(), strconv.Itoa(*self.Info.OverlayInfo.TicketId), self.Info.PeerAddress})
	req.ReqParams.Peer.PeerId = self.Info.PeerId()
	req.ReqParams.Peer.TicketId = self.Info.PeerInfo.TicketId
	req.ReqParams.Peer.Address = self.Info.PeerInfo.Address

	msg := connect.GetPPMessage(&req, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send ScanTree:", msg)
}

func (self *Peer) broadcastScanTree(req *connect.ScanTree) {
	msg := connect.GetPPMessage(req, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Broadcast ScanTree:", msg)
}

func (self *Peer) recvScanTree(req *connect.ScanTree) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv ScanTree:", req)

	self.ConnectObj.RecvScanTree(req, self)
}

func (self *Peer) sendScanTreeResponse(res *connect.ScanTreeResponse) {
	msg := connect.GetPPMessage(res, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send ScanTree response:", msg)
}

func (self *Peer) recvScanTreeResponse(res *connect.ScanTreeResponse) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv ScanTree response:", res)

	if res.RspCode == connect.RspCode_ScanTreeNonLeaf {
		return
	}

	self.ConnectObj.RecvScanTreeResponse(res)
}

func (self *Peer) recvData(params *connect.GetDataRspParams, data []byte, includeOGP bool) {
	if data == nil || len(data) <= 0 {
		return
	}

	if params.Peer.PeerId == self.Info.PeerId() {
		return
	}

	if params.ExtHeaderLen > 0 {
		extHeader := connect.BroadcastDataExtensionHeader{}
		json.Unmarshal(data[:params.ExtHeaderLen], &extHeader)

		data = data[params.ExtHeaderLen:]

		if extHeader.AppId == consts.AppIdChat && params.Payload.PayloadType == consts.PayloadTypeText {
			self.ConnectObj.RecvChatCallback(params.Peer.PeerId, string(data))
		} else if extHeader.AppId == consts.AppIdData {
			self.ConnectObj.RecvDataCallback(self.ToPeerId, params.Peer.PeerId, string(data))
		} else if extHeader.AppId == consts.AppIdIoT {
			self.ConnectObj.RecvIoTCallback(string(data))
		} else if extHeader.AppId == consts.AppIdBlockChain {
			self.ConnectObj.RecvBlockChainCallback(string(data))
		} else if extHeader.AppId == consts.AppIdMedia {
			logger.Println(logger.INFO, self.ToPeerId, "Recv Media data:", len(data))
			self.ConnectObj.RecvMediaCallback(params.Peer.PeerId, &data)
		}

		broadcastParams := connect.BroadcastDataParams{}
		broadcastParams.Operation.Ack = false
		broadcastParams.Peer.PeerId = params.Peer.PeerId
		broadcastParams.Peer.Sequence = params.Sequence
		broadcastParams.Payload = params.Payload
		broadcastParams.ExtHeaderLen = params.ExtHeaderLen

		go self.ConnectObj.BroadcastData(&broadcastParams, &data, &self.ToPeerId, true, includeOGP)
	} else {
		logger.Println(logger.ERROR, self.ToPeerId, "Recv data ext-header-len error:", params.ExtHeaderLen)
	}
}

func (self *Peer) recvBroadcastData(req *connect.BroadcastData, data []byte) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv broadcast data:", req)
	//logger.Println(logger.WORK, self.ToPeerId, "Recv broadcast data content:", data)

	params := req.ReqParams

	if params.Operation.Ack {
		self.sendBroadcastDataResponse()
	}

	if !self.ConnectObj.checkBroadcastDataSeq(params.Peer.PeerId, params.Peer.Sequence) {
		logger.Println(logger.WORK, self.ToPeerId, "Already recv broadcast data seq:", params.Peer.PeerId, " - ", params.Peer.Sequence)
		return
	}

	if data == nil || len(data) <= 0 {
		return
	}

	if params.Peer.PeerId == self.Info.PeerId() {
		return
	}

	if params.ExtHeaderLen > 0 {
		extHeader := connect.BroadcastDataExtensionHeader{}
		json.Unmarshal(data[:params.ExtHeaderLen], &extHeader)

		payload := data[params.ExtHeaderLen:]

		if extHeader.AppId == consts.AppIdChat && params.Payload.PayloadType == consts.PayloadTypeText {
			self.ConnectObj.RecvChatCallback(params.Peer.PeerId, string(payload))
		} else if extHeader.AppId == consts.AppIdData {
			self.ConnectObj.RecvDataCallback(self.ToPeerId, params.Peer.PeerId, string(payload))
		} else if extHeader.AppId == consts.AppIdIoT {
			self.ConnectObj.RecvIoTCallback(string(payload))
		} else if extHeader.AppId == consts.AppIdBlockChain {
			self.ConnectObj.RecvBlockChainCallback(string(payload))
		} else if extHeader.AppId == consts.AppIdMedia {
			logger.Println(logger.INFO, self.ToPeerId, "Recv Media data:", len(payload))
			self.ConnectObj.RecvMediaCallback(params.Peer.PeerId, &payload)
		}

		go self.ConnectObj.BroadcastData(&params, &data, &self.ToPeerId, true, true)
	} else {
		logger.Println(logger.ERROR, self.ToPeerId, "Recv data ext-header-len error:", params.ExtHeaderLen)
	}
}

func (self *Peer) recvBroadcastDataResponse(res *connect.BroadcastDataResponse) {
	logger.Println(logger.WORK, self.ToPeerId, "Recv broadcast data response:", res)
}

func (self *Peer) sendBroadcastDataResponse() {
	res := connect.BroadcastDataResponse{}
	res.RspCode = connect.RspCode_BroadcastData

	msg := connect.GetPPMessage(res, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send broadcastData response:", msg)
}

func (self *Peer) sendBuffermap(resChan *chan *connect.BuffermapResponse) {
	req := connect.Buffermap{}
	req.ReqCode = connect.ReqCode_Buffermap
	req.ReqParams.OverlayId = self.Info.OverlayInfo.OverlayId

	self.buffermapResChan = resChan

	msg := connect.GetPPMessage(req, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send buffermap:", msg)
}

func (self *Peer) recvBuffermap(req *connect.Buffermap) {
	logger.Println(logger.WORK, self.ToPeerId, "recv buffermap:", req)

	if req.ReqParams.OverlayId != self.Info.OverlayInfo.OverlayId {
		logger.Println(logger.ERROR, self.ToPeerId, "recv buffermap but ovid wrong:", req)
		return
	}

	res := connect.BuffermapResponse{}
	res.RspCode = connect.RspCode_Buffermap
	res.RspParams.OverlayId = self.Info.OverlayInfo.OverlayId
	res.RspParams.Buffermap = self.ConnectObj.GetBuffermap()

	msg := connect.GetPPMessage(res, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send buffermap response:", msg)
}

func (self *Peer) recvBuffermapResponse(res *connect.BuffermapResponse) {
	defer recover()

	logger.Println(logger.WORK, self.ToPeerId, "recv buffermap response:", res)

	if res.RspParams.OverlayId != self.Info.OverlayInfo.OverlayId {
		logger.Println(logger.ERROR, self.ToPeerId, "recv buffermap response but ovid wrong:", res)
		return
	}

	if self.buffermapResChan != nil {
		*self.buffermapResChan <- res
	}
}

func (self *Peer) sendGetData(sourceId string, sequence int) {
	req := connect.GetData{}
	req.ReqCode = connect.ReqCode_GetData
	req.SourceId = sourceId
	req.Sequence = sequence
	req.OverlayId = self.Info.OverlayInfo.OverlayId

	msg := connect.GetPPMessage(req, nil)
	self.sendPPMessage(msg)

	logger.Println(logger.WORK, self.ToPeerId, "Send GetData:", msg)
}

func (self *Peer) recvGetData(req *connect.GetData) {
	logger.Println(logger.WORK, self.ToPeerId, "recv GetData:", req)

	if req.OverlayId != self.Info.OverlayInfo.OverlayId {
		logger.Println(logger.ERROR, self.ToPeerId, "recv GetData but ovid wrong:", req)
		return
	}

	payload := self.ConnectObj.GetCachingData(req.SourceId, req.Sequence)

	if payload != nil {
		res := connect.GetDataResponse{}
		res.RspCode = connect.RspCode_GetData
		res.RspParams.Peer.PeerId = payload.Header.ReqParams.Peer.PeerId
		res.RspParams.Sequence = payload.Header.ReqParams.Peer.Sequence
		res.RspParams.Payload = payload.Header.ReqParams.Payload
		res.RspParams.ExtHeaderLen = payload.Header.ReqParams.ExtHeaderLen

		/*extHeader := connect.BroadcastDataExtensionHeader{}
		json.Unmarshal((*payload.Payload)[:payload.Header.ReqParams.ExtHeaderLen], &extHeader)
		*/
		msg := connect.GetPPMessage(res, *payload.Payload)
		self.sendPPMessage(msg)

		logger.Println(logger.WORK, self.ToPeerId, "Send GetData response:", msg)
	} else {
		logger.Println(logger.ERROR, self.ToPeerId, "recv GetData but don't have data")
	}
}

func (self *Peer) recvGetDataResponse(res *connect.GetDataResponse, content []byte) {
	logger.Println(logger.WORK, self.ToPeerId, "recv GetData response:", res)

	self.recvData(&res.RspParams, content, false)
}

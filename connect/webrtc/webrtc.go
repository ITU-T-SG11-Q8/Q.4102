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
	"encoding/json"
	"logger"
	"math"
	"sort"
	"strconv"
	"time"

	pwebrtc "github.com/pion/webrtc/v3"
)

type WebrtcConnect struct {
	connect.Common
	recvChan      chan interface{}
	sendChan      chan interface{}
	broadcastChan chan interface{}
	signalHandler SignalHandler

	position connect.PeerPosition

	peerMap map[string]*Peer

	currentScanTreeCSeq int
	broadcastDataSeq    int
}

func (self *WebrtcConnect) OverlayInfo() *connect.OverlayInfo {
	return &self.Common.OverlayInfo
}

func (self *WebrtcConnect) Init(peerId string) {
	self.CommonInit(peerId)

	self.recvChan = make(chan interface{})
	self.sendChan = make(chan interface{})
	self.broadcastChan = make(chan interface{})

	self.peerMap = make(map[string]*Peer)

	//self.Common.PeerAddress = self.ClientConfig.SignalingServerAddr
	self.Common.PeerInfo.Address = self.ClientConfig.SignalingServerAddr

	go self.signalSend()
	go self.signalReceive()
	go self.broadcast()

	self.signalHandler.Start(self.Common.PeerInfo.Address, &self.recvChan)
	self.websocketHello()

	self.broadcastDataSeq = 0

	self.position = connect.Init
}

func (self *WebrtcConnect) HasConnection() bool {
	return len(*self.allPrimary()) > 0
}

func (self *WebrtcConnect) ConnectionInfo() *connect.NetworkResponse {
	info := new(connect.NetworkResponse)

	info.Peer.PeerId = self.PeerId()
	info.Peer.TicketId = *self.OverlayInfo().TicketId

	self.PeerMapMux.Lock()
	for _, peer := range self.peerMap {
		if peer.Position == connect.InComingPrimary || peer.Position == connect.OutGoingPrimary {
			info.Primary = append(info.Primary, connect.NetworkPeerInfo{PeerId: peer.ToPeerId, TicketId: peer.ToTicketId})
		} else if peer.Position == connect.InComingCandidate {
			info.InComingCandidate = append(info.InComingCandidate, connect.NetworkPeerInfo{PeerId: peer.ToPeerId, TicketId: peer.ToTicketId})
		} else if peer.Position == connect.OutGoingCandidate {
			info.OutGoingCandidate = append(info.OutGoingCandidate, connect.NetworkPeerInfo{PeerId: peer.ToPeerId, TicketId: peer.ToTicketId})
		}
	}
	self.PeerMapMux.Unlock()

	return info
}

func (self *WebrtcConnect) OnTrack(toPeerId string, kind string, track *pwebrtc.TrackLocalStaticRTP) {
	if track != nil {
		logger.Println(logger.INFO, "OnTrack!!!!!!!!!!!!!!!!!! webrtc.go", kind)
	} else {
		logger.Println(logger.INFO, "Release Track!!!!!!!!!!!!!!!!!!", kind)
	}

	if kind == "video" {
		if self.VideoTrack == nil {
			self.VideoTrack = track
		} else {
			self.ChangeVideoTrack = true
			logger.Println(logger.INFO, toPeerId, "Change Video Track!!!!!!!!")
		}
	} else {
		if self.AudioTrack == nil {
			self.AudioTrack = track
		} else {
			self.ChangeAudioTrack = true
			logger.Println(logger.INFO, toPeerId, "Change Audio Track!!!!!!!!")
		}
	}

	if self.VideoTrack != nil && self.AudioTrack != nil && !(self.ChangeAudioTrack || self.ChangeVideoTrack) {
		peerlist := self.allPrimary()

		for _, peer := range *peerlist {

			if peer.ToPeerId == toPeerId {
				continue
			}

			peer.peerConnection.AddTrack(self.VideoTrack)
			peer.peerConnection.AddTrack(self.AudioTrack)
			peer.CreateOffer()
		}
	}

	if self.ChangeAudioTrack && self.ChangeVideoTrack {
		self.ChangeVideoTrack = false
		self.ChangeAudioTrack = false

		peerlist := self.allPrimary()

		var OGPrimaryPeer *Peer = nil
		var successReOffer bool = false

		logger.Println(logger.INFO, "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
		for _, peer := range *peerlist {
			logger.Println(logger.INFO, peer.ToPeerId, "search peer!!!!!!!!")

			if peer.ToPeerId == toPeerId {
				continue
			}

			if peer.Position == connect.OutGoingPrimary {
				OGPrimaryPeer = peer
			}

			if peer.MediaReceive {
				logger.Println(logger.INFO, peer.ToPeerId, "Reoffer!!!!!!!!")
				peer.MediaReceive = false

				peer.peerConnection.AddTrack(self.VideoTrack)
				peer.peerConnection.AddTrack(self.AudioTrack)
				peer.CreateOffer()
				successReOffer = true
			}
		}

		if !successReOffer && OGPrimaryPeer != nil {
			logger.Println(logger.INFO, OGPrimaryPeer.ToPeerId, "Reoffer OGP!!!!!!!!")
			OGPrimaryPeer.MediaReceive = false

			OGPrimaryPeer.peerConnection.AddTrack(self.VideoTrack)
			OGPrimaryPeer.peerConnection.AddTrack(self.AudioTrack)
			OGPrimaryPeer.CreateOffer()
		}
	}
}

func (self *WebrtcConnect) broadcastHello(hello *connect.HelloPeer) {
	logger.Println(logger.INFO, hello.ReqParams.Peer.PeerId, "broadcasthello:")

	hello.ReqParams.Operation.Ttl -= 1

	estab := false

	//logger.Println(logger.INFO, hello.ReqParams.Peer.PeerId, "NumPrimary:", self.PeerStatus.NumPrimary, ", MaxPrimaryConnection:", self.PeerConfig.MaxPrimaryConnection)
	//logger.Println(logger.INFO, hello.ReqParams.Peer.PeerId, "NumOutCandidate:", self.PeerStatus.NumOutCandidate, ", MaxOutgoingCandidate:", self.PeerConfig.MaxOutgoingCandidate)

	if self.PeerStatus.NumPrimary < self.PeerConfig.MaxPrimaryConnection ||
		self.PeerStatus.NumInCandidate < self.PeerConfig.MaxIncomingCandidate {
		hello.ReqParams.Operation.ConnNum -= 1
		self.PeerStatus.NumInCandidate++ // count up before send estab
		estab = true
		logger.Println(logger.INFO, hello.ReqParams.Peer.PeerId, "estab true, ConnNum:", hello.ReqParams.Operation.ConnNum)
	}

	if hello.ReqParams.Operation.Ttl > 0 {
		peerlist := self.inComingPrimary()

		if len(*peerlist) > 0 {
			logger.Println(logger.INFO, "before connNum:", hello.ReqParams.Operation.ConnNum)
			connNum := float64(hello.ReqParams.Operation.ConnNum) / float64(len(*peerlist))
			connNum = math.Ceil(connNum)
			hello.ReqParams.Operation.ConnNum = int(connNum)
			logger.Println(logger.INFO, "after connNum:", hello.ReqParams.Operation.ConnNum)

			for _, peer := range *peerlist {
				if peer.ToPeerId == hello.ReqParams.Peer.PeerId {
					continue
				}

				peer.RelayHello(hello)
			}
		}
	}

	if estab {
		//<-time.After(time.Second * 3)
		logger.Println(logger.INFO, "estab:")
		conPeer, ok := self.ConnectTo(hello.ReqParams.Peer.PeerId, connect.Established)

		if ok {
			self.CommunicationMux.Lock()

			if conPeer.SendEstab() {
				self.PeerStatus.NumInCandidate-- // double count in addConnectionInfo
				conPeer.AddConnectionInfo(connect.InComingCandidate)
				conPeer.CheckHeartBeatRecved()
				conPeer.ToTicketId = hello.ReqParams.Peer.TicketId
			} else {
				self.DisconnectFrom(conPeer)
				self.PeerStatus.NumInCandidate--
			}
			self.CommunicationMux.Unlock()
		}
	}
}

func (self *WebrtcConnect) broadcast() {
	for {
		msg := <-self.broadcastChan

		logger.Println(logger.INFO, "broadcast:", msg)

		switch msg.(type) {
		case *connect.HelloPeer:
			hello := msg.(*connect.HelloPeer)

			self.broadcastHello(hello)
		}
	}
}

func (self *WebrtcConnect) websocketHello() {
	hello := struct {
		Action string `json:"action"`
		PeerId string `json:"peer-id"`
	}{
		"hello",
		self.PeerId(),
	}

	self.sendChan <- hello
}

func (self *WebrtcConnect) websocketBye() {
	hello := struct {
		Action string `json:"action"`
		PeerId string `json:"peer-id"`
	}{
		"bye",
		self.PeerId(),
	}

	self.sendChan <- hello
}

func (self *WebrtcConnect) inComingPrimary() *[]*Peer {
	plist := new([]*Peer)
	self.PeerMapMux.Lock()
	for _, peer := range self.peerMap {
		if peer.Position == connect.InComingPrimary {
			*plist = append(*plist, peer)
		}
	}
	self.PeerMapMux.Unlock()
	return plist
}

func (self *WebrtcConnect) allPrimary() *[]*Peer {
	plist := new([]*Peer)
	self.PeerMapMux.Lock()
	for _, peer := range self.peerMap {
		if peer.Position == connect.OutGoingPrimary || peer.Position == connect.InComingPrimary {
			*plist = append(*plist, peer)
		}
	}
	self.PeerMapMux.Unlock()
	return plist
}

func (self *WebrtcConnect) outGoingCandidate() *[]*Peer {
	plist := new([]*Peer)
	self.PeerMapMux.Lock()
	for _, peer := range self.peerMap {
		if peer.Position == connect.OutGoingCandidate {
			*plist = append(*plist, peer)
		}
	}
	self.PeerMapMux.Unlock()
	return plist
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
			default:
				obj = send
			}

			buf, err := json.Marshal(obj)
			if err != nil {
				logger.Println(logger.ERROR, "signal json marshal:", err)
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

					self.PeerMapMux.Lock()
					peer, ok := self.peerMap[sdp.Fromid]

					if ok {
						logger.Println(logger.WORK, "receive", sdp.Type, "from", sdp.Fromid)
						if sdp.Type == "answer" {
							peer.SetSdp(sdp)
						} else if sdp.Type == "offer" {
							if peer.Position == connect.SendHello {
								logger.Println(logger.WORK, sdp.Fromid, "Already connect. ignore.")
							} else {
								peer.ReceiveOffer(sdp)
							}
						}
						self.PeerMapMux.Unlock()
					} else {
						if sdp.Type == "offer" {
							logger.Printf(logger.WORK, "receive offer from %s", sdp.Fromid)

							connectChan := make(chan bool, 1)

							/*peer = NewPeer(sdp.Fromid, &self.Common, connect.InComing,
							&self.sendChan, &connectChan, &self.broadcastChan, self.DisconnectFrom,
							self.OnTrack, self.RecvScanTree, self.RecvScanTreeResponse, self.recvChat,
							self.BroadcastData, self.GetBuffermap)*/
							peer = NewPeer(sdp.Fromid, connect.InComing, &connectChan, self)
							self.peerMap[sdp.Fromid] = peer
							self.PeerMapMux.Unlock()

							peer.ReceiveOffer(sdp)

							go func() {
								conn, ok := <-connectChan

								if !conn && ok {
									self.DisconnectFrom(peer)
								}
							}()
						} else {
							self.PeerMapMux.Unlock()
						}
					}
				}

			case connect.RTCIceCandidate:
				ice := recv.(connect.RTCIceCandidate)
				//fmt.Println(ice)

				if ice.Toid == self.PeerId() {
					peer, ok := self.peerMap[ice.Fromid]

					if ok {
						logger.Printf(logger.WORK, "receive iceCandidate from %s", ice.Fromid)
						peer.AddIceCandidate(ice)
					}
				}
			}
		}
	}
}

func (self *WebrtcConnect) probePeers() {
	self.PeerMapMux.Lock()
	for _, peer := range self.peerMap {
		if peer.Position == connect.Established {
			peer.SendProbe()
		} /* else { recovery 일때는 estab 아닌애들도 있다...
			self.DisconnectFrom(peer)
		}*/
	}
	self.PeerMapMux.Unlock()

	<-time.After(time.Second * time.Duration(self.PeerConfig.ProbePeerTimeout))

	// TODO probe check

	type ProbePeer struct {
		Peer           *Peer
		ProbeTimeMilli int64
	}

	pbPeers := make([]ProbePeer, 0)

	self.PeerMapMux.Lock()
	for _, peer := range self.peerMap {
		if peer.Position == connect.Established {
			if peer.probeTime != nil {
				pbPeer := ProbePeer{}
				pbPeer.Peer = peer
				pbPeer.ProbeTimeMilli = *peer.probeTime
				pbPeers = append(pbPeers, pbPeer)
			}
		}
	}
	self.PeerMapMux.Unlock()

	sort.Slice(pbPeers, func(i, j int) bool {
		return pbPeers[i].ProbeTimeMilli < pbPeers[j].ProbeTimeMilli
	})

	for _, pbPeer := range pbPeers {
		pbPeer.Peer.TryPrimary()
	}
}

func (self *WebrtcConnect) ConnectPeers(recovery bool) {

	var retry int = 1

	if self.PeerConfig.RetryOverlayJoin {
		retry = self.PeerConfig.RetryOverlayJoinCount

		if retry <= 0 {
			retry = 1
		}
	}

	var cnt int = 0

	for recovery || cnt < retry {

		cnt++

		logger.Println(logger.INFO, "Overlay join count", cnt)

		ovinfo := self.OverlayJoin(recovery || cnt > 1)

		if ovinfo == nil {
			logger.Println(logger.ERROR, "Failed to join overlay.")
			return
		}

		ovPeerList := ovinfo.Status.PeerInfoList

		if ovPeerList == nil || len(ovPeerList) <= 0 {
			logger.Println(logger.ERROR, "Overlay peer list is empty.")
			return
		}

		logger.Println(logger.INFO, "Overlay Peer list: ", ovPeerList)

		for _, peer := range ovPeerList {

			if peer.PeerId == self.PeerId() {
				continue
			}

			self.position = connect.SendHello

			conPeer, conn := self.ConnectTo(peer.PeerId, connect.SendHello)

			if !conn {
				if conPeer != nil && conPeer.Position == connect.OutGoingCandidate {
					if conPeer.setPrimary() {
						logger.Println(logger.INFO, "Success primary with", conPeer.ToPeerId)
						break
					}
				}
				logger.Println(logger.INFO, "Failed primary with", conPeer.ToPeerId)
				continue
			}

			if !conPeer.sendHello() {
				logger.Println(logger.ERROR, conPeer.ToPeerId, "Failed to send hello")
				self.DisconnectFrom(conPeer)
				continue
			}

			self.DisconnectFrom(conPeer)

			/*
				<-time.After(time.Second * time.Duration(self.PeerConfig.PeerEstabTimeout))

				if self.PeerConfig.ProbePeerTimeout > 0 {
					if logger.LEVEL >= logger.INFO {
						for pid, peer := range self.peerMap {
							logger.Println(logger.INFO, pid, " positon: ", peer.Position)
						}
					}

					self.probePeers()

					//TODO probe after retry next
				} //else {
				if self.HaveOutGoingPrimary {
					logger.Println(logger.INFO, "Success to make primary")
					break
				} else {
					logger.Println(logger.INFO, "Failed to make primary. Try connect to next peer.")
				}
				//}*/
		}

		<-time.After(time.Second * time.Duration(self.PeerConfig.PeerEstabTimeout))

		if self.PeerConfig.ProbePeerTimeout > 0 {
			if logger.LEVEL >= logger.INFO {
				for pid, peer := range self.peerMap {
					logger.Println(logger.INFO, pid, " positon: ", peer.Position)
				}
			}

			self.probePeers()

			//TODO probe after retry next
		}

		if self.HaveOutGoingPrimary {
			logger.Println(logger.INFO, "Success to make primary")
			break
		} else {
			if recovery {
				logger.Println(logger.INFO, "Recovery after", self.PeerConfig.RetryOverlayRecoveryInterval, "sec.")
				<-time.After(time.Second * time.Duration(self.PeerConfig.RetryOverlayRecoveryInterval))
			} else if self.PeerConfig.RetryOverlayJoin {
				logger.Println(logger.INFO, "Retry after", self.PeerConfig.RetryOverlayJoinInterval, "sec.")
				<-time.After(time.Second * time.Duration(self.PeerConfig.RetryOverlayJoinInterval))
			}
		}
	}
}

func (self *WebrtcConnect) ConnectTo(toPeerId string, positon connect.PeerPosition) (*Peer, bool) {
	logger.Println(logger.WORK, "Try connect to", toPeerId)
	self.PeerMapMux.Lock()

	old, ok := self.peerMap[toPeerId]

	var rslt bool = false
	var peer *Peer = nil

	if ok {
		logger.Println(logger.WORK, "Already connect to", toPeerId)
		peer = old
		self.PeerMapMux.Unlock()
	} else {
		connectChan := make(chan bool)
		/*peer = NewPeer(toPeerId, &self.Common, positon,
		&self.sendChan, &connectChan, &self.broadcastChan, self.DisconnectFrom, self.OnTrack,
		self.RecvScanTree, self.RecvScanTreeResponse, self.recvChat, self.BroadcastData, self.GetBuffermap)*/

		peer = NewPeer(toPeerId, positon, &connectChan, self)

		self.peerMap[toPeerId] = peer
		self.PeerMapMux.Unlock()

		peer.CreateOffer()

		rslt = <-connectChan
	}

	return peer, rslt
}

func (self *WebrtcConnect) DisconnectFrom(peer *Peer) {
	if peer == nil {
		return
	}

	self.PeerMapMux.Lock()

	logger.Println(logger.WORK, "Disconnect from", peer.ToPeerId)

	delete(self.peerMap, peer.ToPeerId)

	/*self.CachingBufferMapMutex.Lock()
	delete(self.CachingBufferMap, peer.ToPeerId)
	self.CachingBufferMapMutex.Unlock()*/

	peer.Close()

	self.PeerMapMux.Unlock()

	if self.LeaveOverlay {
		return
	}

	if peer.Position == connect.OutGoingPrimary {
		logger.Println(logger.WORK, "Disconnected from OutGoingPrimary. Try recovery.")
		go self.Recovery()
	}
}

func (self *WebrtcConnect) Recovery() {

	<-time.After(time.Second * 1)

	logger.Println(logger.WORK, "Start recovery.")

	plist := self.outGoingCandidate()

	if len(*plist) > 0 {
		for _, peer := range *plist {
			if peer.setPrimary() {
				break
			}
		}

		if !self.HaveOutGoingPrimary {
			self.ConnectPeers(true)
		} /*else {
			if self.OverlayInfo().CrPolicy.RecoveryBy == connect.RecoveryByPull {
				go self.recoveryDataForPull()
			}
		}*/
	} else {
		self.ConnectPeers(true)
	}
}

/*
func (self *WebrtcConnect) DisconnectById(toPeerId string) {
	peer := self.peerMap[toPeerId]

	self.DisconnectFrom(peer)
}
*/

func (self *WebrtcConnect) SendScanTree() int {
	self.currentScanTreeCSeq = time.Now().Nanosecond()
	for _, val := range *self.allPrimary() {
		val.sendScanTree(self.currentScanTreeCSeq)
	}

	return self.currentScanTreeCSeq
}

func (self *WebrtcConnect) RecvScanTree(req *connect.ScanTree, peer *Peer) {

	if req.ReqParams.CSeq == self.currentScanTreeCSeq {
		return
	}

	peers := self.allPrimary()

	res := connect.ScanTreeResponse{}
	res.RspParams = req.ReqParams

	if len(*peers) > 1 {
		res.RspCode = connect.RspCode_ScanTreeNonLeaf
		peer.sendScanTreeResponse(&res)

		via := append([][]string{{self.PeerId(), self.Common.PeerInfo.Address}}, req.ReqParams.Overlay.Via...)
		req.ReqParams.Overlay.Via = via
		//req.ReqParams.Overlay.Path = path

		//peers = self.allPrimary()
		for _, primary := range *peers {
			if peer.ToPeerId != primary.ToPeerId {
				primary.broadcastScanTree(req)
			}
		}
	} else {
		res.RspCode = connect.RspCode_ScanTreeLeaf
		path := append([][]string{{self.PeerId(), strconv.Itoa(*self.OverlayInfo().TicketId), self.Common.PeerInfo.Address}}, req.ReqParams.Overlay.Path...)
		res.RspParams.Overlay.Path = path
		peer.sendScanTreeResponse(&res)
	}
}

func (self *WebrtcConnect) RecvScanTreeResponse(res *connect.ScanTreeResponse) {
	via := res.RspParams.Overlay.Via[0]

	if via[0] != self.PeerId() {
		logger.Println(logger.ERROR, "ScanTree response error: via[0] != me")
		return
	}

	if len(res.RspParams.Overlay.Via) == 1 {
		self.ReportScanTreeCallback(&res.RspParams.Overlay.Path, self.currentScanTreeCSeq)
	} else {
		res.RspParams.Overlay.Via = res.RspParams.Overlay.Via[1:]

		logger.Println(logger.INFO, "ScanTree response relay:", res.RspParams.Overlay.Via)

		path := append([][]string{{via[0], strconv.Itoa(*self.OverlayInfo().TicketId), via[1]}}, res.RspParams.Overlay.Path...)
		res.RspParams.Overlay.Path = path

		for _, peer := range self.peerMap {
			logger.Println(logger.INFO, "~~~~~~~~~~~ topeer:", peer.ToPeerId)
			//if strings.Compare(peer.ToPeerId, res.RspParams.Overlay.Via[0][0]) == 0 {
			if peer.ToPeerId == res.RspParams.Overlay.Via[0][0] {
				logger.Println(logger.INFO, "~!!!!!!!!!!!!! send scan rel peer:", peer.ToPeerId)
				peer.sendScanTreeResponse(res)
				break
			}
		}
	}
}

func (self *WebrtcConnect) getBroadcastDataSeq() int {
	self.broadcastDataSeq += 1
	return self.broadcastDataSeq
}

func (self *WebrtcConnect) SendData(data *[]byte, appId string) {

	req := connect.BroadcastData{}
	req.ReqCode = connect.ReqCode_BroadcastData
	req.ReqParams.Operation = &connect.BroadcastDataParamsOperation{}
	req.ReqParams.Operation.Ack = self.PeerConfig.BroadcastOperationAck
	req.ReqParams.Peer.PeerId = self.PeerId()
	req.ReqParams.Peer.Sequence = self.getBroadcastDataSeq()
	req.ReqParams.App.AppId = appId

	if appId == consts.AppIdMedia {
		req.ReqParams.Payload.ContentType = consts.ContentTypeOctetStream
	} else {
		req.ReqParams.Payload.ContentType = consts.ContentTypeText
	}

	databyte := *data

	req.ReqParams.Payload.Length = len(*data)

	self.BroadcastData(&req.ReqParams, &databyte, nil, true, true)
}

func (self *WebrtcConnect) BroadcastCachingData(sourcePeerId *string, sequence int) {
	self.CachingBufferMapMutex.Lock()

	for _, buf := range self.CachingBufferMap {

		if *sourcePeerId != buf.SourcePeerId {
			continue
		}

		buf.BufferMutax.Lock()

		for _, dp := range buf.DataPackets {
			if sequence == dp.Sequence {
				self.BroadcastData(&dp.Payload.Header.ReqParams, dp.Payload.Content, &buf.SourcePeerId, false, true)
				break
			}
		}

		buf.BufferMutax.Unlock()
	}

	self.CachingBufferMapMutex.Unlock()
}

func (self *WebrtcConnect) IoTData(data *connect.IoTData) {
	logger.Println(logger.INFO, "IOT DATA:", data)

	self.UDPConnection = true
	self.AddConnectedAppIds(data.AppId)

	appdata, err := json.Marshal(data.AppData)
	if err != nil {
		logger.Println(logger.ERROR, "IOT Data to string error:", err)
	} else {
		self.SendData(&appdata, data.AppId)
		self.RecvIoTCallback(string(appdata))
	}
}

func (self *WebrtcConnect) BlockChainData(data *connect.BlockChainData) {
	logger.Println(logger.INFO, "BlockChain DATA:", data)

	self.UDPConnection = true
	self.AddConnectedAppIds(data.AppId)

	appdata, err := json.Marshal(data.AppData)
	if err != nil {
		logger.Println(logger.ERROR, "IOT Data to string error:", err)
	} else {
		self.SendData(&appdata, data.AppId)
		//self.RecvBlockChainCallback(string(appdata))
	}
}

func (self *WebrtcConnect) MediaData(data *connect.MediaAppData) {
	logger.Println(logger.INFO, "Media DATA:", data)

	self.UDPConnection = true
	self.AddConnectedAppIds(data.AppId)

	self.SendData(data.AppData, data.AppId)
}

func (self *WebrtcConnect) BroadcastData(params *connect.BroadcastDataParams, data *[]byte, senderId *string, caching bool, includeOGP bool) {

	req := new(connect.BroadcastData)
	req.ReqCode = connect.ReqCode_BroadcastData
	req.ReqParams = *params

	if caching {
		self.dataCaching(req, data, &params.Peer.PeerId)
	}

	msg := connect.GetPPMessage(req, *data)

	for _, peer := range *self.allPrimary() {
		if senderId != nil && *senderId == peer.ToPeerId {
			continue
		}

		if req.ReqParams.Peer.PeerId == peer.ToPeerId {
			continue
		}

		if peer.Position == connect.OutGoingPrimary && !includeOGP {
			continue
		}

		logger.Println(logger.WORK, peer.ToPeerId, "send broadcastdata:", req)
		peer.sendPPMessage(msg)
	}
}

func (self *WebrtcConnect) checkCachingBuffer(buf *connect.CachingBuffer) {
	now := time.Now()

	buf.BufferMutax.Lock()

	for {
		if len(buf.DataPackets) > self.OverlayInfo().CrPolicy.MNCache {

			if self.OverlayInfo().CrPolicy.MDCache > 0 {
				packet := buf.DataPackets[0]
				ti := packet.DateTime.Add(time.Minute * time.Duration(self.OverlayInfo().CrPolicy.MDCache))
				if ti.Before(now) {
					buf.DataPackets = buf.DataPackets[1:]
				} else {
					break
				}
			} else {
				buf.DataPackets = buf.DataPackets[1:]
			}
		} else {
			break
		}
	}

	buf.BufferMutax.Unlock()
}

func (self *WebrtcConnect) GetBuffermap() *[]*connect.PeerBuffermap {
	self.CachingBufferMapMutex.Lock()

	bufmaps := new([]*connect.PeerBuffermap)

	for _, buf := range self.CachingBufferMap {
		self.checkCachingBuffer(buf)

		buf.BufferMutax.Lock()

		bufmap := connect.PeerBuffermap{}
		bufmap.SourcePeerId = buf.SourcePeerId

		for _, dp := range buf.DataPackets {
			bufmap.Sequence = append(bufmap.Sequence, dp.Sequence)
		}

		*bufmaps = append(*bufmaps, &bufmap)

		buf.BufferMutax.Unlock()
	}

	self.CachingBufferMapMutex.Unlock()

	return bufmaps
}

func (self *WebrtcConnect) GetCachingData(sourceId string, sequence int) *connect.DataPacketPayload {
	self.CachingBufferMapMutex.Lock()

	for _, buf := range self.CachingBufferMap {
		if buf.SourcePeerId == sourceId {
			for _, dp := range buf.DataPackets {
				if dp.Sequence == sequence {
					self.CachingBufferMapMutex.Unlock()
					return &dp.Payload
				}
			}
		}
	}

	self.CachingBufferMapMutex.Unlock()

	return nil
}

func (self *WebrtcConnect) dataCaching(header *connect.BroadcastData, data *[]byte, senderId *string) {

	if 0 >= self.OverlayInfo().CrPolicy.MNCache {
		return
	}

	self.CachingBufferMapMutex.Lock()
	buf := self.CachingBufferMap[*senderId]

	if buf == nil {
		buf = &connect.CachingBuffer{}
		buf.SourcePeerId = *senderId
		self.CachingBufferMap[*senderId] = buf
	}
	self.CachingBufferMapMutex.Unlock()

	buf.BufferMutax.Lock()
	for _, dp := range buf.DataPackets {
		if dp.Sequence == header.ReqParams.Peer.Sequence {
			buf.BufferMutax.Unlock()
			return
		}
	}

	dp := connect.DataPacket{}
	dp.DateTime = time.Now()
	dp.Sequence = header.ReqParams.Peer.Sequence
	dp.Payload.Header = header
	dp.Payload.Content = data

	buf.DataPackets = append(buf.DataPackets, dp)
	buf.BufferMutax.Unlock()

	self.checkCachingBuffer(buf)

	//logger.PrintJson(logger.WORK, "CachingBuffer", self.CachingBufferMap)
	logger.Println(logger.INFO, "cachingbuffer-", *senderId, "-size: ", len(buf.DataPackets))
}

func (self *WebrtcConnect) checkBuffermapForBroadcast(bufmap *[]*connect.PeerBuffermap) {

	mybufmap := self.GetBuffermap()

	missingbuf := self.checkBuffermap(bufmap, mybufmap)

	for _, buf := range missingbuf {
		for _, seq := range buf.Sequence {
			self.BroadcastCachingData(&buf.SourcePeerId, seq)
		}
	}
}

func (self *WebrtcConnect) checkBuffermapForGetData(peer *Peer, bufmap *[]*connect.PeerBuffermap) int {

	mybufmap := self.GetBuffermap()

	missingbuf := self.checkBuffermap(mybufmap, bufmap)

	var sendCnt int = 0

	for _, buf := range missingbuf {
		for _, seq := range buf.Sequence {
			//self.BroadcastBuffermap(&buf.SourcePeerId, seq)
			peer.sendGetData(buf.SourcePeerId, seq)
			sendCnt++
		}
	}

	return sendCnt
}

// target과 비교해서 source에 없는것 리턴
func (self *WebrtcConnect) checkBuffermap(source *[]*connect.PeerBuffermap, target *[]*connect.PeerBuffermap) []connect.PeerBuffermap {

	rsltBuf := make([]connect.PeerBuffermap, 0)

	if source != nil && len(*source) > 0 {
		if target != nil && len(*target) > 0 {
			for _, tbuf := range *target {
				buffind := false
				for _, buf := range *source {
					if buf.SourcePeerId != tbuf.SourcePeerId {
						continue
					}

					missing := new(connect.PeerBuffermap)
					missing.SourcePeerId = buf.SourcePeerId

					buffind = true

					for _, targetSeq := range tbuf.Sequence {
						find := false
						for _, seq := range buf.Sequence {
							if targetSeq == seq {
								find = true
								break
							}
						}

						if !find {
							missing.Sequence = append(missing.Sequence, targetSeq)
						}
					}

					rsltBuf = append(rsltBuf, *missing)
				}

				if !buffind {
					rsltBuf = append(rsltBuf, *tbuf)
				}
			}
		}
	} else {
		if target != nil {
			for _, buf := range *target {
				rsltBuf = append(rsltBuf, *buf)
			}
		}
	}

	return rsltBuf
}

func (self *WebrtcConnect) recoveryDataForPull() {

	logger.Println(logger.WORK, "Start data recovery - Pull")

	resChan := make(chan *connect.BuffermapResponse)

	/*type peerBuf struct {
		PeerId     string
		Positon    connect.PeerPosition
		Buffermaps *[]*connect.PeerBuffermap
	}*/

	candiBufmaps := make(map[*Peer]*[]*connect.PeerBuffermap, 0)
	primaryBufmap := new([]*connect.PeerBuffermap)
	var primaryPeer *Peer = nil

	self.PeerMapMux.Lock()
	for _, peer := range self.peerMap {

		if peer.Position != connect.OutGoingCandidate && peer.Position != connect.OutGoingPrimary {
			continue
		}

		pb := new([]*connect.PeerBuffermap)

		peer.sendBuffermap(&resChan)

		select {
		case res := <-resChan:
			pb = res.RspParams.Buffermap

			if peer.Position == connect.OutGoingCandidate {
				candiBufmaps[peer] = pb
			} else if peer.Position == connect.OutGoingPrimary {
				primaryPeer = peer
				primaryBufmap = pb
			}
		case <-time.After(time.Second * 5):
			logger.Println(logger.ERROR, peer.ToPeerId, "Recv Buffermap response timeout!")
			continue
		}
	}
	self.PeerMapMux.Unlock()

	close(resChan)

	logger.Println(logger.INFO, "Pull recovery response candi count:", len(candiBufmaps))

	self.checkBuffermapForBroadcast(primaryBufmap)

	for peer, candibuf := range candiBufmaps {
		sendCnt := self.checkBuffermapForGetData(peer, candibuf)
		if sendCnt > 0 {
			<-time.After(time.Second * 3)
		}
	}

	self.checkBuffermapForGetData(primaryPeer, primaryBufmap)

}

func (self *WebrtcConnect) Release(done *chan struct{}) {

	self.LeaveOverlay = true

	self.OverlayLeave()

	for _, peer := range self.peerMap {
		peer.SendRelease()
		<-time.After(time.Millisecond * 100)
		self.DisconnectFrom(peer)
	}
	//<-time.After(time.Millisecond * 100)

	close(*done)
}

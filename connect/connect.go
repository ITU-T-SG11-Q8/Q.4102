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

package connect

import (
	"consts"
	"encoding/json"
	"logger"
	"math/rand"
	"strconv"
	"sync"
	"time"

	"github.com/pion/webrtc/v3"
)

type PeerPosition int

const (
	Init PeerPosition = iota
	InComing
	OutGoing
	SendHello
	Established
	InComingCandidate
	OutGoingCandidate
	InComingPrimary
	OutGoingPrimary
	Stable
)

const (
	RecoveryByPush string = "push"
	RecoveryByPull string = "pull"
)

type Connect interface {
	Init(peerId string, instanceId int64)
	PeerId() string
	PeerInstanceId() string
	//ConnectTo(peerId string, position PeerPosition) (*Peer, bool)
	ConnectPeers(recovery bool)
	//BroadcastData(params *BroadcastDataParams, data *[]byte, senderId *string, caching bool, includeOGP bool)
	CreateOverlay(hoc *HybridOverlayCreation) *OverlayInfo
	OverlayInfo() *OverlayInfo
	PeerInfo() *PeerInfo
	OverlayJoin(recovery bool) *HybridOverlayJoinResponseOverlay
	OverlayJoinBy(hoj *HybridOverlayJoin, recovery bool) *HybridOverlayJoinResponseOverlay
	OverlayModification(hom *HybridOverlayModification) *HybridOverlayModificationOverlay
	OverlayRemove(hom *HybridOverlayRemoval) *HybridOverlayRemovalResponseOverlay
	OverlayRefresh(hor *HybridOverlayRefresh) *HybridOverlayRefreshResponse
	OverlayReport()
	OverlayReportBy(overlayId string) *HybridOverlayReportOverlay
	OverlayQuery(ovid *string, title *string, desc *string) bool
	OverlayLeave()
	OverlayLeaveBy(overlayId string) *HybridOverlayLeaveResponse
	//DisconnectById(toPeerId string)
	OnTrack(toPeerId string, kind string, track *webrtc.TrackLocalStaticRTP)
	GetTrack(kind string) *webrtc.TrackLocalStaticRTP
	Release(done *chan struct{})
	Recovery()
	SendScanTree() int
	SendData(data *[]byte, appId string)
	IsOwner() bool
	HasConnection() bool
	ConnectionInfo() *NetworkResponse
	IoTData(data *IoTData)
	BlockChainData(data *BlockChainData)
	MediaData(data *MediaAppData)
	GetClientConfig() ClientConfig
	GetPeerInfo() *PeerInfo
	GetPeerConfig() *PeerConfig
	GetPeerStatus() *PeerStatus
	GetConnectedAppIds() *[]string
	AddConnectedAppIds(appid string)

	IsUDPConnection() bool
	GetIoTPeerList() *[]string
	GetIoTDataListByPeer(peerId string) *[]IoTDataResponse
	GetIoTLastDataByPeer(peerId string) *IoTDataResponse
	GetIoTDataListByType(keyword string) *[]*IoTTypeResponse
	GetIoTLastDataByType(keyword string) *[]*IoTTypeResponse

	SetOverlayCreationCallback(ovcreate func(ovid string))
	SetScanTreeReportCallback(report func(path *[][]string, cseq int))
	SetRecvChatCallback(recvchat func(peerId string, msg string))
	SetConnectionChangeCallback(connchange func(conn bool))
	SetRecvDataCallback(recvdata func(sender string, source string, data string))
	SetLog2WebCallback(log2web func(log string))
	SetRecvIoTCallback(recviot func(msg string))
	SetRecvBlockChainCallback(recvblc func(msg string))
	SetRecvMediaCallback(recvmedia func(sender string, data *[]byte))
}

type Common struct {
	HOMP
	ClientConfig ClientConfig
	PeerConfig   PeerConfig
	PeerInfo     PeerInfo
	OverlayInfo  OverlayInfo
	//PeerAddress  string
	//PeerAuth     PeerAuth
	PeerStatus PeerStatus

	peerInstanceId string

	EstabPeerCount      int
	HaveOutGoingPrimary bool

	letterRunes []rune
	joinTicker  *time.Ticker

	OutGoingPrimaryMux sync.Mutex
	PeerMapMux         sync.Mutex
	CommunicationMux   sync.Mutex

	VideoTrack       *webrtc.TrackLocalStaticRTP
	AudioTrack       *webrtc.TrackLocalStaticRTP
	ChangeVideoTrack bool
	ChangeAudioTrack bool

	LeaveOverlay bool

	CachingBufferMap      map[string]*CachingBuffer
	CachingBufferMapMutex sync.Mutex

	overlayCreationCallback  func(ovid string)
	connectionChangeCallback func(conn bool)
	RecvDataCallback         func(sender string, source string, data string)
	log2WebCallback          func(log string)
	ReportScanTreeCallback   func(path *[][]string, cseq int)
	RecvChatCallback         func(peerId string, msg string)
	RecvIoTCallback          func(msg string)
	RecvBlockChainCallback   func(msg string)
	RecvMediaCallback        func(sender string, data *[]byte)

	UDPConnection bool

	connectedAppIds map[string]bool
}

func (conn *Common) CommonInit(peerId string, instanceId int64) {
	conn.PeerInfo.PeerId = peerId
	conn.PeerInfo.InstanceId = instanceId
	conn.ClientConfig = ReadClientConfig()
	logger.Println(logger.INFO, "client config:", conn.ClientConfig)
	conn.PeerConfig = ReadPeerConfig()
	logger.Println(logger.INFO, "peer config:", conn.PeerConfig)
	conn.OverlayAddr = conn.ClientConfig.OverlayServerAddr
	conn.PeerInfo.TicketId = -1

	conn.PeerStatus.CostMap.Primary = []string{}
	conn.PeerStatus.CostMap.OutgoingCandidate = []string{}
	conn.PeerStatus.CostMap.IncomingCandidate = []string{}

	conn.letterRunes = []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
	rand.Seed(time.Now().UnixNano())
	if len(conn.PeerInfo.Auth.Password) <= 0 {
		conn.PeerInfo.Auth.Password = conn.RandStringRunes(16)
	}
	conn.EstabPeerCount = 0
	conn.HaveOutGoingPrimary = false
	conn.VideoTrack = nil
	conn.AudioTrack = nil
	conn.ChangeAudioTrack = false
	conn.ChangeVideoTrack = false

	conn.LeaveOverlay = false

	conn.UDPConnection = false

	conn.CachingBufferMap = make(map[string]*CachingBuffer)
}

func (conn *Common) GetPeerInfo() *PeerInfo {
	return &conn.PeerInfo
}

func (conn *Common) GetPeerConfig() *PeerConfig {
	return &conn.PeerConfig
}

func (conn *Common) GetPeerStatus() *PeerStatus {
	return &conn.PeerStatus
}

func (conn *Common) IsUDPConnection() bool {
	return conn.UDPConnection
}

func (conn *Common) GetConnectedAppIds() *[]string {
	appids := make([]string, 0)

	for key := range conn.connectedAppIds {
		appids = append(appids, key)
	}

	return &appids
}

func (conn *Common) AddConnectedAppIds(appid string) {
	conn.connectedAppIds[appid] = true
}

func (conn *Common) GetIoTPeerList() *[]string {
	defer conn.CachingBufferMapMutex.Unlock()

	list := make([]string, 0)

	conn.CachingBufferMapMutex.Lock()

	for key, val := range conn.CachingBufferMap {
		for _, dp := range val.DataPackets {

			extHeader := BroadcastDataExtensionHeader{}
			err := json.Unmarshal((*dp.Payload.Payload)[:dp.Payload.Header.ReqParams.ExtHeaderLen], &extHeader)
			if err != nil {
				logger.Println(logger.ERROR, "extheader Unmarshal error:", err)
				break
			} else {
				if extHeader.AppId == consts.AppIdIoT {
					list = append(list, key)
					break
				}
			}
		}
	}

	return &list
}

func (conn *Common) GetIoTDataListByPeer(peerId string) *[]IoTDataResponse {
	defer conn.CachingBufferMapMutex.Unlock()

	list := make([]IoTDataResponse, 0)

	conn.CachingBufferMapMutex.Lock()

	val, ok := conn.CachingBufferMap[peerId]

	if ok {
		val.BufferMutax.Lock()

		for _, dp := range val.DataPackets {

			extHeader := BroadcastDataExtensionHeader{}
			err := json.Unmarshal((*dp.Payload.Payload)[:dp.Payload.Header.ReqParams.ExtHeaderLen], &extHeader)
			if err != nil {
				logger.Println(logger.ERROR, "extheader Unmarshal error:", err)
				continue
			} else {
				if extHeader.AppId != consts.AppIdIoT {
					continue
				}
			}

			iot := []IoTAppData{}
			json.Unmarshal(*dp.Payload.Payload, &iot)

			res := IoTDataResponse{}
			res.DateTime = dp.DateTime.Format("2006-01-02 15:04:05")
			res.Data = &iot

			list = append(list, res)
		}

		val.BufferMutax.Unlock()
	}

	return &list
}

func (conn *Common) GetIoTLastDataByPeer(peerId string) *IoTDataResponse {
	defer conn.CachingBufferMapMutex.Unlock()

	res := IoTDataResponse{}

	conn.CachingBufferMapMutex.Lock()

	val, ok := conn.CachingBufferMap[peerId]

	if ok {
		val.BufferMutax.Lock()

		for i := len(val.DataPackets) - 1; i >= 0; i-- {
			dp := val.DataPackets[i]

			extHeader := BroadcastDataExtensionHeader{}
			err := json.Unmarshal((*dp.Payload.Payload)[:dp.Payload.Header.ReqParams.ExtHeaderLen], &extHeader)
			if err != nil {
				logger.Println(logger.ERROR, "extheader Unmarshal error:", err)
				continue
			} else {
				if extHeader.AppId != consts.AppIdIoT {
					continue
				}
			}

			iot := []IoTAppData{}
			json.Unmarshal(*dp.Payload.Payload, &iot)

			res.DateTime = dp.DateTime.Format("2006-01-02 15:04:05")
			res.Data = &iot

			break
		}

		val.BufferMutax.Unlock()
	}

	return &res
}

func (conn *Common) GetIoTDataListByType(keyword string) *[]*IoTTypeResponse {
	defer conn.CachingBufferMapMutex.Unlock()

	list := make([]*IoTTypeResponse, 0)
	dic := make(map[string]*IoTTypeResponse)

	conn.CachingBufferMapMutex.Lock()

	for pid, val := range conn.CachingBufferMap {
		val.BufferMutax.Lock()

		for _, dp := range val.DataPackets {

			extHeader := BroadcastDataExtensionHeader{}
			err := json.Unmarshal((*dp.Payload.Payload)[:dp.Payload.Header.ReqParams.ExtHeaderLen], &extHeader)
			if err != nil {
				logger.Println(logger.ERROR, "extheader Unmarshal error:", err)
				continue
			} else {
				if extHeader.AppId != consts.AppIdIoT {
					continue
				}
			}

			iot := []IoTAppData{}
			json.Unmarshal(*dp.Payload.Payload, &iot)

			for _, appdata := range iot {
				if appdata.Keyword == keyword {

					data := IoTTypeResponseData{}
					data.DateTime = dp.DateTime.Format("2006-01-02 15:04:05")
					data.Data = appdata.Value

					res, ok := dic[pid]

					if ok {
						res.Data = append(res.Data, data)
					} else {
						res = new(IoTTypeResponse)
						res.PeerId = pid
						res.Data = append(res.Data, data)
						dic[pid] = res
					}
				}
			}
		}

		val.BufferMutax.Unlock()
	}

	for _, tr := range dic {
		list = append(list, tr)
	}

	return &list
}

func (conn *Common) GetIoTLastDataByType(keyword string) *[]*IoTTypeResponse {
	defer conn.CachingBufferMapMutex.Unlock()

	list := make([]*IoTTypeResponse, 0)

	conn.CachingBufferMapMutex.Lock()

	for pid, val := range conn.CachingBufferMap {
		val.BufferMutax.Lock()

	F1:
		for i := len(val.DataPackets) - 1; i >= 0; i-- {
			dp := val.DataPackets[i]

			extHeader := BroadcastDataExtensionHeader{}
			err := json.Unmarshal((*dp.Payload.Payload)[:dp.Payload.Header.ReqParams.ExtHeaderLen], &extHeader)
			if err != nil {
				logger.Println(logger.ERROR, "extheader Unmarshal error:", err)
				continue
			} else {
				if extHeader.AppId != consts.AppIdIoT {
					continue
				}
			}

			iot := []IoTAppData{}
			json.Unmarshal(*dp.Payload.Payload, &iot)

			for i := len(iot) - 1; i >= 0; i-- {
				if iot[i].Keyword == keyword {

					data := IoTTypeResponseData{}
					data.DateTime = dp.DateTime.Format("2006-01-02 15:04:05")
					data.Data = iot[i].Value

					res := new(IoTTypeResponse)
					res.PeerId = pid
					res.Data = append(res.Data, data)

					list = append(list, res)
					break F1
				}
			}
		}

		val.BufferMutax.Unlock()
	}

	return &list
}

func (conn *Common) GetClientConfig() ClientConfig {
	return conn.ClientConfig
}

func (conn *Common) GetTrack(kind string) *webrtc.TrackLocalStaticRTP {
	if kind == "video" {
		return conn.VideoTrack
	} else {
		return conn.AudioTrack
	}
}

func (conn *Common) RemoveCostMapPeer(costmap *[]string, toPeerId string) bool {
	for idx, peerid := range *costmap {
		if peerid == toPeerId {
			if len(*costmap) == 1 {
				*costmap = []string{}
			} else {
				(*costmap)[idx] = (*costmap)[len(*costmap)-1]
				*costmap = (*costmap)[:len(*costmap)-1]
			}

			return true
		}
	}

	return false
}

func (conn *Common) SetOverlayCreationCallback(ovcreate func(ovid string)) {
	conn.overlayCreationCallback = ovcreate
}

func (conn *Common) SetConnectionChangeCallback(connchange func(conn bool)) {
	conn.connectionChangeCallback = connchange
}

func (conn *Common) SetRecvDataCallback(recvdata func(sender string, source string, data string)) {
	conn.RecvDataCallback = recvdata
}

func (conn *Common) SetLog2WebCallback(log2web func(log string)) {
	conn.log2WebCallback = log2web
}

func (conn *Common) SetScanTreeReportCallback(report func(path *[][]string, cseq int)) {
	conn.ReportScanTreeCallback = report
}

func (conn *Common) SetRecvChatCallback(recvchat func(peerId string, msg string)) {
	conn.RecvChatCallback = recvchat
}

func (conn *Common) SetRecvIoTCallback(recviot func(msg string)) {
	conn.RecvIoTCallback = recviot
}

func (conn *Common) SetRecvBlockChainCallback(recvblcn func(msg string)) {
	conn.RecvBlockChainCallback = recvblcn
}

func (conn *Common) SetRecvMediaCallback(recvmedia func(sender string, data *[]byte)) {
	conn.RecvMediaCallback = recvmedia
}

func (conn *Common) sendConnectionChange2Web() {
	conn.connectionChangeCallback(conn.PeerStatus.NumPrimary > 0)
}

func (conn *Common) AddConnectionInfo(position PeerPosition, toPeerId string) {
	switch position {
	case InComingCandidate:
		conn.PeerStatus.NumInCandidate++
		conn.PeerStatus.CostMap.IncomingCandidate = append(conn.PeerStatus.CostMap.IncomingCandidate, toPeerId)
	case OutGoingCandidate:
		conn.PeerStatus.NumOutCandidate++
		conn.PeerStatus.CostMap.OutgoingCandidate = append(conn.PeerStatus.CostMap.OutgoingCandidate, toPeerId)
	case InComingPrimary:
		if conn.RemoveCostMapPeer(&conn.PeerStatus.CostMap.IncomingCandidate, toPeerId) {
			conn.PeerStatus.NumInCandidate--
		}

		conn.PeerStatus.NumPrimary++
		conn.PeerStatus.CostMap.Primary = append(conn.PeerStatus.CostMap.Primary, toPeerId)
	case OutGoingPrimary:
		if conn.RemoveCostMapPeer(&conn.PeerStatus.CostMap.OutgoingCandidate, toPeerId) {
			conn.PeerStatus.NumOutCandidate--
		}

		conn.PeerStatus.NumPrimary++
		conn.PeerStatus.CostMap.Primary = append(conn.PeerStatus.CostMap.Primary, toPeerId)
		conn.HaveOutGoingPrimary = true
	}

	conn.OverlayReport()
	conn.sendConnectionChange2Web()
}

func (conn *Common) DelConnectionInfo(position PeerPosition, toPeerId string) {
	switch position {
	case InComingPrimary, OutGoingPrimary:
		if conn.RemoveCostMapPeer(&conn.PeerStatus.CostMap.Primary, toPeerId) {
			conn.PeerStatus.NumPrimary--

			if position == OutGoingPrimary {
				conn.HaveOutGoingPrimary = false
			}
		}

	case InComingCandidate:
		if conn.RemoveCostMapPeer(&conn.PeerStatus.CostMap.IncomingCandidate, toPeerId) {
			conn.PeerStatus.NumInCandidate--
		}

	case OutGoingCandidate:
		if conn.RemoveCostMapPeer(&conn.PeerStatus.CostMap.OutgoingCandidate, toPeerId) {
			conn.PeerStatus.NumOutCandidate--
		}
	}

	conn.OverlayReport()
	conn.sendConnectionChange2Web()
}

func (conn *Common) RandStringRunes(n int) string {
	b := make([]rune, n)
	for i := range b {
		b[i] = conn.letterRunes[rand.Intn(len(conn.letterRunes))]
	}
	return string(b)
}

func (conn *Common) PeerId() string {
	return conn.PeerInfo.PeerId
}

func (conn *Common) PeerInstanceId() string {
	if conn.peerInstanceId == "" {
		conn.peerInstanceId = conn.PeerInfo.PeerId + ";" + strconv.FormatInt(conn.PeerInfo.InstanceId, 10)
	}
	return conn.peerInstanceId
}

func (conn *Common) IsOwner() bool {
	return conn.OverlayInfo.OwnerId == conn.PeerId()
}

func (conn *Common) SetPeerId(id string) {
	conn.PeerInfo.PeerId = id
}

func (conn *Common) CreateOverlay(hoc *HybridOverlayCreation) *OverlayInfo {
	conn.OverlayInfo.copy(&hoc.Overlay)
	conn.OverlayInfo.copy(conn.HOMP.CreateOverlay(hoc))

	if len(conn.OverlayInfo.OverlayId) <= 0 {
		conn.log2WebCallback("Overlay created. Id: " + conn.OverlayInfo.OverlayId)
		conn.overlayCreationCallback(conn.OverlayInfo.OverlayId)
	} else {
		conn.log2WebCallback("Failed to create Overlay.")
	}

	return &conn.OverlayInfo
}

func (conn *Common) OverlayJoinBy(hoj *HybridOverlayJoin, recovery bool) *HybridOverlayJoinResponseOverlay {

	res := conn.HOMP.OverlayJoin(hoj, recovery)

	if res == nil {
		conn.log2WebCallback("Failed to join Overlay.")
		return nil
	}

	if len(res.Overlay.OverlayId) <= 0 {
		conn.log2WebCallback("Failed to join Overlay.")
		return nil
	}

	conn.log2WebCallback("Join Overlay.")

	if !recovery {

		conn.OverlayInfo.copy(&res.Overlay)
		conn.PeerInfo.TicketId = res.Peer.TicketId

		if res.Peer.Expires > 0 {
			conn.PeerConfig.Expires = res.Peer.Expires
			conn.joinTicker = time.NewTicker(time.Millisecond * time.Duration(float32(conn.PeerConfig.Expires)*0.8) * 1000)
			go func() {
				for range conn.joinTicker.C {

					if conn.LeaveOverlay {
						break
					}

					hor := HybridOverlayRefresh{}
					hor.Overlay.OverlayId = conn.OverlayInfo.OverlayId
					hor.Peer.PeerId = conn.PeerId()
					hor.Peer.InstanceId = conn.PeerInfo.InstanceId
					hor.Peer.Address = conn.PeerInfo.Address
					hor.Peer.Auth = conn.PeerInfo.Auth
					conn.HOMP.OverlayRefresh(&hor)
				}
			}()
		}
	}

	return &res.Overlay
}

func (conn *Common) OverlayJoin(recovery bool) *HybridOverlayJoinResponseOverlay {
	hoj := new(HybridOverlayJoin)
	hoj.Overlay.OverlayId = conn.OverlayInfo.OverlayId
	hoj.Overlay.Type = conn.OverlayInfo.Type
	hoj.Overlay.SubType = conn.OverlayInfo.SubType
	hoj.Overlay.Auth = &conn.OverlayInfo.Auth
	hoj.Peer.PeerId = conn.PeerId()
	hoj.Peer.InstanceId = conn.PeerInfo.InstanceId
	hoj.Peer.Address = conn.PeerInfo.Address
	hoj.Peer.Auth = conn.PeerInfo.Auth
	hoj.Peer.Expires = &conn.PeerConfig.Expires
	hoj.Peer.TicketId = &conn.PeerInfo.TicketId

	return conn.OverlayJoinBy(hoj, recovery)
}

func (conn *Common) OverlayModification(hom *HybridOverlayModification) *HybridOverlayModificationOverlay {
	return conn.HOMP.OverlayModification(hom)
}

func (conn *Common) OverlayRemove(hom *HybridOverlayRemoval) *HybridOverlayRemovalResponseOverlay {
	return conn.HOMP.OverlayRemoval(hom)
}

func (conn *Common) OverlayRefresh(hor *HybridOverlayRefresh) *HybridOverlayRefreshResponse {
	return conn.HOMP.OverlayRefresh(hor)
}

func (conn *Common) OverlayReport() {
	conn.OverlayReportBy(conn.OverlayInfo.OverlayId)
}

func (conn *Common) OverlayReportBy(overlayId string) *HybridOverlayReportOverlay {
	hor := new(HybridOverlayReport)
	hor.Overlay.OverlayId = overlayId
	hor.Peer.PeerId = conn.PeerId()
	hor.Peer.InstanceId = conn.PeerInfo.InstanceId
	hor.Status = conn.PeerStatus
	hor.Peer.Auth = conn.PeerInfo.Auth

	return conn.HOMP.OverlayReport(hor)
}

func (conn *Common) OverlayQuery(ovid *string, title *string, desc *string) bool {
	hoq := conn.HOMP.QueryOverlay(ovid, title, desc)

	if hoq == nil || len(*hoq) <= 0 {

		conn.log2WebCallback("Failed to query Overlay.")

		return false
	}

	conn.log2WebCallback("Query Overlay.")

	conn.OverlayInfo.copy(&(*hoq)[0].Overlay)

	return true
}

func (conn *Common) OverlayLeave() {
	conn.OverlayLeaveBy(conn.OverlayInfo.OverlayId)
}

func (conn *Common) OverlayLeaveBy(overlayId string) *HybridOverlayLeaveResponse {
	hol := new(HybridOverlayLeave)
	hol.Overlay.OverlayId = overlayId
	hol.Overlay.Auth = &conn.OverlayInfo.Auth
	hol.Peer.PeerId = conn.PeerId()
	hol.Peer.InstanceId = conn.PeerInfo.InstanceId
	hol.Peer.Auth = &conn.PeerInfo.Auth

	res := conn.HOMP.OverlayLeave(hol)

	conn.log2WebCallback("Leave Overlay.")

	logger.Println(logger.INFO, "Overlay leave response:", res)

	return res
}

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

package main

import (
	"consts"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"logger"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"github.com/pion/rtcp"
	"github.com/pion/webrtc/v3"
)

const (
	rtcpPLIInterval = time.Second * 3
)

type PeerClient struct {
	webRtcConfig   webrtc.Configuration
	peerConnection *webrtc.PeerConnection
	dataChannel    *webrtc.DataChannel
	trackFunc      func(kind string, track *webrtc.TrackLocalStaticRTP)
	Vtrack         *webrtc.TrackLocalStaticRTP
	Atrack         *webrtc.TrackLocalStaticRTP

	wsconn *websocket.Conn

	candidatesMux     sync.Mutex
	pendingCandidates []*webrtc.ICECandidateInit

	remoteCandidatesMux     sync.Mutex
	remotePendingCandidates []*webrtc.ICECandidateInit

	ScanTreeCSeq int
}

func NewPeerClient(trackFunc func(kind string, track *webrtc.TrackLocalStaticRTP), conn *websocket.Conn) *PeerClient {
	client := new(PeerClient)
	client.webRtcConfig = webrtc.Configuration{
		ICEServers: []webrtc.ICEServer{
			{
				URLs: []string{"stun:stun.l.google.com:19302"},
			},
		},
	}

	client.trackFunc = trackFunc
	client.wsconn = conn

	client.ScanTreeCSeq = 0

	return client
}

func (client *PeerClient) ReceiveOffer(sdp *webrtc.SessionDescription, addTrack bool) *webrtc.SessionDescription {
	peerConnection, err := webrtc.NewPeerConnection(client.webRtcConfig)

	if err != nil {
		panic(err)
	}

	client.peerConnection = peerConnection

	client.peerConnection.OnConnectionStateChange(func(s webrtc.PeerConnectionState) {
		logger.Println(logger.WORK, "PeerClient Connection State has changed:", s.String())
	})

	if addTrack {
		if client.Vtrack != nil {
			client.peerConnection.AddTrack(client.Vtrack)
		}

		if client.Atrack != nil {
			client.peerConnection.AddTrack(client.Atrack)
		}

	} else {
		client.peerConnection.OnTrack(func(tr *webrtc.TrackRemote, r *webrtc.RTPReceiver) {
			fmt.Println("OnTrack!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

			go func() {
				ticker := time.NewTicker(rtcpPLIInterval)
				for range ticker.C {
					if rtcpSendErr := peerConnection.WriteRTCP([]rtcp.Packet{&rtcp.PictureLossIndication{MediaSSRC: uint32(tr.SSRC())}}); rtcpSendErr != nil {
						fmt.Println(rtcpSendErr)
						return
					}
				}
			}()

			localTrack, newTrackErr := webrtc.NewTrackLocalStaticRTP(tr.Codec().RTPCodecCapability, "video", "pion")
			if newTrackErr != nil {
				panic(newTrackErr)
			}

			if tr.Kind() == webrtc.RTPCodecTypeVideo {
				client.trackFunc("video", localTrack)
			} else if tr.Kind() == webrtc.RTPCodecTypeAudio {
				client.trackFunc("audio", localTrack)
			}
			rtpBuf := make([]byte, 1400)
			for {
				i, _, readErr := tr.Read(rtpBuf)
				if readErr != nil {
					//panic(readErr)
					return
				}

				// ErrClosedPipe means we don't have any subscribers, this is ok if no peers have connected yet
				if _, err = localTrack.Write(rtpBuf[:i]); err != nil && !errors.Is(err, io.ErrClosedPipe) {
					//panic(err)
					return
				}
			}
		})
	}

	client.peerConnection.OnICECandidate(func(ice *webrtc.ICECandidate) {
		if ice == nil {
			return
		}

		logger.Println(logger.INFO, "!!!! client.peerConnection.OnICECandidate", ice)

		client.remoteCandidatesMux.Lock()
		defer client.remoteCandidatesMux.Unlock()

		if client.peerConnection == nil || client.peerConnection.RemoteDescription() == nil {
			iceinit := ice.ToJSON()
			client.remotePendingCandidates = append(client.remotePendingCandidates, &iceinit)
		} else {
			res := struct {
				Type string                  `json:"type"`
				ICE  webrtc.ICECandidateInit `json:"ice"`
			}{}

			res.Type = consts.TypeICE
			res.ICE = ice.ToJSON()
			buf, _ := json.Marshal(res)
			client.wsconn.WriteMessage(websocket.TextMessage, buf)
		}

	})

	client.peerConnection.OnDataChannel(func(d *webrtc.DataChannel) {
		client.dataChannel = d

		client.dataChannel.OnOpen(func() {
			client.OnDataChannelOpen()
		})

		client.dataChannel.OnMessage(func(msg webrtc.DataChannelMessage) {
			client.OnDataChannelMessage(msg)
		})
	})

	err = client.peerConnection.SetRemoteDescription(*sdp)
	if err != nil {
		panic(err)
	}

	answer, err := client.peerConnection.CreateAnswer(nil)
	if err != nil {
		panic(err)
	}

	err = client.peerConnection.SetLocalDescription(answer)
	if err != nil {
		panic(err)
	}

	client.candidatesMux.Lock()
	for _, c := range client.pendingCandidates {

		onICECandidateErr := client.peerConnection.AddICECandidate(*c)
		if onICECandidateErr != nil {
			panic(onICECandidateErr)
		}
	}
	client.candidatesMux.Unlock()

	return &answer
}

func (client *PeerClient) AddIceCandidate(ice *webrtc.ICECandidateInit) {

	client.candidatesMux.Lock()
	defer client.candidatesMux.Unlock()

	if client.peerConnection == nil || client.peerConnection.RemoteDescription() == nil {
		client.pendingCandidates = append(client.pendingCandidates, ice)
	} else {
		err := client.peerConnection.AddICECandidate(*ice)
		if err != nil {
			logger.Println(logger.ERROR, "!!!!!! add icecandi to webclient:", err)
		}
	}
}

func (client *PeerClient) SendRemoteIceCandidate() {
	client.remoteCandidatesMux.Lock()
	for _, c := range client.remotePendingCandidates {

		buf, _ := json.Marshal(c)
		client.wsconn.WriteMessage(websocket.TextMessage, buf)
	}
	client.remoteCandidatesMux.Unlock()
}

func (client *PeerClient) OnDataChannelOpen() {
	fmt.Printf("Data channel '%s'-'%d' open.\n", client.dataChannel.Label(), client.dataChannel.ID())

	//*self.connectChan <- true
}

func (client *PeerClient) OnDataChannelMessage(msg webrtc.DataChannelMessage) {
	fmt.Printf("Message from DataChannel '%s': '%s'\n", client.dataChannel.Label(), string(msg.Data))
}

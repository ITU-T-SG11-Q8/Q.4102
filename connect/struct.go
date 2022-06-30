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

package connect

import (
	"encoding/json"
	"os"

	pwebrtc "github.com/pion/webrtc/v3"
)

type Config struct {
	SignalingServerAddr string `json:"SIGNALING_SERVER_ADDR"`
}

func GetConfig() Config {
	config := Config{}

	file, _ := os.ReadFile("config.json")
	_ = json.Unmarshal([]byte(file), &config)

	return config
}

type PeerConfig struct {
	PeerEstabMaxCount    int `json:"PEER_ESTAB_MAX_COUNT"`
	PeerEstabTimeout     int `json:"PEER_ESTAB_TIMEOUT"`
	MaxPrimaryConnection int `json:"MAX_PRIMARY_CONNECTION"`
	MaxIncomingCandidate int `json:"MAX_INCOMING_CANDIDATE"`
	MaxOutgoingCandidate int `json:"MAX_OUTGOING_CANDIDATE"`
	HelloPeerTTL         int `json:"HELLO_PEER_TTL"`
	EstabPeerTimeout     int `json:"ESTAB_PEER_TIMEOUT"`
	EstabPeerMaxCount    int `json:"ESTAB_PEER_MAX_COUNT"`
	ProbePeerTimeout     int `json:"PROBE_PEER_TIMEOUT"`
}

type OverlayInfo struct {
	OverlayId   string
	Title       string
	Type        string
	SubType     string
	OwnerId     string
	Expires     int
	Status      OverlayStatus
	Description string
	Auth        OverlayAuth
}

type TransPolicy struct {
	RateControlQuantity int
	RateControlBitrate  int
	TransmissionControl string
	AuthList            []string
}

type PeerInfo struct {
	PeerId  string
	Address string
	Auth    PeerAuth
}

type OverlayAuth struct {
}

type OverlayStatus struct {
	NumPeers     int
	PeerInfoList []PeerInfo
}

type PeerStatus struct {
	NumPrimary      int
	NumOutCandidate int
	NumInCandidate  int
	CostMap         interface{}
}

type PeerAuth struct {
	Password string
}

type PeerBuffermap struct {
	Buffermap    interface{}
	SourcePeerId string
	Sequence     []int
}

type RTCSessionDescription struct {
	Fromid       string                     `json:"fromid"`
	Toid         string                     `json:"toid"`
	Fromticketid string                     `json:"fromticketid"`
	Sdp          pwebrtc.SessionDescription `json:"sdp"`
	Type         string                     `json:"type"`
}

type RTCIceCandidate struct {
	Fromid    string `json:"fromid"`
	Toid      string `json:"toid"`
	Candidate string `json:"candidate"`
	Type      string `json:"type"`
}

type TypeGetter struct {
	Type string `json:"type"`
}

type PPMessage struct {
	Ver     byte
	Type    byte
	Length  int16
	Header  struct{}
	Content []byte
}

func GetPPMessage() *PPMessage {
	pp := new(PPMessage)
	pp.Ver = 0x01
	pp.Type = 0x10

	return pp
}

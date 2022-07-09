module hp2p.go.peer

go 1.17

require (
	connect v0.0.0
	consts v0.0.0
	github.com/gorilla/websocket v1.4.2
	github.com/graphql-go/graphql v0.8.0
	github.com/pion/rtcp v1.2.6
	github.com/pion/webrtc/v3 v3.0.32
	logger v0.0.0
)

require (
	github.com/go-resty/resty/v2 v2.7.0 // indirect
	github.com/google/uuid v1.2.0 // indirect
	github.com/pion/datachannel v1.4.21 // indirect
	github.com/pion/dtls/v2 v2.0.9 // indirect
	github.com/pion/ice/v2 v2.1.10 // indirect
	github.com/pion/interceptor v0.0.13 // indirect
	github.com/pion/logging v0.2.2 // indirect
	github.com/pion/mdns v0.0.5 // indirect
	github.com/pion/randutil v0.1.0 // indirect
	github.com/pion/rtp v1.6.5 // indirect
	github.com/pion/sctp v1.7.12 // indirect
	github.com/pion/sdp/v3 v3.0.4 // indirect
	github.com/pion/srtp/v2 v2.0.2 // indirect
	github.com/pion/stun v0.3.5 // indirect
	github.com/pion/transport v0.12.3 // indirect
	github.com/pion/turn/v2 v2.0.5 // indirect
	github.com/pion/udp v0.1.1 // indirect
	github.com/pkg/errors v0.9.1 // indirect
	golang.org/x/crypto v0.0.0-20210322153248-0c34fe9e7dc2 // indirect
	golang.org/x/net v0.0.0-20211029224645-99673261e6eb // indirect
	golang.org/x/sys v0.0.0-20210423082822-04245dca01da // indirect
	golang.org/x/xerrors v0.0.0-20200804184101-5ec99f83aff1 // indirect
)

replace connect => ./connect

replace logger => ./logger

replace consts => ./consts

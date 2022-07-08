module hp2p.go/connect

go 1.16

require (
    github.com/gorilla/websocket v1.4.2
    github.com/pion/webrtc/v3 v3.0.32 // indirect
    consts v0.0.0
)

replace logger => ../logger

replace consts => ../consts
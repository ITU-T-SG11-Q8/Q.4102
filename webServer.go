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
	"connect"
	"consts"
	"encoding/json"
	"log"
	"logger"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"sync"

	"github.com/gorilla/websocket"
	"github.com/pion/webrtc/v3"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

type HTTPServer struct {
	vtrack *webrtc.TrackLocalStaticRTP
	atrack *webrtc.TrackLocalStaticRTP

	OnTrack      func(toPeerId string, kind string, track *webrtc.TrackLocalStaticRTP)
	GetTrack     func(kind string) *webrtc.TrackLocalStaticRTP
	SendScanTree func() int
	SendData     func(data *[]byte, appId string, candidatePath bool)

	IsOwner func() bool
	PeerId  string

	wsmap map[*websocket.Conn]*PeerClient

	wsMux sync.Mutex

	webHandler *WebHandler
	connectObj *connect.Connect
	wsPort     int

	scanTreeChan chan interface{}
}

type Path struct {
	Id       string `json:"id"`
	TicketId string `json:"ticket-id"`
	Address  string `json:"address"`
}

type Chat struct {
	Type    string `json:"type"`
	Source  string `json:"source"`
	Message string `json:"message"`
}

type Data struct {
	Type string `json:"type"`
	Data string `json:"data"`
}

type ScanTreeData struct {
	Type string     `json:"type"`
	Data [][]string `json:"data"`
}

type staticHandler struct {
	http.Handler
}

type ReceivedData struct {
	Type    string `json:"type"`
	Sender  string `json:"sender"`
	Source  string `json:"source"`
	Message string `json:"message"`
}

type Sdp struct {
	Type string                     `json:"type"`
	Sdp  *webrtc.SessionDescription `json:"sdp"`
}

type Ice struct {
	Type string                   `json:"type"`
	ICE  *webrtc.ICECandidateInit `json:"ice"`
}

func (h *staticHandler) ServeHTTP(w http.ResponseWriter, req *http.Request) {
	localPath := "webClient" + req.URL.Path

	if localPath == "webClient/" ||
		localPath == "webClient/iot" ||
		localPath == "webClient/network" ||
		localPath == "webClient/media" {
		localPath = "webClient/index.html"
	}

	content, err := os.ReadFile(localPath)
	if err != nil {
		w.WriteHeader(404)
		w.Write([]byte(http.StatusText(404)))
		return
	}

	contentType := getContentType(localPath)
	w.Header().Add("Content-Type", contentType)
	w.Write(content)
}

func getContentType(localPath string) string {
	var contentType string
	ext := filepath.Ext(localPath)

	switch ext {
	case ".html":
		contentType = "text/html"
	case ".css":
		contentType = "text/css"
	case ".js":
		contentType = "application/javascript"
	case ".png":
		contentType = "image/png"
	case ".jpg":
		contentType = "image/jpeg"
	case ".woff", ".woff2", ".ttf":
		contentType = "font/opentype"
	default:
		contentType = "text/plain"
	}

	return contentType
}

func NewHttpServer(peerId string) *HTTPServer {
	server := new(HTTPServer)
	server.vtrack = nil
	server.atrack = nil
	server.wsmap = make(map[*websocket.Conn]*PeerClient)
	server.PeerId = peerId
	server.scanTreeChan = nil

	return server
}

func (server *HTTPServer) SetScanTreeChan(scanTreeChan *chan interface{}) {
	if scanTreeChan != nil {
		server.scanTreeChan = *scanTreeChan
	} else {
		server.scanTreeChan = nil
	}
}

func (server *HTTPServer) setTrack(kind string, track *webrtc.TrackLocalStaticRTP) {
	if kind == "video" {
		server.vtrack = track
	} else if kind == "audio" {
		server.atrack = track
	}

	server.OnTrack("", kind, track)
}

func (server *HTTPServer) SetConnect(conn *connect.Connect) {
	server.connectObj = conn

	(*conn).SetOverlayCreationCallback(server.OverlayCreation)
	(*conn).SetScanTreeReportCallback(server.RecvScanTree)
	(*conn).SetRecvChatCallback(server.RecvChat)
	(*conn).SetConnectionChangeCallback(server.ConnectionChange)
	(*conn).SetRecvDataCallback(server.RecvData)
	(*conn).SetLog2WebCallback(server.Log2Web)
	(*conn).SetRecvIoTCallback(server.RecvIoT)

	server.SetHandler(NewWebHandler(conn))
	server.OnTrack = (*conn).OnTrack
	server.GetTrack = (*conn).GetTrack
	server.SendScanTree = (*conn).SendScanTree
	server.SendData = (*conn).SendData

	server.SetApiHandler(NewApiHandler(conn))
}

func (server *HTTPServer) SetHandler(handler *WebHandler) {
	server.webHandler = handler
	handler.websocketPort = server.wsPort

	http.HandleFunc("/api/InitData", server.webHandler.InitDataHandler)
	http.HandleFunc("/api/Mobile/IoT", server.webHandler.IoTHandler)
	http.HandleFunc("/api/Mobile/Network", server.webHandler.NetworkHandler)
}

func (server *HTTPServer) SetApiHandler(handler *ApiHandler) {
	handler.SetScanTreeChan = server.SetScanTreeChan
	handler.SendChat = server.SendChat
	http.HandleFunc("/api/graphql", handler.HandleApi)
}

func (server *HTTPServer) Start(port int) {
	go func() {
		listener, err := net.Listen("tcp", ":"+strconv.Itoa(port))
		if err != nil {
			panic(err)
		}

		//fs := http.FileServer(http.Dir("webClient"))
		//http.Handle("/", fs)
		//http.Handle("/client/", http.StripPrefix("/client/", fs))
		//http.Handle("/client/", new(staticHandler))
		http.Handle("/", new(staticHandler))
		server.wsPort = listener.Addr().(*net.TCPAddr).Port
		logger.Println(logger.WORK, "HTTP Server start with :", listener.Addr())

		logger.Println(logger.WORK, "")

		panic(http.ServeTLS(listener, nil, "private.crt", "temp.key"))

	}()

	http.HandleFunc("/ws", server.wsHandler)
}

func (server *HTTPServer) wsBroadcast(msg []byte) {
	for key := range server.wsmap {
		if err := server.wsSend(key, msg); err != nil {
			log.Printf("conn.WriteMessage: %v", err)
			continue
		}
	}
}

func (server *HTTPServer) wsSend(conn *websocket.Conn, data []byte) error {
	server.wsMux.Lock()
	defer server.wsMux.Unlock()

	return conn.WriteMessage(websocket.TextMessage, data)
}

func (server *HTTPServer) wsHandler(w http.ResponseWriter, r *http.Request) {
	var crsupgrader = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool { return true },
	}
	conn, err := crsupgrader.Upgrade(w, r, nil)
	defer func() {
		logger.Println(logger.WORK, "WebClient disconnected.")
		peer := server.wsmap[conn]
		if peer != nil && peer.peerConnection != nil {
			if peer.peerConnection.ConnectionState() > webrtc.PeerConnectionStateDisconnected {
				peer.peerConnection.Close()
			}
		}
		delete(server.wsmap, conn)
		conn.Close()
	}()

	if err != nil {
		log.Printf("upgrader.Upgrade: %v", err)
		return
	}

	var client *PeerClient = nil

	if server.wsmap[conn] == nil {
		client = NewPeerClient(server.setTrack, conn)
		server.wsmap[conn] = client
	} else {
		client = server.wsmap[conn]
	}

	//server.wsSend(conn, []byte(`{"Owner":`+strconv.FormatBool(server.IsOwner)+`,"PeerId":"`+server.PeerId+`"}`))

	for {
		/*messageType*/ _, p, err := conn.ReadMessage()
		if err != nil {
			logger.Println(logger.ERROR, "conn.ReadMessage error:", err)
			return
		}

		msgtype := struct {
			Type string `json:"type"`
		}{}

		json.Unmarshal(p, &msgtype)

		if msgtype.Type == consts.TypeScanTree {
			client.ScanTreeCSeq = server.SendScanTree()
			continue
		} else if msgtype.Type == consts.TypeChat {
			server.wsBroadcast(p)

			chat := Chat{}
			json.Unmarshal(p, &chat)

			buf := []byte(chat.Message)

			go server.SendData(&buf, consts.AppIdChat, false)

			continue
		} else if msgtype.Type == consts.TypeSendData {
			data := Data{}
			json.Unmarshal(p, &data)

			server.RecvData(server.PeerId, server.PeerId, data.Data)

			buf := []byte(data.Data)

			go server.SendData(&buf, consts.AppIdData, false)
		} else if msgtype.Type == consts.TypeSdp {
			sdp := Sdp{}
			json.Unmarshal(p, &sdp)

			var answer *webrtc.SessionDescription = nil

			if server.IsOwner() {
				answer = client.ReceiveOffer(sdp.Sdp, false)
			} else {
				server.vtrack = server.GetTrack("video")
				server.atrack = server.GetTrack("audio")

				if server.vtrack == nil {
					server.wsSend(conn, []byte(`{"type":"error","message":"Media not found."}`))
					return
				}

				client.Vtrack = server.vtrack
				client.Atrack = server.atrack

				answer = client.ReceiveOffer(sdp.Sdp, true)
			}

			res := Sdp{}

			res.Type = consts.TypeSdp
			res.Sdp = answer

			buf, _ := json.Marshal(res)
			server.wsSend(conn, buf)

			client.SendRemoteIceCandidate()
		} else if msgtype.Type == consts.TypeICE {
			ice := Ice{}
			json.Unmarshal(p, &ice)
			client.AddIceCandidate(ice.ICE)
		}
	}
}

func (server *HTTPServer) SendChat(msg string) {
	chat := Chat{}
	chat.Message = msg
	chat.Source = server.PeerId
	chat.Type = consts.AppIdChat

	wbuf, _ := json.Marshal(chat)
	server.wsBroadcast(wbuf)

	buf := []byte(chat.Message)
	go server.SendData(&buf, consts.AppIdChat, false)
}

func (server *HTTPServer) OverlayCreation(overlayId string) {
	ovcre := struct {
		Type      string `json:"type"`
		OverlayId string `json:"overlayId"`
	}{}
	ovcre.Type = consts.TypeOverlayCreation
	ovcre.OverlayId = overlayId

	buf, _ := json.Marshal(ovcre)

	server.wsBroadcast(buf)
}

func (server *HTTPServer) RecvScanTree(path *[][]string, cseq int) {
	logger.Println(logger.INFO, "RecvScanTree!!! :", path)

	res := ScanTreeData{}
	res.Type = consts.TypeScanTree

	res.Data = append(res.Data, *path...)
	buf, _ := json.Marshal(res)

	for _, client := range server.wsmap {
		if client.ScanTreeCSeq == cseq {
			server.wsSend(client.wsconn, buf)
			break
		}
	}

	if server.scanTreeChan != nil {
		dat := connect.ApiScanTreeData{}
		dat.CSeq = cseq
		dat.Data = path
		server.scanTreeChan <- &dat
	}
}

func (server *HTTPServer) RecvChat(peerId string, msg string) {
	chat := Chat{}
	chat.Type = consts.TypeChat
	chat.Source = peerId
	chat.Message = msg

	buf, _ := json.Marshal(chat)

	server.wsBroadcast(buf)
}

func (server *HTTPServer) RecvData(sender string, source string, msg string) {
	data := ReceivedData{}
	data.Type = consts.TypeReceivedData
	data.Sender = sender
	data.Source = source
	data.Message = msg

	buf, _ := json.Marshal(data)

	server.wsBroadcast(buf)
}

func (server *HTTPServer) RecvIoT(msg string) {
	data := Data{}
	data.Type = consts.TypeIoT
	data.Data = msg

	buf, _ := json.Marshal(data)

	server.wsBroadcast(buf)
}

func (server *HTTPServer) ConnectionChange(conn bool) {
	msg := struct {
		Type          string `json:"type"`
		HasConnection bool   `json:"hasConnection"`
	}{}

	msg.Type = consts.TypeConnectionChange
	msg.HasConnection = conn

	buf, _ := json.Marshal(msg)

	server.wsBroadcast(buf)
}

func (server *HTTPServer) Log2Web(log string) {
	msg := struct {
		Type    string `json:"type"`
		Message string `json:"message"`
	}{}

	msg.Type = consts.TypeConnectionChange
	msg.Message = log

	buf, _ := json.Marshal(msg)

	server.wsBroadcast(buf)
}

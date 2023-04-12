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
	"logger"
	"net/http"
)

type InitData struct {
	WEB_SOCKET_PORT    int
	PEER_ID            string
	TICKET_ID          int
	OVERLAY_ID         string
	IS_OWNER           bool
	HAS_CONNECTION     bool
	HAS_UDP_CONNECTION bool
}

type IoTRequest struct {
	Query   string `json:"query"`
	Keyword string `json:"keyword"`
}

type WebHandler struct {
	connectObj    *connect.Connect
	websocketPort int
	udpConnection bool
}

func NewWebHandler(conn *connect.Connect) *WebHandler {
	handler := new(WebHandler)
	handler.udpConnection = false
	handler.connectObj = conn

	return handler
}

func (handler *WebHandler) InitDataHandler(rw http.ResponseWriter, r *http.Request) {
	encoder := json.NewEncoder(rw)
	data := InitData{}
	data.WEB_SOCKET_PORT = handler.websocketPort
	data.PEER_ID = (*handler.connectObj).PeerId()
	data.TICKET_ID = (*handler.connectObj).PeerInfo().TicketId
	data.OVERLAY_ID = (*handler.connectObj).OverlayInfo().OverlayId
	data.IS_OWNER = (*handler.connectObj).IsOwner()
	data.HAS_CONNECTION = (*handler.connectObj).HasConnection()
	data.HAS_UDP_CONNECTION = (*handler.connectObj).IsUDPConnection()

	rw.Header().Set("Content-Type", "application/json")
	err := encoder.Encode(data)
	if err != nil {
		logger.Println(logger.ERROR, "HTTP Server encode error :", err)
	}

	//rw.WriteHeader(http.StatusOK)
}

func (handler *WebHandler) IoTHandler(rw http.ResponseWriter, r *http.Request) {
	encoder := json.NewEncoder(rw)
	decoder := json.NewDecoder(r.Body)
	req := IoTRequest{}
	decoder.Decode(&req)

	var response interface{}

	switch req.Query {
	case consts.IoTPeerList:
		logger.Println(logger.INFO, "peerlist data request")
		res := struct {
			Peerlist *[]string `json:"peerlist"`
		}{}

		res.Peerlist = (*handler.connectObj).GetIoTPeerList()

		response = res

	case consts.IoTDataList:
		peerId := req.Keyword
		logger.Println(logger.INFO, peerId, "data request")

		res := (*handler.connectObj).GetIoTDataListByPeer(peerId)

		response = res

	case consts.IoTDataLast:
		peerId := req.Keyword
		logger.Println(logger.INFO, peerId, "last data request")

		res := (*handler.connectObj).GetIoTLastDataByPeer(peerId)

		response = res

	case consts.IoTTypeList:
		dataType := req.Keyword
		logger.Println(logger.INFO, dataType, "data request")

		res := (*handler.connectObj).GetIoTDataListByType(dataType)

		response = res

	case consts.IoTTypeLast:
		dataType := req.Keyword
		logger.Println(logger.INFO, dataType, "last data request")

		response = (*handler.connectObj).GetIoTLastDataByType(dataType)

		//response = res
	}

	rw.Header().Set("Content-Type", "application/json")
	err := encoder.Encode(response)
	if err != nil {
		logger.Println(logger.ERROR, "HTTP Server encode error :", err)
	}
}

func (handler *WebHandler) NetworkHandler(rw http.ResponseWriter, r *http.Request) {
	encoder := json.NewEncoder(rw)
	data := (*handler.connectObj).ConnectionInfo()

	rw.Header().Set("Content-Type", "application/json")
	err := encoder.Encode(data)
	if err != nil {
		logger.Println(logger.ERROR, "HTTP Server encode error :", err)
	}
}

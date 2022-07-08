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
	"encoding/binary"
	"encoding/json"
	"logger"
	"net"
	"strconv"
)

type UDPServer struct {
	IoTDataCallback        func(data *connect.IoTData)
	BlockChainDataCallback func(data *connect.BlockChainData)
	MediaDataCallback      func(data *connect.MediaAppData)

	blockChainNode net.Addr
	mediaNode      net.Addr
	udpConn        *net.PacketConn

	peerId string
}

func (udp *UDPServer) start(port int) {

	udp.blockChainNode = nil
	udp.mediaNode = nil
	udp.udpConn = nil

	server, err := net.ListenPacket("udp", ":"+strconv.Itoa(port))
	if err != nil {
		logger.Println(logger.ERROR, "Failed to Start UDP Server.")
		return
	}

	udp.udpConn = &server

	logger.Println(logger.WORK, "UDP Server start with :", server.LocalAddr().String())

	go func() {
		for {
			buf := make([]byte, 4)
			n, clientAddress, err := server.ReadFrom(buf)
			if n != 4 {
				logger.Println(logger.INFO, "buffer size is not 4...")
			} else {
				len := binary.BigEndian.Uint32(buf)

				buf := make([]byte, len)
				n /*clientAddress*/, _, err := server.ReadFrom(buf)
				if n == 0 {
					logger.Println(logger.INFO, "buffer size is 0...")
				} else if n > 0 {
					iotdata := connect.IoTData{}

					json.Unmarshal(buf[:n], &iotdata)

					if iotdata.AppId == consts.AppIdIoT {
						udp.IoTDataCallback(&iotdata)
					} else if iotdata.AppId == consts.AppIdBlockChain {
						bcData := connect.BlockChainData{}
						json.Unmarshal(buf[:n], &bcData)
						bcData.AppData.Sender = udp.peerId
						udp.BlockChainDataCallback(&bcData)
					} else if iotdata.AppId == consts.AppIdBlockChainRegister {
						udp.blockChainNode = clientAddress
						logger.Println(logger.WORK, "BlockChain Node connected.")
					} else if iotdata.AppId == consts.AppIdMedia {
						mediadata := connect.MediaData{}
						json.Unmarshal(buf[:n], &mediadata)
						buf := make([]byte, mediadata.Length)
						n, _, err := server.ReadFrom(buf)

						if err != nil {
							logger.Println(logger.ERROR, "mediadata receive error:", err)
						} else if n == mediadata.Length {
							mdata := connect.MediaAppData{}
							mdata.AppId = consts.AppIdMedia
							mdata.AppData = &buf

							udp.MediaDataCallback(&mdata)
						}
					} else if iotdata.AppId == consts.AppIdMediaRegister {
						udp.mediaNode = clientAddress
						logger.Println(logger.WORK, "Media Node connected.")
					}
				}

				if err != nil {
					logger.Println(logger.ERROR, "UDP Recv error :", err)
				}
			}

			if err != nil {
				logger.Println(logger.ERROR, "UDP Recv error :", err)
			}

			/*_, err = server.WriteTo(buf[:n], clientAddress)
			  if err != nil {
			      logger.Println(logger.ERROR, "UDP send error :", err)
			  }*/
		}
	}()
}

func (udp *UDPServer) RecvBlockChain(data string) {
	if udp.udpConn != nil && udp.blockChainNode != nil {
		bcData := connect.BlockChainAppData{}
		json.Unmarshal([]byte(data), &bcData)

		if len(bcData.Receiver) == 0 || bcData.Receiver == udp.peerId {
			b := make([]byte, 4)
			lenlen := len(data)
			binary.BigEndian.PutUint32(b, uint32(lenlen))
			(*udp.udpConn).WriteTo(b, udp.blockChainNode)
			(*udp.udpConn).WriteTo([]byte(data), udp.blockChainNode)
		}
	}
}

func (udp *UDPServer) RecvMedia(sender string, data *[]byte) {
	if udp.udpConn != nil && udp.mediaNode != nil {
		mdata := connect.MediaData{}
		mdata.AppId = sender
		mdata.Length = len(*data)

		jdata, err := json.Marshal(mdata)
		if err != nil {
			logger.Println(logger.ERROR, "Media data marshal error:", err)
			return
		}

		b := make([]byte, 4)
		lenlen := len(jdata)
		binary.BigEndian.PutUint32(b, uint32(lenlen))
		(*udp.udpConn).WriteTo(b, udp.mediaNode)
		(*udp.udpConn).WriteTo(jdata, udp.mediaNode)
		(*udp.udpConn).WriteTo(*data, udp.mediaNode)
	}
}

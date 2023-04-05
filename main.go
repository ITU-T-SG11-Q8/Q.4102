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
	"flag"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"time"

	"connect"
	"connect/webrtc"
	"logger"
)

func main() {
	peerId := flag.String("id", "", "Peer ID")
	//toPeerId := flag.String("connect", "", "Peer ID to connect")
	title := flag.String("t", "", "Title")
	desc := flag.String("d", "", "Description")
	expires := flag.Int("e", 3600, "Overlay Expires")
	create := flag.Bool("c", false, "Create Overlay")
	join := flag.Bool("j", false, "Join Overlay")
	hbInterval := flag.Int("hi", 10, "Heartbeat interval")
	hbTimeout := flag.Int("ht", 15, "Heartbeat timeout")
	authType := flag.String("a", "open", "Auth type [open|closed]")
	adminKey := flag.String("ak", "admin", "Admin key")
	accessKey := flag.String("ac", "1234", "Access key")
	peerList := flag.String("pl", "", "Peer list [peer1,peer2,...]")
	mnCache := flag.Int("mn", 0, "mN Cache")
	mdCache := flag.Int("md", 0, "mD Cache(minute)")
	recoveryBy := flag.String("r", "push", "Recovery by [push|pull]")
	rateControlQuantity := flag.Int("rq", 0, "Rate control quantity(count). 0 is unlimit.")
	ratecontrolBitrate := flag.Int("rb", 0, "Rate control bitrate(Kbps). 0 is unlimit.")
	transmissionControl := flag.String("tc", "no", "Transmission control [yes|no]")
	authList := flag.String("al", "", "Auth list [peer1,peer2,...]")
	ovId := flag.String("o", "", "Overlay ID for join")
	wport := flag.Int("wp", 0, "Peer web client port. default random port.")

	flag.Parse()

	if len(*peerId) <= 0 {
		logger.Println(logger.ERROR, "Need Peer ID. Use -h for usage.")
		return
	}

	if *create && len(*title) <= 0 {
		logger.Println(logger.ERROR, "Need Title. Use -h for usage.")
		return
	}

	if *join && len(*ovId) <= 0 && len(*title) <= 0 && len(*desc) <= 0 {
		logger.Println(logger.ERROR, "Need Overlay ID or Title or Description. Use -h for usage.")
		return
	}

	ex, _ := os.Executable()
	exPath := filepath.Dir(ex)

	os.Chdir(exPath)

	var instanceId int64 = time.Now().UnixMicro()

	logger.Println(logger.INFO, "Peer Id :", *peerId)
	logger.Println(logger.INFO, "Instance Id :", instanceId)
	logger.Println(logger.INFO, "Title :", *title)
	logger.Println(logger.INFO, "Description :", *desc)
	logger.Println(logger.INFO, "Expires :", *expires)
	logger.Println(logger.INFO, "Create :", *create)
	logger.Println(logger.INFO, "Heartbeat interval :", *hbInterval)
	logger.Println(logger.INFO, "Heartbeat timeout :", *hbTimeout)
	logger.Println(logger.INFO, "Auth type :", *authType)
	logger.Println(logger.INFO, "Admin key :", *adminKey)
	logger.Println(logger.INFO, "Access key :", *accessKey)
	logger.Println(logger.INFO, "Peer List :", *peerList)
	logger.Println(logger.INFO, "Rate control quantity(count) :", *rateControlQuantity)
	logger.Println(logger.INFO, "Rate control bitrate(Kbps) :", *ratecontrolBitrate)
	logger.Println(logger.INFO, "Transmission control :", *transmissionControl)
	logger.Println(logger.INFO, "Auth List :", *authList)
	logger.Println(logger.INFO, "Overlay ID :", *ovId)
	logger.Println(logger.INFO, "Web client port :", *wport)

	var overlayCreation *connect.HybridOverlayCreation = nil

	if *create {

		overlayCreation = new(connect.HybridOverlayCreation)
		overlayCreation.Overlay.Title = *title
		overlayCreation.Overlay.Type = "core"
		overlayCreation.Overlay.SubType = "tree"
		overlayCreation.Overlay.OwnerId = *peerId
		overlayCreation.Overlay.Expires = *expires
		overlayCreation.Overlay.Description = *desc
		if len(overlayCreation.Overlay.Description) <= 0 {
			overlayCreation.Overlay.Description = "no description"
		}
		overlayCreation.Overlay.HeartbeatInterval = *hbInterval
		overlayCreation.Overlay.HeartbeatTimeout = *hbTimeout

		auth := new(connect.OverlayAuth)
		auth.Type = *authType
		auth.AdminKey = *adminKey
		auth.AccessKey = nil
		auth.PeerList = nil
		if auth.Type == "closed" {
			if len(*peerList) > 0 {
				auth.PeerList = strings.Split(*peerList, ",")

				if len(*accessKey) > 0 {
					auth.AccessKey = accessKey
				}
			} else {
				if len(*accessKey) > 0 {
					auth.AccessKey = accessKey
				} else {
					logger.Println(logger.ERROR, "Need Access Key or Peer list when Auth type is 'closed'. Use -h for usage.")
					return
				}
			}
		}
		overlayCreation.Overlay.Auth = *auth

		crPolicy := new(connect.CrPolicy)
		crPolicy.MNCache = *mnCache
		crPolicy.MDCache = *mdCache
		crPolicy.RecoveryBy = *recoveryBy
		overlayCreation.Overlay.CrPolicy = crPolicy
	}

	logger.Printf(logger.INFO, "\n\nHP2P.Go start...\n\n")

	runtime.GOMAXPROCS(runtime.NumCPU())
	logger.Printf(logger.INFO, "Use %v processes.\n\n", runtime.GOMAXPROCS(0))

	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt, syscall.SIGINT, syscall.SIGTERM)
	httpServer := NewHttpServer(*peerId)
	httpServer.Start(*wport)

	var conn connect.Connect = &webrtc.WebrtcConnect{}
	conn.Init(*peerId, instanceId)

	httpServer.SetConnect(&conn)

	udpServer := UDPServer{}
	udpServer.peerId = *peerId
	udpServer.start(conn.GetClientConfig().UdpPort4IoT)
	udpServer.IoTDataCallback = conn.IoTData
	udpServer.BlockChainDataCallback = conn.BlockChainData
	udpServer.MediaDataCallback = conn.MediaData
	conn.SetRecvBlockChainCallback(udpServer.RecvBlockChain)
	conn.SetRecvMediaCallback(udpServer.RecvMedia)

	httpServer.IsOwner = conn.IsOwner

	if *create {
		conn.CreateOverlay(overlayCreation)

		if conn.OverlayInfo() == nil || len(conn.OverlayInfo().OverlayId) <= 0 {
			logger.Println(logger.ERROR, "Failed to create overlay.")
			return
		}

		logger.Println(logger.INFO, "CreateOverlay ID : ", conn.OverlayInfo().OverlayId)

		ovinfo := conn.OverlayJoin(false)

		if ovinfo == nil {
			logger.Println(logger.ERROR, "Failed to join overlay.")
			return
		}

		conn.OverlayReport()
	} else if *join {
		conn.OverlayQuery(ovId, title, desc)
		go conn.ConnectPeers(false)
	}

	//reader := bufio.NewReader(os.Stdin)

	//for {
	//select {
	//case <-interrupt:
	<-interrupt
	logger.Println(logger.INFO, "interrupt!!!!!")
	done := make(chan struct{})

	conn.Release(&done)

	select {
	case <-done:
	case <-time.After(time.Second * 10):
	}
	//return
	/*default:
	line, _ := reader.ReadString('\n')

	switch {
	case strings.HasPrefix(line, "msg "):
		send := strings.TrimSuffix(strings.TrimPrefix(line, "msg "), "\r")
		send = strings.TrimSuffix(send, "\n")
		logger.Println(logger.INFO, []byte(send))
		conn.BroadcastMessage([]byte(send))
	}*/
	//}
	//}
}

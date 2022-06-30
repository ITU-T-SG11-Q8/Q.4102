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

package main

import (
	"bufio"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"runtime"
	"strings"
	"time"

	"connect"
	"connect/webrtc"
)

func main() {
	peerId := flag.String("id", "", "Peer ID")
	toPeerId := flag.String("connect", "", "Peer ID to connect")
	flag.Parse()

	if len(*peerId) <= 0 {
		log.Fatal("Need Peer ID. Use -h for usage.")
	}

	fmt.Printf("HP2P.Go start...\n\n")

	runtime.GOMAXPROCS(runtime.NumCPU())
	fmt.Printf("Use %v processes.\n\n", runtime.GOMAXPROCS(0))

	log.SetFlags(log.LstdFlags | log.Lshortfile)

	interrupt := make(chan os.Signal, 1)
	signal.Notify(interrupt, os.Interrupt)

	log.Printf("PeerId: %s", *peerId)
	log.Printf("ToPeerId: %s", *toPeerId)

	/*sss := test.Ttest("111")
	fmt.Println(sss)
	fmt.Println(hello1.Hello())
	fmt.Println(hello1.Hello1_2())
	fmt.Println(hello2.Hello2())*/

	var conn connect.Connect = &webrtc.WebrtcConnect{}
	conn.Init(*peerId)

	if len(*toPeerId) > 0 {
		log.Printf("connect to %s", *toPeerId)
		conn.ConnectTo(*toPeerId)
	}

	reader := bufio.NewReader(os.Stdin)

	for {
		select {
		case <-interrupt:
			log.Println("interrupt!!!!!")
			done := make(chan struct{})

			select {
			case <-done:
			case <-time.After(time.Second * 1):
			}
			return
		default:
			line, _ := reader.ReadString('\n')

			switch {
			case strings.HasPrefix(line, "msg "):
				send := strings.TrimSuffix(strings.TrimPrefix(line, "msg "), "\r")
				send = strings.TrimSuffix(send, "\n")
				log.Println([]byte(send))
				conn.BroadcastMessage(send)
			}
		}
	}
}

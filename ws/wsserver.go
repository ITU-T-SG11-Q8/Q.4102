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
	"fmt"
	"log"
	"net/http"

	"github.com/gorilla/websocket"
)

var climap map[*websocket.Conn]int

func main() {

	climap = make(map[*websocket.Conn]int)

	http.Handle("/", http.FileServer(http.Dir("static")))
	http.HandleFunc("/ws", socketHandler)

	port := "8080"
	log.Printf("Listening on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
	log.Println("111")
}

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

func socketHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	defer func() {
		delete(climap, conn)
		conn.Close()
	}()

	if err != nil {
		log.Printf("upgrader.Upgrade: %v", err)
		return
	}

	if climap[conn] == 0 {
		climap[conn] = 1
	}

	for {
		messageType, p, err := conn.ReadMessage()
		fmt.Println(string(p))

		if err != nil {
			log.Printf("conn.ReadMessage: %v", err)
			return
		}
		/*
			if err := conn.WriteMessage(messageType, p); err != nil {
				log.Printf("conn.WriteMessage: %v", err)
				return
			}*/

		for key := range climap {
			if err := key.WriteMessage(messageType, p); err != nil {
				log.Printf("conn.WriteMessage: %v", err)
				continue
			}
		}
	}
}

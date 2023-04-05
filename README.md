# Q.4102

## Usage

1. Edit client's Configurations in 'clientconfig.json'   
2. Edit peer's Configurations in 'peerconfig.json'   
3. Build
```
$cd Peer   
$go mod tidy   
$go build
```
4. Run
```
- Usage
$hp2p.go.peer -h

- Owner peer
$hp2p.go.peer -c -id peer1 -t title

- Join peer
$hp2p.go.peer -j -id peer2 -t title

- Peer that does nothing (for use API later)
$hp2p.go.peer -id peer3
```

## Live Demo
You can check the running test server by accessing the following URL:  
http://144.24.179.237:8081/
  
And by setting the following information in clientconfig.json, you can connect to the running server/peer and test it.
```
...
"OVERLAY_SERVER_ADDR" : "http://144.24.179.237:8081",
"SIGNALING_SERVER_ADDR" : "ws://144.24.179.237:8082",
...
```
  
Use the following command to connect to the running peer.  
(xxx is an arbitrary peer ID, excluding peer1, peer2, peer3, and peer4.)
```
$hp2p.go.peer -j -id [xxx] -t test_overlay
```
Alternatively, you can also create a new overlay to test with the following command.
```
$hp2p.go.peer -c -id [xxx] -t [overlay_name]
```
  
## LICENSE

The MIT License

Copyright (c) 2022 ETRI

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
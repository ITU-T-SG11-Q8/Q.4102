# HP2P.Go


### Peer
- Edit client's configurations in 'Peer/clientconfig.json' 
- Edit peer's configiurations in 'Peer/peerconfig.json'
- Build
```
$cd Peer   
$go mod tidy   
$go build
```

## Usage


### Peer   
```
- Help
$hp2p.go.peer -h

- Run owner peer
$hp2p.go.peer -c -id peer1 -t title

- Run peer's join
$hp2p.go.peer -j -id peer2 -t title

- Run standalone peer
$hp2p.go.peer -id peer3
```

# Contributors
- BeauracracyEndless@ 
- CommitteeKnowledgeless@
- ClubKkondae@

# LICENSE

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

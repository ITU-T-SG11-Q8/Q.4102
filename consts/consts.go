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

package consts

const (
	AppIdChat               string = "chat"
	AppIdData               string = "etri_data"
	AppIdIoT                string = "iot"
	AppIdBlockChain         string = "blockchain"
	AppIdBlockChainRegister string = "blockchainregister"
	AppIdMedia              string = "media"
	AppIdMediaRegister      string = "mediaregister"
)

const (
	PayloadTypeText        string = "text/plain"
	PayloadTypeOctetStream string = "application/octet-stream"
)

const (
	IoTPeerList string = "peerlist"
	IoTDataList string = "peer_data_list"
	IoTDataLast string = "peer_last_data"
	IoTTypeList string = "type_data_list"
	IoTTypeLast string = "type_last_data"
)

const (
	TypeSdp              string = "sdp"
	TypeICE              string = "ice"
	TypeChat             string = "chat"
	TypeIoT              string = "iot"
	TypeScanTree         string = "scan_tree"
	TypeSendData         string = "send_data"
	TypeReceivedData     string = "received_data"
	TypeConnectionChange string = "connection_change"
	TypeOverlayCreation  string = "creation"
)

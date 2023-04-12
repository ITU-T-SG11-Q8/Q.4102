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
	"encoding/json"
	"logger"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/graphql-go/graphql"
)

type ApiError struct {
	ErrorMessage string
}

func (err *ApiError) Error() string {
	return err.ErrorMessage
}

var overlayNetworkType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "overlayNetworkType",
		Fields: graphql.Fields{
			"overlayTitle": &graphql.Field{
				Type: graphql.String,
			},
			"overlayId": &graphql.Field{
				Type: graphql.String,
			},
			"ticketId": &graphql.Field{
				Type: graphql.Int,
			},
		},
	},
)

var peerInfoType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "peerInfoType",
		Fields: graphql.Fields{
			"peerId": &graphql.Field{
				Type: graphql.String,
			},
			"networkAddress": &graphql.Field{
				Type: graphql.String,
			},
			"overlayNetwork": &graphql.Field{
				Type: overlayNetworkType,
			},
			"debugLevel": &graphql.Field{
				Type: graphql.Int,
			},
			"peerAuth": &graphql.Field{
				Type: graphql.String,
			},
		},
	},
)

var peerStatusType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "peerStatusType",
		Fields: graphql.Fields{
			"overlayId": &graphql.Field{
				Type: graphql.String,
			},
			"title": &graphql.Field{
				Type: graphql.String,
			},
			"peerId": &graphql.Field{
				Type: graphql.String,
			},
			"ownerId": &graphql.Field{
				Type: graphql.String,
			},
			"appId": &graphql.Field{
				Type: graphql.NewList(graphql.String),
			},
			"primaryCount": &graphql.Field{
				Type: graphql.Int,
			},
			"incomingCandidateCount": &graphql.Field{
				Type: graphql.Int,
			},
			"outgoingCandidateCount": &graphql.Field{
				Type: graphql.Int,
			},
			"overlayServerAddr": &graphql.Field{
				Type: graphql.String,
			},
			"signalingServerAddr": &graphql.Field{
				Type: graphql.String,
			},
			"udpPort": &graphql.Field{
				Type: graphql.Int,
			},
		},
	},
)

var overlayAuthType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "overlayAuthType",
		Fields: graphql.Fields{
			"type": &graphql.Field{
				Type: graphql.String,
			},
			"adminKey": &graphql.Field{
				Type: graphql.String,
			},
			"accessKey": &graphql.Field{
				Type: graphql.String,
			},
			"peerList": &graphql.Field{
				Type: graphql.NewList(graphql.String),
			},
		},
	},
)

var overlayInfoType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "overlayInfoType",
		Fields: graphql.Fields{
			"overlayId": &graphql.Field{
				Type: graphql.String,
			},
			"title": &graphql.Field{
				Type: graphql.String,
			},
			"type": &graphql.Field{
				Type: graphql.String,
			},
			"subType": &graphql.Field{
				Type: graphql.String,
			},
			"ownerId": &graphql.Field{
				Type: graphql.String,
			},
			"expires": &graphql.Field{
				Type: graphql.Int,
			},
			"description": &graphql.Field{
				Type: graphql.String,
			},
			"auth": &graphql.Field{
				Type: overlayAuthType,
			},
			"ticketId": &graphql.Field{
				Type: graphql.Int,
			},
			"heartbeatInterval": &graphql.Field{
				Type: graphql.Int,
			},
			"heartbeatTimeout": &graphql.Field{
				Type: graphql.Int,
			},
		},
	},
)

var joinOverlayInfoType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "joinOverlayInfoType",
		Fields: graphql.Fields{
			"overlayId": &graphql.Field{
				Type: graphql.String,
			},
			"type": &graphql.Field{
				Type: graphql.String,
			},
			"subType": &graphql.Field{
				Type: graphql.String,
			},
			"expires": &graphql.Field{
				Type: graphql.Int,
			},
			"heartbeatInterval": &graphql.Field{
				Type: graphql.Int,
			},
			"heartbeatTimeout": &graphql.Field{
				Type: graphql.Int,
			},
			"ticketId": &graphql.Field{
				Type: graphql.Int,
			},
		},
	},
)

var modifyOverlayInfoType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "modifyOverlayInfoType",
		Fields: graphql.Fields{
			"overlayId": &graphql.Field{
				Type: graphql.String,
			},
			"title": &graphql.Field{
				Type: graphql.String,
			},
			"ownerId": &graphql.Field{
				Type: graphql.String,
			},
			"expires": &graphql.Field{
				Type: graphql.Int,
			},
			"description": &graphql.Field{
				Type: graphql.String,
			},
			"auth": &graphql.Field{
				Type: overlayAuthType,
			},
		},
	},
)

var refreshOverlayType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "refreshOverlayType",
		Fields: graphql.Fields{
			"overlayId": &graphql.Field{
				Type: graphql.String,
			},
			"expires": &graphql.Field{
				Type: graphql.Int,
			},
			"peerId": &graphql.Field{
				Type: graphql.String,
			},
		},
	},
)

var scanTreeResultType = graphql.NewObject(
	graphql.ObjectConfig{
		Name: "scanTreeResultType",
		Fields: graphql.Fields{
			"peerId": &graphql.Field{
				Type: graphql.String,
			},
			"ticketId": &graphql.Field{
				Type: graphql.Int,
			},
			"address": &graphql.Field{
				Type: graphql.String,
			},
		},
	},
)

type ApiHandler struct {
	connect.HOMP
	connectObj   *connect.Connect
	SendScanTree func() int
	SendChat     func(msg string)

	SetScanTreeChan func(scanTreeChan *chan interface{})
}

func NewApiHandler(conn *connect.Connect) *ApiHandler {
	handler := new(ApiHandler)
	handler.connectObj = conn
	handler.SendScanTree = (*conn).SendScanTree
	handler.OverlayAddr = (*conn).GetClientConfig().OverlayServerAddr

	return handler
}

func (handler *ApiHandler) overlayList(p graphql.ResolveParams) (interface{}, error) {
	title, _ := p.Args["title"].(string)
	description, _ := p.Args["description"].(string)
	ovid, _ := p.Args["overlayId"].(string)

	logger.Println(logger.INFO, "api overlay list title:", title, "desc:", description, "ovid:", ovid)

	//if len(title) > 0 || len(description) > 0 || len(ovid) > 0 {
	rslts := handler.QueryOverlay(&ovid, &title, &description)
	logger.PrintJson(logger.INFO, "api overlay list rslt:", rslts)

	ovs := make([]connect.ApiOverlayInfo, 0)

	for _, rslt := range *rslts {
		ov := connect.ApiOverlayInfo{}
		ov.OverlayId = rslt.Overlay.OverlayId
		ov.Title = rslt.Overlay.Title
		ov.Type = rslt.Overlay.Type
		ov.SubType = rslt.Overlay.SubType
		ov.OwnerId = rslt.Overlay.OwnerId
		//ov.Expires = rslt.Overlay.Expires
		ov.Description = rslt.Overlay.Description
		ov.Auth = rslt.Overlay.Auth

		ovs = append(ovs, ov)
	}

	return ovs, nil
	//}

	//return nil, nil
}

func (handler *ApiHandler) overlayStatus(p graphql.ResolveParams) (interface{}, error) {
	logger.Println(logger.INFO, "api overlay status")

	if (*handler.connectObj).PeerInfo().TicketId < 0 {
		return nil, nil
	}

	rslt := connect.ApiOverlayInfo{}

	rslt.OverlayId = (*handler.connectObj).OverlayInfo().OverlayId
	rslt.Title = (*handler.connectObj).OverlayInfo().Title
	rslt.Type = (*handler.connectObj).OverlayInfo().Type
	rslt.SubType = (*handler.connectObj).OverlayInfo().SubType
	rslt.OwnerId = (*handler.connectObj).OverlayInfo().OwnerId
	//rslt.Expires = (*handler.connectObj).GetPeerConfig().Expires
	rslt.Description = &(*handler.connectObj).OverlayInfo().Description
	rslt.Auth = (*handler.connectObj).OverlayInfo().Auth
	rslt.TicketId = (*handler.connectObj).PeerInfo().TicketId
	rslt.HeartbeatInterval = (*handler.connectObj).OverlayInfo().HeartbeatInterval
	rslt.HeartbeatTimeout = (*handler.connectObj).OverlayInfo().HeartbeatTimeout

	return rslt, nil
}

func (handler *ApiHandler) overlayQuery() *graphql.Object {
	return graphql.NewObject(
		graphql.ObjectConfig{
			Name: "OverlayQuery",
			Fields: graphql.Fields{
				//https://localhost:8625/api/graphql?overaly={list(title:\"title\"){title,overlayId}}
				"list": &graphql.Field{
					Type: graphql.NewList(overlayInfoType),
					Args: graphql.FieldConfigArgument{
						"title": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
						"description": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
						"overlayId": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
					},
					Resolve: handler.overlayList,
				},
				"status": &graphql.Field{
					Type:    overlayInfoType,
					Resolve: handler.overlayStatus,
				},
			},
		},
	)
}

func (handler *ApiHandler) overlayCreate(p graphql.ResolveParams) (interface{}, error) {
	title, _ := p.Args["title"].(string)
	ovtype, _ := p.Args["type"].(string)
	expires, _ := p.Args["expires"].(int)
	description, _ := p.Args["description"].(string)
	heartbeatInterval, _ := p.Args["heartbeatInterval"].(int)
	heartbeatTimeout, _ := p.Args["heartbeatTimeout"].(int)
	adminKey, _ := p.Args["adminKey"].(string)
	accessKey, _ := p.Args["accessKey"].(string)

	logger.Println(logger.INFO, "api overlay create title:", title, "desc:", description, "expires:", expires)
	logger.Println(logger.INFO, "api overlay create ovtype:", ovtype, "heartbeatInterval:", heartbeatInterval, "heartbeatTimeout:", heartbeatTimeout)
	logger.Println(logger.INFO, "api overlay create adminKey:", adminKey, "accessKey:", accessKey)

	if ovtype != "core/tree" && ovtype != "sub/tree" && ovtype != "sub/mesh" {
		logger.Println(logger.ERROR, "api overlay create wrong type.")
		return nil, nil
	}

	if expires <= 0 {
		expires = 3600
	}

	if description == "" {
		description = "no description"
	}

	if heartbeatInterval <= 0 {
		heartbeatInterval = 100
	}

	if heartbeatTimeout <= 0 {
		heartbeatTimeout = 150
	}

	hoc := connect.HybridOverlayCreation{}
	hoc.Overlay.Title = title
	hoc.Overlay.Type = strings.Split(ovtype, "/")[0]
	hoc.Overlay.SubType = strings.Split(ovtype, "/")[1]
	hoc.Overlay.OwnerId = (*handler.connectObj).PeerId()
	//hoc.Overlay.Expires = expires
	hoc.Overlay.Description = description
	hoc.Overlay.HeartbeatInterval = heartbeatInterval
	hoc.Overlay.HeartbeatTimeout = heartbeatTimeout
	hoc.Overlay.Auth.AdminKey = adminKey
	hoc.Overlay.Auth.AccessKey = &accessKey
	if len(*hoc.Overlay.Auth.AccessKey) > 0 {
		hoc.Overlay.Auth.Type = "closed"
	} else {
		hoc.Overlay.Auth.Type = "open"
	}
	hoc.Overlay.CrPolicy = &connect.CrPolicy{}
	hoc.Overlay.CrPolicy.MDCache = 0
	hoc.Overlay.CrPolicy.MNCache = 0
	hoc.Overlay.CrPolicy.RecoveryBy = "push"

	logger.PrintJson(logger.INFO, "create option:", hoc)

	createOverlay := (*handler.connectObj).CreateOverlay(&hoc)

	if (*handler.connectObj).OverlayInfo() == nil || len((*handler.connectObj).OverlayInfo().OverlayId) <= 0 {
		logger.Println(logger.ERROR, "Failed to create overlay.")
		return nil, nil
	}

	logger.Println(logger.INFO, "CreateOverlay ID : ", (*handler.connectObj).OverlayInfo().OverlayId)

	/*ovinfo := (*handler.connectObj).OverlayJoin(false)

	if ovinfo == nil {
		logger.Println(logger.ERROR, "Failed to join overlay.")
		return nil, nil
	}

	(*handler.connectObj).OverlayReport()*/

	return createOverlay, nil
}

func (handler *ApiHandler) overlayJoin(p graphql.ResolveParams) (interface{}, error) {
	ovid, _ := p.Args["overlayId"].(string)
	expires, _ := p.Args["expires"].(int)
	accessKey, _ := p.Args["accessKey"].(string)
	recovery, _ := p.Args["recovery"].(bool)
	peerAuth, _ := p.Args["peerAuth"].(string)

	logger.Println(logger.INFO, "api overlay join ovid:", ovid, "expires:", expires, "accessKey:", accessKey)
	logger.Println(logger.INFO, "api overlay join recovery:", recovery, "peerAuth:", peerAuth)

	if expires <= 0 {
		expires = (*handler.connectObj).GetPeerConfig().Expires
	}

	hoj := new(connect.HybridOverlayJoin)
	hoj.Overlay.OverlayId = ovid
	hoj.Overlay.Type = (*handler.connectObj).OverlayInfo().Type
	hoj.Overlay.SubType = (*handler.connectObj).OverlayInfo().SubType
	hoj.Overlay.Auth = &(*handler.connectObj).OverlayInfo().Auth
	if len(accessKey) > 0 {
		hoj.Overlay.Auth.AccessKey = &accessKey
	}

	hoj.Peer.PeerId = (*handler.connectObj).PeerId()
	hoj.Peer.Address = (*handler.connectObj).GetPeerInfo().Address
	if len(peerAuth) > 0 {
		(*handler.connectObj).GetPeerInfo().Auth.Password = peerAuth
	}
	hoj.Peer.Auth = (*handler.connectObj).GetPeerInfo().Auth
	hoj.Peer.Expires = &expires
	hoj.Peer.TicketId = &(*handler.connectObj).PeerInfo().TicketId

	logger.PrintJson(logger.INFO, "join option:", hoj)

	joinOverlay := (*handler.connectObj).OverlayJoinBy(hoj, recovery)

	return joinOverlay, nil
}

func (handler *ApiHandler) overlayModify(p graphql.ResolveParams) (interface{}, error) {
	ovid, _ := p.Args["overlayId"].(string)
	title, _ := p.Args["title"].(string)
	//expires, _ := p.Args["expires"].(int)
	desc, _ := p.Args["description"].(string)
	adminKey, _ := p.Args["adminKey"].(string)
	accessKey, _ := p.Args["accessKey"].(string)

	//logger.Println(logger.INFO, "api overlay modify ovid:", ovid, "title:", title, "expires:", expires)
	logger.Println(logger.INFO, "api overlay modify desc:", desc, "adminKey:", adminKey, "accessKey:", accessKey)

	hom := connect.HybridOverlayModification{}
	hom.Overlay.OverlayId = ovid
	if len(title) > 0 {
		hom.Overlay.Title = &title
	}
	hom.Overlay.OwnerId = (*handler.connectObj).PeerId()
	/*if expires > 0 {
		hom.Overlay.Expires = &expires
	}*/
	if len(desc) > 0 {
		hom.Overlay.Description = &desc
	}
	if len(adminKey) > 0 {
		hom.Overlay.Auth.AdminKey = adminKey
	} else {
		hom.Overlay.Auth.AdminKey = (*handler.connectObj).OverlayInfo().Auth.AdminKey
	}
	if len(accessKey) > 0 {
		hom.Overlay.Auth.AccessKey = &accessKey
	}

	logger.PrintJson(logger.INFO, "modify option:", hom)

	modifyOverlay := (*handler.connectObj).OverlayModification(&hom)

	return modifyOverlay, nil
}

func (handler *ApiHandler) overlayRemove(p graphql.ResolveParams) (interface{}, error) {
	ovid, _ := p.Args["overlayId"].(string)
	adminKey, _ := p.Args["adminKey"].(string)

	logger.Println(logger.INFO, "api overlay remove ovid:", ovid, "adminKey:", adminKey)

	hor := connect.HybridOverlayRemoval{}
	hor.Overlay.OverlayId = ovid
	hor.Overlay.OwnerId = (*handler.connectObj).PeerId()
	hor.Overlay.Auth.AdminKey = adminKey

	logger.PrintJson(logger.INFO, "remove option:", hor)

	rslt := (*handler.connectObj).OverlayRemove(&hor)

	if len(rslt.OverlayId) > 0 {
		return true, nil
	}

	return false, nil
}

func (handler *ApiHandler) overlayRefresh(p graphql.ResolveParams) (interface{}, error) {
	ovid, _ := p.Args["overlayId"].(string)
	expires, _ := p.Args["expires"].(int)
	accessKey, _ := p.Args["accessKey"].(string)

	logger.Println(logger.INFO, "api overlay refresh ovid:", ovid, "expires:", expires, "accessKey", accessKey)

	hor := connect.HybridOverlayRefresh{}
	hor.Overlay.OverlayId = ovid
	if expires > 0 {
		hor.Peer.Expires = &expires
	}
	if len(accessKey) > 0 {
		hor.Overlay.Auth.AccessKey = &accessKey
	}

	hor.Peer.PeerId = (*handler.connectObj).PeerId()
	hor.Peer.Address = (*handler.connectObj).GetPeerInfo().Address
	hor.Peer.Auth = (*handler.connectObj).GetPeerInfo().Auth

	logger.PrintJson(logger.INFO, "refresh option:", hor)

	refresh := (*handler.connectObj).OverlayRefresh(&hor)

	if len(refresh.Overlay.OverlayId) <= 0 {
		return nil, nil
	}

	rslt := connect.ApiOverlayRefreshResponse{}
	rslt.OverlayId = refresh.Overlay.OverlayId
	rslt.Expires = refresh.Peer.Expires
	rslt.PeerId = refresh.Peer.PeerId

	return rslt, nil
}

func (handler *ApiHandler) overlayReport(p graphql.ResolveParams) (interface{}, error) {
	ovid, _ := p.Args["overlayId"].(string)

	logger.Println(logger.INFO, "api overlay report ovid:", ovid)

	rslt := (*handler.connectObj).OverlayReportBy(ovid)

	if len(rslt.OverlayId) > 0 {
		return true, nil
	}

	return false, nil
}

func (handler *ApiHandler) overlayLeave(p graphql.ResolveParams) (interface{}, error) {
	ovid, _ := p.Args["overlayId"].(string)

	logger.Println(logger.INFO, "api overlay leave ovid:", ovid)

	rslt := (*handler.connectObj).OverlayLeaveBy(ovid)

	if len(rslt.Overlay.OverlayId) > 0 {
		return true, nil
	}

	return false, nil
}

func (handler *ApiHandler) overlayMutation() *graphql.Object {
	return graphql.NewObject(
		graphql.ObjectConfig{
			Name: "OverlayMutation",
			Fields: graphql.Fields{
				//https://localhost:8307/api/graphql?overlay=mutation{create(title:%22titt%22,type:%22core/tree%22,adminKey:%221123%22){overlayId}}
				"create": &graphql.Field{
					Type: overlayInfoType,
					Args: graphql.FieldConfigArgument{
						"title": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
						"type": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
						"adminKey": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
						"expires": &graphql.ArgumentConfig{
							Type: graphql.Int,
						},
						"description": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
						"heartbeatInterval": &graphql.ArgumentConfig{
							Type: graphql.Int,
						},
						"heartbeatTimeout": &graphql.ArgumentConfig{
							Type: graphql.Int,
						},
						"accessKey": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
					},
					Resolve: handler.overlayCreate,
				},
				//https://localhost:8307/api/graphql?overlay=mutation{modify(overlayId:"b612afdc-90f0-4061-a157-29f57b5b5e40",title:"dddd"){overlayId,title,ownerId,expires,description,auth{type,accessKey,adminKey,peerList}}}
				"modify": &graphql.Field{
					Type: modifyOverlayInfoType,
					Args: graphql.FieldConfigArgument{
						"overlayId": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
						"title": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
						"expires": &graphql.ArgumentConfig{
							Type: graphql.Int,
						},
						"description": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
						"adminKey": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
						"accessKey": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
					},
					Resolve: handler.overlayModify,
				},
				//https://localhost:7461/api/graphql?overlay=mutation{join(overlayId:%22109f9eec-e929-4a30-b442-4e4ef3fe714b%22,peerAuth:%22asdf1234%22){overlayId,title,type,subType,ownerId,expires,description,auth{type,accessKey,adminKey,peerList}}}
				"join": &graphql.Field{
					Type: joinOverlayInfoType,
					Args: graphql.FieldConfigArgument{
						"overlayId": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
						"expires": &graphql.ArgumentConfig{
							Type: graphql.Int,
						},
						"accessKey": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
						"recovery": &graphql.ArgumentConfig{
							Type: graphql.Boolean,
						},
						"peerAuth": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
					},
					Resolve: handler.overlayJoin,
				},
				///api/graphql?overlay=mutation{remove(overlayId:"141b66d2-4cd1-464c-a52e-7f509fde5bff",adminKey:"asdf1234")}
				"remove": &graphql.Field{
					Type: graphql.Boolean,
					Args: graphql.FieldConfigArgument{
						"overlayId": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
						"adminKey": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
					},
					Resolve: handler.overlayRemove,
				},
				///api/graphql?overlay=mutation{refresh(overlayId:"bb21f4c1-ab89-46b1-bce9-14ed0fd954f5",expires:3600,accessKey:"asdf1234"){overlayId,expires,peerId}}
				"refresh": &graphql.Field{
					Type: refreshOverlayType,
					Args: graphql.FieldConfigArgument{
						"overlayId": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
						"expires": &graphql.ArgumentConfig{
							Type: graphql.Int,
						},
						"accessKey": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
					},
					Resolve: handler.overlayRefresh,
				},
				///api/graphql?overlay=mutation{report(overlayId:"21b01382-eadd-45b4-adb8-ad5d6497db25")}
				"report": &graphql.Field{
					Type: graphql.Boolean,
					Args: graphql.FieldConfigArgument{
						"overlayId": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
					},
					Resolve: handler.overlayReport,
				},
				///api/graphql?overlay=mutation{leave(overlayId:"c45405e0-7451-4213-8dd3-497cb0d941fd")}
				"leave": &graphql.Field{
					Type: graphql.Boolean,
					Args: graphql.FieldConfigArgument{
						"overlayId": &graphql.ArgumentConfig{
							Type: graphql.NewNonNull(graphql.String),
						},
					},
					Resolve: handler.overlayLeave,
				},
			},
		},
	)
}

func (handler *ApiHandler) configQuery() *graphql.Object {
	return graphql.NewObject(
		graphql.ObjectConfig{
			Name: "ConfigQuery",
			Fields: graphql.Fields{
				//https://localhost:3029/api/graphql?config={get{peerId,networkAddress,overlayNetwork{overlayTitle,overlayId,ticketId},debugLevel,peerAuth}}
				"get": &graphql.Field{
					Type: peerInfoType,
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {

						info := connect.ApiPeerInfo{}
						info.PeerId = (*handler.connectObj).PeerId()
						info.NetworkAddress = (*handler.connectObj).GetPeerInfo().Address
						info.OverlayNetwork.OverlayTitle = (*handler.connectObj).OverlayInfo().Title
						info.OverlayNetwork.OverlayId = (*handler.connectObj).OverlayInfo().OverlayId
						if (*handler.connectObj).PeerInfo().TicketId < 0 {
							info.OverlayNetwork.TicketId = 0
						} else {
							info.OverlayNetwork.TicketId = (*handler.connectObj).PeerInfo().TicketId
						}
						info.DebugLevel = logger.LEVEL
						info.PeerAuth = (*handler.connectObj).GetPeerInfo().Auth.Password

						logger.Println(logger.INFO, "api config get:", info)

						return info, nil
					},
				},
			},
		},
	)
}

func (handler *ApiHandler) configMutation() *graphql.Object {
	return graphql.NewObject(
		graphql.ObjectConfig{
			Name: "ConfigMutation",
			Fields: graphql.Fields{
				//https://localhost:12699/api/graphql?config=mutation{set(debugLevel:1)}
				"set": &graphql.Field{
					Type: graphql.Boolean,
					Args: graphql.FieldConfigArgument{
						"debugLevel": &graphql.ArgumentConfig{
							Type: graphql.Int,
						},
						"peerAuth": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
					},
					Resolve: func(p graphql.ResolveParams) (interface{}, error) {
						level, ok := p.Args["debugLevel"].(int)
						if ok {
							logger.Println(logger.INFO, "api set debuglevel:", level)

							logger.SetLevel(level)

							return true, nil
						}

						auth, ok := p.Args["peerAuth"].(string)
						if ok {
							logger.Println(logger.INFO, "api set peerauth:", auth)

							(*handler.connectObj).GetPeerInfo().Auth.Password = auth

							return true, nil
						}

						return false, &ApiError{ErrorMessage: "args not set"}
					},
				},
			},
		},
	)
}

func (handler *ApiHandler) peerStatus(p graphql.ResolveParams) (interface{}, error) {
	logger.Println(logger.INFO, "api peer status")

	rslt := connect.ApiPeerStatus{}

	rslt.OverlayId = (*handler.connectObj).OverlayInfo().OverlayId
	rslt.Title = (*handler.connectObj).OverlayInfo().Title
	rslt.PeerId = (*handler.connectObj).PeerId()
	rslt.OwnerId = (*handler.connectObj).OverlayInfo().OwnerId
	rslt.AppId = *(*handler.connectObj).GetConnectedAppIds()
	rslt.PrimaryCount = (*handler.connectObj).GetPeerStatus().NumPrimary
	rslt.IncomingCandidateCount = (*handler.connectObj).GetPeerStatus().NumInCandidate
	rslt.OutgoingCandidateCount = (*handler.connectObj).GetPeerStatus().NumOutCandidate
	rslt.OverlayServerAddr = (*handler.connectObj).GetClientConfig().OverlayServerAddr
	rslt.SignalingServerAddr = (*handler.connectObj).GetClientConfig().SignalingServerAddr
	rslt.UdpPort = (*handler.connectObj).GetClientConfig().UdpPort4IoT

	return rslt, nil
}

func (handler *ApiHandler) peerScanTree(p graphql.ResolveParams) (interface{}, error) {
	timeout, _ := p.Args["timeout"].(int)

	logger.Println(logger.INFO, "api peer scantree timeout:", timeout)

	if timeout <= 0 {
		timeout = 3
	}

	scanChan := make(chan interface{})
	handler.SetScanTreeChan(&scanChan)

	scantree := make([][]connect.ApiScanTreeResult, 0)

	end := false

	seq := handler.SendScanTree()

	for !end {
		select {
		case <-time.After(time.Second * time.Duration(timeout)):
			handler.SetScanTreeChan(nil)
			end = true
		case msg := <-scanChan:
			scan := msg.(*connect.ApiScanTreeData)

			if seq == scan.CSeq {
				rslts := make([]connect.ApiScanTreeResult, 0)
				for _, path := range *scan.Data {
					rslt := connect.ApiScanTreeResult{}
					rslt.PeerId = path[0]
					rslt.TicketId, _ = strconv.Atoi(path[1])
					rslt.Address = path[2]
					rslts = append(rslts, rslt)
				}
				scantree = append(scantree, rslts)
			}
		}
	}

	return scantree, nil
}

func (handler *ApiHandler) peerQuery() *graphql.Object {
	return graphql.NewObject(
		graphql.ObjectConfig{
			Name: "PeerQuery",
			Fields: graphql.Fields{
				///api/graphql?peer={status{overlayId,title,peerId,ownerId,appId,primaryCount,incomingCandidateCount,outgoingCandidateCount,overlayServerAddr,signalingServerAddr,udpPort}}
				"status": &graphql.Field{
					Type:    peerStatusType,
					Resolve: handler.peerStatus,
				},
				///api/graphql?peer={scantree(timeout:3){peerId,ticketId,address}}
				"scantree": &graphql.Field{
					Type: graphql.NewList(graphql.NewList(scanTreeResultType)),
					Args: graphql.FieldConfigArgument{
						"timeout": &graphql.ArgumentConfig{
							Type: graphql.Int,
						},
					},
					Resolve: handler.peerScanTree,
				},
			},
		},
	)
}

func (handler *ApiHandler) peerSend(p graphql.ResolveParams) (interface{}, error) {
	text, _ := p.Args["text"].(string)

	logger.Println(logger.INFO, "api peer sendtext text:", text)

	if len(text) <= 0 {
		return false, nil
	}

	handler.SendChat(text)

	return true, nil
}

func (handler *ApiHandler) peerMutation() *graphql.Object {
	return graphql.NewObject(
		graphql.ObjectConfig{
			Name: "PeerMutation",
			Fields: graphql.Fields{
				//https://localhost:8625/api/graphql?overaly={list(title:\"title\"){title,overlayid}}
				"send": &graphql.Field{
					Type: graphql.Boolean,
					Args: graphql.FieldConfigArgument{
						"text": &graphql.ArgumentConfig{
							Type: graphql.String,
						},
					},
					Resolve: handler.peerSend,
				},
			},
		},
	)
}

func (handler *ApiHandler) peerSchema() graphql.Schema {
	schema, _ := graphql.NewSchema(
		graphql.SchemaConfig{
			Query:    handler.peerQuery(),
			Mutation: handler.peerMutation(),
		},
	)

	return schema
}

func (handler *ApiHandler) overlaySchema() graphql.Schema {
	schema, _ := graphql.NewSchema(
		graphql.SchemaConfig{
			Query:    handler.overlayQuery(),
			Mutation: handler.overlayMutation(),
		},
	)

	return schema
}

func (handler *ApiHandler) configSchema() graphql.Schema {
	schema, _ := graphql.NewSchema(
		graphql.SchemaConfig{
			Query:    handler.configQuery(),
			Mutation: handler.configMutation(),
		},
	)

	return schema
}

func (handler *ApiHandler) HandleApi(w http.ResponseWriter, r *http.Request) {
	var result *graphql.Result = nil
	var statusCode int = http.StatusBadRequest
	var schema graphql.Schema
	var querystr string = ""

	if querystr = r.URL.Query().Get("config"); len(querystr) > 0 {
		schema = handler.configSchema()
	} else if querystr = r.URL.Query().Get("overlay"); len(querystr) > 0 {
		schema = handler.overlaySchema()
	} else if querystr = r.URL.Query().Get("peer"); len(querystr) > 0 {
		schema = handler.peerSchema()
	}

	result, statusCode = handler.executeQuery(querystr, schema)

	if result == nil {
		w.WriteHeader(statusCode)
	} else {
		json.NewEncoder(w).Encode(result)
	}
}

func (handler *ApiHandler) executeQuery(query string, schema graphql.Schema) (result *graphql.Result, statusCode int) {
	result = graphql.Do(graphql.Params{
		Schema:        schema,
		RequestString: query,
	})

	if len(result.Errors) > 0 {
		logger.Println(logger.ERROR, "graphql api errors:", result.Errors)
		return nil, 400
	} else {
		return result, 200
	}
}

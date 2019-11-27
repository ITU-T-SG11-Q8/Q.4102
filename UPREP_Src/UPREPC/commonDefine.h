#ifndef __COMMONDEFINE_H
#define __COMMONDEFINE_H

#pragma warning ( disable : 4018 )

//////////////////////////////////////////////////////////////////////////
#define DEV_OVERLAYID "DEV_OVERLAYID"
//#define DEV_OVERLAY_URL "http://192.168.0.100:8090/services/prep/overlay"
//#define DEV_CHANNEL_URL "http://192.168.0.100:8090/services/prep/channel"
#define DEV_OVERLAY_URL "http://192.168.0.40:9004/overlayNetworkTerminals"
#define DEV_CHANNEL_URL "http://192.168.0.40:9001/channels/"
//////////////////////////////////////////////////////////////////////////

#define RESPONSE_CODE_SOCK_ERROR 0
#define RESPONSE_CODE_OK 200
//#define RESPONSE_CODE_FAIL 400
#define RESPONSE_CODE_AUTH_REQUIRED 401
#define RESPONSE_CODE_NOTFOUND 404

#define SUCCESS 1
#define FAIL 0
#define SENDING 2

#define MODE_TIMEOUT_SEC 1
#define MODE_TIMEOUT_PIECE 2

#ifndef WIN32
#include <string.h>
#define _strdup(x)	strdup(x)
#endif

// string length
/*
#define DEFAULT_LEN 128+1
#define IPADDRESS_LEN 32+1
#define ACTIVITY_LEN 16+1
*/
// xml
/*
#define XML_CHANNEL_HEAD "<prep-service><service-info type=\"streaming\">\r\n"
#define XML_CHANNEL_TAIL "</service-info>\r\n</prep-service>"
#define XML_HEAD "<prep-service>\r\n"
#define XML_TAIL "</prep-service>"
#define XML_SERVICE_INFO "service-info"
#define XML_PREP_SERVICE "prep-service"
#define XML_PREP_OVERLAY "prep-overlay"
#define XML_PREP_NODE "prep-node"
#define XML_NODE_NETWORK_INFO "node-network-info"
#define XML_NODE_PROFILE "node-profile"
#define XML_NODE_ACTIVITY "node-activity"
#define XML_SUBJECT "subject"
#define XML_DESCRIPTION "description"
#define XML_IMAGE "image"
#define XML_PROVIDER "provider"
#define XML_PREP_INFO "prep-info"
#define XML_ID "id"
#define XML_IP "ip"
#define XML_PORT "port"
#define XML_URL "url"
#define XML_FRAGMENT_SIZE "fragment-size"
#define XML_EXPIRES "expires"
#define XML_MAXSERVERCONN "maxServerConn"
#define XML_CURSERVERCONN "curServerConn"
#define XML_MAXUPLOAD "maxUpload"
#define XML_MAXDOWNLOAD "maxDownload"
#define XML_STATUS "status"
#define XML_UPLOADED "uploaded"
#define XML_DOWNLOADED "downloaded"
#define XML_ACTIVETIME "activeTime"
#define XML_ACTION "action"
#define XML_ATTRIBUTE "attribute"*/

/*
typedef struct _PrepConfig_t {
	char* strAgentID;
	char* strLocalIP;
	unsigned int nLocalPort;

	//////////////////////////////////////////////////////////////////////////

	char *storage_path;

	unsigned int max_partner;   // 최대 Partner 숫자
	unsigned int max_neighbor;  // 최대 Neighbor 숫자
	unsigned int num_poke_neighbor;  // 찔러보는 Neighbor 숫자... 
}PrepConfig_t;

typedef struct _PrepNetwork_t
{
	char* strChannelServerURL;
	char* strChannelServerIP;
	unsigned int nChannelServerPort;
	char* strChannelServerPath;

	char* strOverlayServerURL;
	char* strOverlayServerIP;
	unsigned int nOverlayServerPort;
	char* strOverlayServerPath;

	//////////////////////////////////////////////////////////////////////////

	unsigned long fragment_size;
	unsigned int  fragment_number;
} PrepNetwork_t;
*/
typedef struct _PrepAgentInfo_t
{
	char* strPAID;
	char* strLocalIP;
	unsigned int nLocalPort;

	char* strChannelServerURL;
	char* strChannelServerIP;
	unsigned int nChannelServerPort;
	char* strChannelServerPath;

	char* strOverlayServerURL;
	char* strOverlayServerIP;
	unsigned int nOverlayServerPort;
	char* strOverlayServerPath;

	unsigned int nPieceSize;
} PrepAgentInfo_t;

typedef struct _OverlayItem_t {
	char* strOverlayID;
	char* strPAID;
	char* strAgentIP;
	unsigned int nAgentPort;
	unsigned int nMaxServerConn;
	unsigned int nCurServerConn;
	unsigned int nMaxUpload;
	unsigned int nMaxDownload;	
	char* strAction;
	char* strAttribute;
	unsigned int nUploaded;
	unsigned int nDownloaded;
	unsigned int nActiveTime;
} OverlayItem_t;

typedef struct _ChannelItem_t {
	char* strSubject;
	char* strDescription;
	char* strDescriptionImage;
	char* strProvider;
	char* strPAID;
	char* strOverlayURL;
	char* strOverlayID;
	unsigned int nPieceSize;
	unsigned int nExpires;
} ChannelItem_t;

typedef struct _Progress_t {
	int nStatus;
	double dTotalBytes;
	double dDownloadBytes;
	double dUploadBytes;
	int nSendPeerCount;
	int nRecvPeerCount;
	int nPeerCountInOverlayNetwork;
	long lAddedTime;
	long lCompleteTime;
	double dDownloadBps;
	double dUploadBps;
} Progress_t;

typedef struct _Property_t {
	char* strOverlayID;
	char* strTracker;
	double dDownloadLimit;
	double dUploadLimit;
	int nMaxSendPeerCount;
} Property_t;

#define PREP_EVENT_INIT "init"
#define PREP_EVENT_DOWNLOAD_SIZE "downSize"
#define PREP_EVENT_DOWNLOAD_PIECE "downPiece"
#define PREP_EVENT_UPDATE_DOWNLOAD_PIECE "updateDownPiece"
#define PREP_EVENT_UPLOAD_PIECE "upPiece"
#define PREP_EVENT_CONNECT_FAIL "connFail"
#define PREP_EVENT_START "start"
#define PREP_EVENT_COMPLETE "complete"
#define PREP_EVENT_PAUSE "pause"
#define PREP_EVENT_RESUME "resume"
#define PREP_EVENT_VERSION "version"
#define PREP_EVENT_BANDWIDTH "bandwidth"

#endif
#ifndef __PREP_COMMON_STRUCT_H__
#define __PREP_COMMON_STRUCT_H__

#include "commonDefine.h"
#include "Protocol/JsonKey.h"
#include <string>
#include <list>
#include <map>
#include <mutex>
#ifdef WIN32
#include <winsock.h>
#else
#include <sys/socket.h>
typedef int SOCKET;
#endif

typedef struct _ServerInfo_t
{
	SOCKET socket;
	char *strKey;
}ServerInfo_t;

typedef struct _PAMInfo_t
{
	char *strKey;
	char *strPAMSURL;
	int nInterval;
}PAMInfo_t;

typedef struct _ClientInfo_t
{
	char *strKey;

	pthread_t ClientHandle;
	SOCKET socket;

	char *strOverlayID;
	char * strServerIP;
	unsigned int nServerPort;
	char *strServerPath;

	pthread_mutex_t	ClientMutex;
	pthread_cond_t ClientCond;
	pthread_t ClientFireTID;

	unsigned int waitSecond;
}ClientInfo_t;

typedef struct _PeerData_t
{
	int prepMode;

	int nBYE;
	int nRefresh;
	pthread_t peerHandle;
	char pa_id[128 + 1];
	char ip[15 + 1];
	unsigned int port;
}PeerData_t;

typedef struct _NotifyData_t
{
	/*ProtocolHeader_t *header;
	ProtocolNotify_t *notify;*/
	unsigned int piece_index;
	struct _NotifyData_t *next;
}NotifyData_t;

typedef struct _PartnerData_t
{
	SOCKET socket;

	int nBYE;
	NotifyData_t *notifyData;
	unsigned int nNotifyCount;
	double notifyTime;

	PeerData_t *peerData;
}PartnerData_t;

typedef struct _PieceEvent_t
{
	int type;
	int id;
	bool integrity;
	std::string to;
	std::string from;
	_PieceEvent_t()
	{
		type = PAMP_OVERLAY_EVENT_UPLOADED;
		id = 0;
		integrity = true;
		to = "";
		from = "";
	}
}PieceEvent_t;

typedef std::map<double, PartnerData_t*> PartnerMap;
typedef PartnerMap::iterator PartnerMapIter;

typedef std::map<double, PeerData_t *> PeerMap;
typedef PeerMap::iterator PeerMapIter;

typedef struct _PrepAgent_t
{
	char* strOverlayID;
	char* strPAID;

	pthread_t recordHandle;
	pthread_t ServerHandle;
	pthread_t PlayHandle;
	pthread_t CommunicateHandle;
	pthread_t PAMReoprtHandle;

	int nPAMInterval;

	ClientInfo_t *ClientInfo;

	SOCKET recordSocket;
	SOCKET ServerSocket;
	SOCKET CommunicateSocket;
	SOCKET PlayServerSocket;
	SOCKET PlaySocket;

// 	PeerData_t **recvPeerData;
// 	PeerData_t **sendPeerData;
	double nPeerIdNext;
	PeerMap totalPeerMap;
	std::mutex totalPeerMutex;
	
	unsigned int nPieceSize;

	unsigned short nCurRecvPeerCount;
	unsigned short nCurSendPeerCount;
	unsigned short nPeerCountInOverlayNetwork;

	unsigned int nRecordPort;
	unsigned int nPeerPort;
	unsigned int nCommunicatePort;

	unsigned int nMaxPartnerCount;
	unsigned int nMaxPeerCount;
	unsigned int nAddPartnerCount;
	//unsigned int nCurSendPartnerCount;

	unsigned short nMaxRetryCount;

	unsigned short nSpStartPercent;

	double nPartnerTimeout;
	short nPartnerTimeoutMode;

	double nStartTimestamp;

	//PartnerData_t **recvPartnerData;
	//PartnerData_t **sendPartnerData;
	double nPartnerIdNext;
	PartnerMap recvPartnerMap;
	PartnerMap sendPartnerMap;
	std::mutex recvPartnerMutex;
	std::mutex sendPartnerMutex;

	double dUploadBps;
	double dDownloadBps;
	double dSecDownloadBytes;
	double dSecUploadBytes;
	double dTotalDownloadBytes;
	double dTotalUploadBytes;

	double dUploadBpsLimit;
	double dDownloadBpsLimit;

	double dAllUploadBpsLimit;
	double dAllDownloadBpsLimit;

	unsigned short nClose;

	int nIsPODO;
	int nAgentType;
	int nPause;
	int nIsHEVC;
	
	int nUsePello;

	std::list<PieceEvent_t*> pieceEventList;
	std::mutex pieceEventMutex;

	_PrepAgent_t()
	{
		strOverlayID = 0;
		strPAID = 0;

		ClientInfo = 0;

		recordSocket = 0;
		ServerSocket = 0;
		CommunicateSocket = 0;
		PlayServerSocket = 0;
		PlaySocket = 0;

		recordHandle = 0;
		ServerHandle = 0;
		PlayHandle = 0;
		CommunicateHandle = 0;
		PAMReoprtHandle = 0;
		nPAMInterval = 0;

		//recvPeerData = 0;
		//sendPeerData = 0;
		nPeerIdNext = 0;
		totalPeerMap.clear();

		nPieceSize = 0;

		nCurRecvPeerCount = 0;
		nCurSendPeerCount = 0;
		nPeerCountInOverlayNetwork = 0;

		nRecordPort = 0;
		nPeerPort = 0;
		nCommunicatePort = 0;

		nMaxPartnerCount = 0;
		nMaxPeerCount = 0;
		nAddPartnerCount = 0;
		//nCurSendPartnerCount = 0;

		nMaxRetryCount = 0;

		nSpStartPercent = 0;

		//recvPartnerData = 0;
		//sendPartnerData = 0;

		nPartnerIdNext = 0;
		recvPartnerMap.clear();
		sendPartnerMap.clear();

		dUploadBps = 0;
		dDownloadBps = 0;
		dSecDownloadBytes = 0;
		dSecUploadBytes = 0;
		dTotalDownloadBytes = 0;
		dTotalUploadBytes = 0;

		dUploadBpsLimit = 0;
		dDownloadBpsLimit = 0;

		dAllUploadBpsLimit = 0;
		dAllDownloadBpsLimit = 0;

		nClose = 0;

		nIsPODO = 0;
		nAgentType = 0;
		nPause = 0;
		nIsHEVC = 0;

		nUsePello = 0;

		nPartnerTimeout = 0;
		nPartnerTimeoutMode = MODE_TIMEOUT_SEC;

		nStartTimestamp = -1;
	}
} PrepAgent_t;

typedef struct _PeerInfo_t
{
	char *strKey;

	SOCKET socket;
	
	//SOCKET playerSocket;
	//struct sockaddr_in player_addr;
	
	double nPeerId;
	double nPartnerId;
	unsigned short nRetryCount;
	unsigned short nAddPartnerCount;
	int nDownSetPiece;

	int prepMode;
	
	void (*callback) (void*);

	PrepAgent_t * agent;
	ClientInfo_t *parentClient;
	ProtocolBuffermap_t *peerDownloadMapInfo;

	int port;
	char *id;
	char *ip;
}PeerInfo_t;

#endif
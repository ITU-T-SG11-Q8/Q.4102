#ifdef WIN32
#define _CRTDBG_MAP_ALLOC
#include "crtdbg.h"
#endif
#ifdef WIN32
#include <winsock.h>
#define close(x)			closesocket(x)
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#endif

#include <stdio.h>
#include <string.h>

#include "prepProtocolControl.h"
#include "commonDefine.h"
#include "NetworkUtil.h"

#include "Protocol/Hello.h"
#include "Protocol/Pello.h"
#include "Protocol/Get.h"
#include "Protocol/Data.h"
#include "Protocol/Refresh.h"
#include "Protocol/Buffermap.h"
#include "Protocol/PartnerRequest.h"
#include "Protocol/PartnerResponse.h"
#include "Protocol/Notify.h"
#include "Protocol/Busy.h"
#include "Protocol/Bye.h"

#include "Util.h"
#include "NetworkUtil.h"

unsigned long SEND_INDEX;

void DownloadMapPrint( unsigned int piece_index, unsigned int ds_length, unsigned char *download_map) 
{	
#ifdef PRINT_DEBUG
	{
		int j;
		DebugPrintInfo("\t\tDOWNLOAD_MAP(begin with %d : ", piece_index);
		for(j=0;j<ds_length;j++)
		{
			DebugPrintInfo("%d ", download_map[j]);
		}	
		DebugPrintInfo("");		
	}
#endif
}

void _stopPartners(PeerInfo_t *peer)
{
	peer->agent->sendPartnerMutex.lock();
	for (PartnerMapIter it = peer->agent->sendPartnerMap.begin(); it != peer->agent->sendPartnerMap.end(); ++it)
	{
		it->second->nBYE = 1;
	}
	peer->agent->sendPartnerMutex.unlock();

	peer->agent->recvPartnerMutex.lock();
	for (PartnerMapIter it = peer->agent->recvPartnerMap.begin(); it != peer->agent->recvPartnerMap.end(); ++it)
	{
		it->second->nBYE = 1;
	}
	peer->agent->recvPartnerMutex.unlock();
}

void _refreshPeers(PeerInfo_t *peer)
{
	peer->agent->totalPeerMutex.lock();
	for (PeerMapIter it = peer->agent->totalPeerMap.begin(); it != peer->agent->totalPeerMap.end(); ++it)
	{
		if (it->first == peer->nPeerId) continue;

		if (it->second->prepMode == PREP_SERVER_MODE)
		{
			it->second->nBYE = 1;
		}
		else if (it->second->prepMode == PREP_CLIENT_MODE)
		{
			it->second->nRefresh = 1;
		}
	}
	peer->agent->totalPeerMutex.unlock();
}

int recvHELLO(PeerInfo_t * Info, bsonobj& bson)
{
	int piece_index;
	int validVer = 0;
	
	ProtocolHello_t PrepHello;

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_HELLO [START]\n");

	Hello hello(bson);

	Info->agent->totalPeerMutex.lock();
	PeerMapIter it = Info->agent->totalPeerMap.find(Info->nPeerId);
	if (it != Info->agent->totalPeerMap.end())
	{
		sprintf_s(it->second->pa_id, hello.PeerId.c_str());
	}
	Info->agent->totalPeerMutex.unlock();

	PrepHello.valid_time = hello.ValidTime;
	PrepHello.sp_index = hello.SPIndex >= 0 ? hello.SPIndex : 0;
	PrepHello.complete_length = hello.CPLength;
	PrepHello.dp_index = hello.DPIndex;
	PrepHello.ds_length = hello.DSLength;

	if (PrepHello.ds_length > 0)
	{
		//RECV DOWNLOAD_MAP
		PrepHello.download_map = (unsigned char *)malloc(sizeof(unsigned char)*PrepHello.ds_length);
		if (PrepHello.download_map != NULL)
		{
			cpymem(PrepHello.download_map, hello.BufferMap, PrepHello.ds_length);
		}
	}
	else PrepHello.download_map = NULL;

	if (Info->agent->nPause)
	{
		return 0; // BYE~
	}

	if (Info->agent->nIsPODO)
	{
		validVer = PODOBuffer_isValidVersion(Info->strKey, PrepHello.valid_time);

		if (validVer == 0) // 나보다 버젼이 낮아
		{
			sendHELLO(Info, hello.StartTimestamp);
			return 0;
		}
		else if (validVer == -1) // 나보다 버젼이 높아
		{
			//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_VERSION, Info->agent->strOverlayID, NULL, NULL, 0, PrepHello.valid_time);
			return 0; // BYE~
		}
	}

	if (hello.OverlayId != Info->agent->strOverlayID)
	{
		return 0;
	}

	if (Info->peerDownloadMapInfo != NULL)
	{
		if (Info->peerDownloadMapInfo->download_map != NULL)
		{
			free(Info->peerDownloadMapInfo->download_map);
			Info->peerDownloadMapInfo->download_map = NULL;
		}

		free(Info->peerDownloadMapInfo);
		Info->peerDownloadMapInfo = NULL;
	}

	Info->peerDownloadMapInfo = (ProtocolBuffermap_t *)malloc(sizeof(ProtocolBuffermap_t));
	if (Info->peerDownloadMapInfo != NULL)
	{
		Info->peerDownloadMapInfo->piece_index = PrepHello.sp_index;
		Info->peerDownloadMapInfo->complete_length = PrepHello.complete_length;
		Info->peerDownloadMapInfo->dp_index = PrepHello.dp_index;
		Info->peerDownloadMapInfo->ds_length = PrepHello.ds_length;
		Info->peerDownloadMapInfo->download_map = PrepHello.download_map;
	}

	int refreshRslt = FAIL;
	
	if (Info->agent->nIsPODO)
		refreshRslt = PODOBuffer_refreshDownloadMap(Info->strKey, PrepHello.sp_index, PrepHello.complete_length, PrepHello.dp_index, PrepHello.ds_length, PrepHello.download_map);
	else
		refreshRslt = prepBuffer_refreshDownloadMap(Info->strKey, PrepHello.sp_index, PrepHello.complete_length, PrepHello.dp_index, PrepHello.ds_length, PrepHello.download_map);
	
	DownloadMapPrint(PrepHello.sp_index, PrepHello.ds_length, PrepHello.download_map);

	if (refreshRslt == SENDING)
	{
		_refreshPeers(Info);
		_stopPartners(Info);

		LogPrint(LOG_DEBUG, "\t!!!!! SP 갱신으로 파트너 삭제 !!!!!\n");
	}

	if(Info->prepMode == PREP_SERVER_MODE) {
		sendHELLO(Info, hello.StartTimestamp);
	}
	else //if (Info->agent->nAgentType != PAMP_TYPE_SEEDER)
	{
		if (Info->agent->nIsPODO)
			piece_index = PODOBuffer_getPieceIndex4Download(Info->strKey, PrepHello.sp_index, PrepHello.complete_length, PrepHello.dp_index, PrepHello.ds_length, PrepHello.download_map);
		else
			piece_index = prepBuffer_getPieceIndex4Download(Info->strKey, PrepHello.sp_index, PrepHello.complete_length, PrepHello.dp_index, PrepHello.ds_length, PrepHello.download_map);

		if(piece_index >= 0)
		{
			if (Info->agent->nIsPODO)
				PODOBuffer_setDownloadMapStatusByKey(Info->strKey, piece_index, PIECE_STATUS_DOWNLOADING);
			else
				prepBuffer_setDownloadMapStatusByKey(Info->strKey, piece_index, PIECE_STATUS_DOWNLOADING);

			Info->nDownSetPiece = piece_index;

			LogPrint(LOG_DEBUG, "recvHello sendGet\n");
			sendGET(Info, piece_index);
		}
		else if (Info->nPartnerId < 0)  //이놈한테는 지금 받을 Piece가 없어!
		{
			if (Info->prepMode != PREP_SERVER_MODE)
			{
				LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_HELLO [END]\n");
				return 0; // BYE~~
			}
		}
	}

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_HELLO [END]\n");

	return 1;
}

int sendHELLO(PeerInfo_t * Info, double starttime)
{
	int ret;
	ProtocolHello_t prepHello;
	//ProtocolHeader_t prepHeader;

// 	if(!PrepBuffer) return 0;
// 	if(Info->socket <=0 ) return 0;

	prepHello.download_map = NULL;

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_HELLO [START]\n");
	//HELLO
	//memcpy(prepHello.pa_id, Info->agent->strPAID, PA_ID_LEN);
	//memcpy(prepHello.overlay_id, Info->agent->strOverlayID, OVERLAY_ID_LEN);

	memset(&prepHello, 0, sizeof(ProtocolHello_t));

	if (Info->agent->nIsPODO)
	{
		PODOBuffer_getDownloadMap4HELLO(Info->strKey, &prepHello);
	}
	else
	{
		prepBuffer_getDownloadMap4HELLO(Info->strKey, &prepHello, starttime);
	}
	
	Hello hello;

	hello.PeerId = Info->agent->strPAID;
	hello.OverlayId = Info->agent->strOverlayID;
	hello.ValidTime = prepHello.valid_time;
	hello.SPIndex = prepHello.sp_index;
	hello.CPLength = prepHello.complete_length;
	hello.DPIndex = prepHello.dp_index;
	hello.DSLength = prepHello.ds_length;
	
	if (Info->agent->nStartTimestamp > 0)
		hello.StartTimestamp = Info->agent->nStartTimestamp;

	if (hello.DSLength > 0)
	{
		hello.BufferMap = new char[hello.DSLength];
		cpymem(hello.BufferMap, prepHello.download_map, hello.DSLength);
	}	

	int len = 0;

	const char * buf = hello.GetBin(len);
	
	//SEND HELLO
	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_HELLO [hello]\n");
	//ret=send(Info->socket, (char*)&prepHello, sizeof(ProtocolHello_t)-sizeof(unsigned char *), 0);
	ret = send(Info->socket, buf, len, 0);
	LogPrint(LOG_DEBUG, "ret %d \n", ret);
	if(ret <=0 ) { /* TODO: error handling */ }
		
	if (prepHello.download_map != NULL)
	{
		free(prepHello.download_map);
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_HELLO [END]\n");

	return 1;
}

int recvPELLO(PeerInfo_t * Info, bsonobj& bson)
{
	int piece_index;
	int validVer = 0;
	
	ProtocolHello_t PrepHello;

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_PELLO [START]\n");

	Pello pello(bson);

	if (Info->prepMode == PREP_SERVER_MODE)
	{
		Info->agent->totalPeerMutex.lock();
		PeerMapIter it = Info->agent->totalPeerMap.find(Info->nPeerId);

		if (it != Info->agent->totalPeerMap.end())
		{
			sprintf_s(it->second->pa_id, pello.PeerId.c_str());

			LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_PELLO [%s]\n", it->second->pa_id);

			it->second->prepMode = PREP_CLIENT_MODE;
			Info->prepMode = PREP_CLIENT_MODE;

			Info->agent->nCurRecvPeerCount--;
			Info->agent->nCurSendPeerCount++;
		}

		Info->agent->totalPeerMutex.unlock();
	}
	else
	{
		return 0;
	}

	if (Info->agent->nStartTimestamp >= 0 && prepBuffer_getCurrentSP(Info->strKey) < 0)
	{
		return 0;
	}

	PrepHello.valid_time = pello.ValidTime;
	PrepHello.sp_index = pello.SPIndex;
	PrepHello.complete_length = pello.CPLength;
	PrepHello.dp_index = pello.DPIndex;
	PrepHello.ds_length = pello.DSLength;

	if (PrepHello.ds_length > 0)
	{
		//RECV DOWNLOAD_MAP
		PrepHello.download_map = (unsigned char *)malloc(sizeof(unsigned char)*PrepHello.ds_length);
		if (PrepHello.download_map != NULL)
		{
			cpymem(PrepHello.download_map, pello.BufferMap, PrepHello.ds_length);
		}
	}
	else PrepHello.download_map = NULL;

	
	if (Info->agent->nPause)
	{
		return 0; // BYE~
	}

	if (Info->agent->nIsPODO)
	{
		validVer = PODOBuffer_isValidVersion(Info->strKey, PrepHello.valid_time);

		if (validVer == 0) // 나보다 버젼이 낮아
		{
			return 0;
		}
		else if (validVer == -1) // 나보다 버젼이 높아
		{
			return 0; // BYE~
		}
	}

	if (Info->peerDownloadMapInfo != NULL)
	{
		if (Info->peerDownloadMapInfo->download_map != NULL)
		{
			free(Info->peerDownloadMapInfo->download_map);
			Info->peerDownloadMapInfo->download_map = NULL;
		}

		free(Info->peerDownloadMapInfo);
		Info->peerDownloadMapInfo = NULL;
	}

	Info->peerDownloadMapInfo = (ProtocolBuffermap_t *)malloc(sizeof(ProtocolBuffermap_t));
	if (Info->peerDownloadMapInfo != NULL)
	{
		Info->peerDownloadMapInfo->piece_index = PrepHello.sp_index;
		Info->peerDownloadMapInfo->complete_length = PrepHello.complete_length;
		Info->peerDownloadMapInfo->dp_index = PrepHello.dp_index;
		Info->peerDownloadMapInfo->ds_length = PrepHello.ds_length;
		Info->peerDownloadMapInfo->download_map = PrepHello.download_map;
	}

	int refreshRslt = FAIL;

	if (Info->agent->nIsPODO)
		refreshRslt = PODOBuffer_refreshDownloadMap(Info->strKey, PrepHello.sp_index, PrepHello.complete_length, PrepHello.dp_index, PrepHello.ds_length, PrepHello.download_map);
	else
		refreshRslt = prepBuffer_refreshDownloadMap(Info->strKey, PrepHello.sp_index, PrepHello.complete_length, PrepHello.dp_index, PrepHello.ds_length, PrepHello.download_map);

	DownloadMapPrint(PrepHello.sp_index, PrepHello.ds_length, PrepHello.download_map);

	if (refreshRslt == SENDING)
	{
		_refreshPeers(Info);
		_stopPartners(Info);

		LogPrint(LOG_DEBUG, "\t!!!!! SP 갱신으로 파트너 삭제 !!!!!\n");
	}

	if (Info->agent->nIsPODO)
		piece_index = PODOBuffer_getPieceIndex4Download(Info->strKey, PrepHello.sp_index, PrepHello.complete_length, PrepHello.dp_index, PrepHello.ds_length, PrepHello.download_map);
	else
		piece_index = prepBuffer_getPieceIndex4Download(Info->strKey, PrepHello.sp_index, PrepHello.complete_length, PrepHello.dp_index, PrepHello.ds_length, PrepHello.download_map);

	if (piece_index >= 0)
	{
		if (Info->agent->nIsPODO)
			PODOBuffer_setDownloadMapStatusByKey(Info->strKey, piece_index, PIECE_STATUS_DOWNLOADING);
		else
			prepBuffer_setDownloadMapStatusByKey(Info->strKey, piece_index, PIECE_STATUS_DOWNLOADING);

		Info->nDownSetPiece = piece_index;

		LogPrint(LOG_DEBUG, "recvPello sendGet\n");
		sendGET(Info, piece_index);
	}
	else  //이놈한테는 지금 받을 Piece가 없어!
	{
		return 0; // BYE~~
	}

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_PELLO [END]\n");

	return 1;
}

int sendPELLO(PeerInfo_t * Info)
{
	int ret;
	ProtocolHello_t prepHello;
	
	prepHello.download_map = NULL;

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_PELLO [START]\n");
	
	memset(&prepHello, 0, sizeof(ProtocolHello_t));

	if (Info->agent->nIsPODO)
	{
		PODOBuffer_getDownloadMap4HELLO(Info->strKey, &prepHello);
	}
	else
	{
		prepBuffer_getDownloadMap4HELLO(Info->strKey, &prepHello, 0);
	}

	Pello pello;

	pello.PeerId = Info->agent->strPAID;
	pello.OverlayId = Info->agent->strOverlayID;
	pello.ValidTime = prepHello.valid_time;
	pello.SPIndex = prepHello.sp_index;
	pello.CPLength = prepHello.complete_length;
	pello.DPIndex = prepHello.dp_index;
	pello.DSLength = prepHello.ds_length;

	if (pello.DSLength > 0)
	{
		pello.BufferMap = new char[pello.DSLength];
		cpymem(pello.BufferMap, prepHello.download_map, pello.DSLength);
	}

	int len = 0;

	const char * buf = pello.GetBin(len);

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_PELLO [pello]\n");
	ret = send(Info->socket, buf, len, 0);
	
	if (ret <= 0) { /* TODO: error handling */ }

	if (prepHello.download_map != NULL)
	{
		free(prepHello.download_map);
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_PELLO [END]\n");

	return 1;
}

int recvGET(PeerInfo_t * Info, bsonobj& bson)
{
	ProtocolGet_t PrepGet;
	
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_GET [START]\n");
	
	Get get(bson);
	
	PrepGet.piece_index = get.PieceIndex;
	PrepGet.offset = get.Offset;

	LogPrint(LOG_DEBUG, "\t----> recv GET : %d\n", PrepGet.piece_index);
	
	sendDATA(Info, PrepGet.piece_index);

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_GET [END]\n");

	return 1;
}

int sendGET(PeerInfo_t * Info, unsigned int piece_index) 
{
	int ret;

	Get get;
	get.PieceIndex = piece_index;
	get.Offset = 0;

	int len = 0;
	const char * buf = get.GetBin(len);

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_GET [get]\n");
	ret = send(Info->socket, buf, len, 0);
	if(ret <=0 )
	{
		LogPrint(LOG_CRITICAL, "\t\t----> send PREP_PROTOCOL_GET [ERROR] : %d\n", piece_index);
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_GET [END]\n");

	return 1;
}

int recvDATA(PeerInfo_t * Info, bsonobj& bson)
{
	int nextPiece_index;
	ProtocolData_t PrepData;
	
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_DATA [START]\n");
	
	LogPrint(LOG_DEBUG, "recvDATA 수신 완료\n");

	Data data(bson);

	PrepData.piece_index = data.PieceIndex;
	PrepData.offset = data.Offset;
	PrepData.size = data.DataSize;
	
	LogPrint(LOG_DEBUG, "%s\t----> recv Data : %d\n", Info->agent->strPAID, PrepData.piece_index);
	LogPrint(LOG_DEBUG, "\t----> recv PrepData.size : %d\n", PrepData.size);

	
	if (data.DataSize > 0)
	{
		Info->nRetryCount = 0;
		
		{
			int issending = 0;
			if (Info->agent->nIsPODO)
			{
				issending = PODOBuffer_setPieceData(Info->strKey, PrepData.piece_index, data.DataBin);
			}
			else
			{
				issending = prepBuffer_setPieceData(Info->strKey, PrepData.piece_index, data.DataBin);
				prepBuffer_setPieceDataTimestamp(Info->strKey, PrepData.piece_index, data.TimeStamp);

				if (Info->agent->nPartnerTimeoutMode == MODE_TIMEOUT_PIECE && Info->agent->nPartnerTimeout < 0)
				{
					double itv = prepBuffer_getPieceDataTimestampInterval(Info->strKey);

					if (itv > 0)
					{
						Info->agent->nPartnerTimeout = (Info->agent->nPartnerTimeout * -1) * itv;
					}
				}
			}

			Info->nDownSetPiece = -1;
			
			if (issending != FAIL)
			{
				LogPrint(LOG_DEBUG, "PREP_EVENT_DOWNLOAD_PIECE\n");

				if (Info->agent->nAgentType == PAMP_TYPE_CS || Info->agent->nIsHEVC)
				{
					char * pieceData = NULL;

					while (prepBuffer_getCurrentPP(Info->strKey) < prepBuffer_getCurrentDP(Info->strKey))
					{
						pieceData = prepBuffer_getPlayData(Info->strKey, 0);

						if (pieceData == NULL /*|| !strcmp("", pieceData)*/)
						{
							LogPrint(LOG_DEBUG, "pieceData == NULL\n");
						}
						else
						{
							free(pieceData);
							pieceData = NULL;

							if (GetSimulationLogPrint() > 0)
							{
								int pp = prepBuffer_getCurrentPP(Info->strKey);
								LogPrint(LOG_SIMULATION, "PlayPiece\t\t%d\t%s\t\t%s\n", pp, GetTimeString(prepBuffer_getPieceDataTimestamp(Info->strKey, pp) / 1000), GetTimeString(0));
							}
						}
					}
				}

				LogPrint(LOG_DEBUG, "333333333333333333333333333333333333\n");
								
				if (Info->agent->nPAMInterval > 0 || GetSimulationLogPrint() > 0)
				{

					LogPrint(LOG_DEBUG, "44444444444444444444444444444444444444444\n");
					PieceEvent_t *pe = new PieceEvent_t();
					pe->type = PAMP_OVERLAY_EVENT_DOWNLOADED;
					pe->id = PrepData.piece_index;
					pe->integrity = true;

					if (Info->nPartnerId >= 0)
					{
						Info->agent->sendPartnerMutex.lock();
						PartnerMapIter it = Info->agent->sendPartnerMap.find(Info->nPartnerId);
						if (it != Info->agent->sendPartnerMap.end())
						{
							pe->from = it->second->peerData->pa_id;
						}
						else
						{
							pe->from = "Unknown";
						}
						Info->agent->sendPartnerMutex.unlock();
					}
					else
					{
						Info->agent->totalPeerMutex.lock();
						PeerMapIter it = Info->agent->totalPeerMap.find(Info->nPeerId);
						if (it != Info->agent->totalPeerMap.end())
						{
							pe->from = it->second->pa_id;
						}
						else
						{
							pe->from = "Unknown";
						}
						Info->agent->totalPeerMutex.unlock();
					}

					pe->to = Info->agent->strPAID;

					if (Info->agent->nPAMInterval > 0)
					{
						Info->agent->pieceEventMutex.lock();
						Info->agent->pieceEventList.push_back(pe);
						Info->agent->pieceEventMutex.unlock();
					}

					if (GetSimulationLogPrint() > 0)
					{
						LogPrint(LOG_DEBUG, "555555555555555555555555555555555555555555\n");
						char* aa = GetTimeString(data.TimeStamp / 1000);
						char* bb = GetTimeString(0);
						LogPrint(LOG_DEBUG, "666666666666666666666666666666666\n");
						LogPrint(LOG_SIMULATION, "ReceivePiece\t%d\t%s\t\t%s\t\t%s\t%s\n", pe->id, aa, bb, pe->from.c_str(), pe->to.c_str());

						LogPrint(LOG_DEBUG, "77777777777777777777777777777777777\n");
						delete aa;
						LogPrint(LOG_DEBUG, "888888888888888888888888888888888\n");
						delete bb;

						
					}
				}

				LogPrint(LOG_DEBUG, "PREP_EVENT_DOWNLOAD_PIECE - END\n");
			}
			else
			{
				prepBuffer_setDownloadMapStatusByKey(Info->strKey, PrepData.piece_index, PIECE_STATUS_ERROR);
			}

			if (Info->agent->nIsPODO)
			{
				if (PODOBuffer_isPODOComplete(Info->strKey, 1))
				{
					PODOBuffer_removeDownFile(Info->strKey);
				}
			}

			LogPrint(LOG_DEBUG, "1111111111111111111111111111111111\n");

			Info->agent->recvPartnerMutex.lock();
			for (PartnerMapIter it = Info->agent->recvPartnerMap.begin(); it != Info->agent->recvPartnerMap.end(); ++it)
			{
				NotifyData_t *data = it->second->notifyData;

				if (data == NULL)
				{
					data = (NotifyData_t *)malloc(sizeof(NotifyData_t));
					if (data != NULL)
					{
						memset(data, 0, sizeof(NotifyData_t));
						it->second->notifyData = data;
					}
				}
				else
				{
					NotifyData_t *next = data;
					while (next->next != NULL)
					{
						next = next->next;
					}

					data = (NotifyData_t *)malloc(sizeof(NotifyData_t));
					if (data != NULL)
					{
						memset(data, 0, sizeof(NotifyData_t));
						next->next = data;
					}
				}

				data->piece_index = PrepData.piece_index;
			}
			Info->agent->recvPartnerMutex.unlock();

			LogPrint(LOG_DEBUG, "22222222222222222222222222222222\n");
 		}
	}
	else
	{
		if (Info->agent->nIsPODO)
			PODOBuffer_setDownloadMapStatusByKey(Info->strKey, PrepData.piece_index, PIECE_STATUS_ERROR);
		else
			prepBuffer_setDownloadMapStatusByKey(Info->strKey, PrepData.piece_index, PIECE_STATUS_ERROR);
	}
	
	if (Info->nPartnerId < 0)
	{
		//다음에 받을 piece_index 결정
		if (Info->agent->nIsPODO)
		{
			nextPiece_index = PODOBuffer_getPieceIndex4Download(Info->strKey, Info->peerDownloadMapInfo->piece_index, Info->peerDownloadMapInfo->complete_length, \
				Info->peerDownloadMapInfo->dp_index, Info->peerDownloadMapInfo->ds_length, Info->peerDownloadMapInfo->download_map);
		}
		else
		{
			nextPiece_index = prepBuffer_getPieceIndex4Download(Info->strKey, Info->peerDownloadMapInfo->piece_index, Info->peerDownloadMapInfo->complete_length, \
				Info->peerDownloadMapInfo->dp_index, Info->peerDownloadMapInfo->ds_length, Info->peerDownloadMapInfo->download_map);
		}

		if (PrepData.size <= 0 || PrepData.piece_index == nextPiece_index)
		{
			if(Info->nRetryCount >= Info->agent->nMaxRetryCount)
			{
				LogPrint(LOG_DEBUG, "No more Interest\n");
				return -1;
			}
			else
			{
				Info->nRetryCount++;
				SLEEP(1000);

				if (Info->agent->nIsPODO)
					sendREFRESH(Info, PODOBuffer_getCurrentDP(Info->strKey));
				else
					sendREFRESH(Info, prepBuffer_getCurrentDP(Info->strKey));
			}
		}
		else
		{
			if(nextPiece_index >= 0)
			{
				Info->nRetryCount = 0;
				Info->nAddPartnerCount = 0;

				if (Info->agent->nIsPODO)
					PODOBuffer_setDownloadMapStatusByKey(Info->strKey, nextPiece_index, PIECE_STATUS_DOWNLOADING);
				else
					prepBuffer_setDownloadMapStatusByKey(Info->strKey, nextPiece_index, PIECE_STATUS_DOWNLOADING);

				Info->nDownSetPiece = nextPiece_index;

				LogPrint(LOG_DEBUG, "recvData sendGet\n");
				sendGET(Info, nextPiece_index);
			}
			else
			{
				if(Info->nPartnerId < 0)
				{
					if(Info->nRetryCount >= Info->agent->nMaxRetryCount)
					{
						LogPrint(LOG_DEBUG, "No more Interest\n");
						return -1;
					}
					else
					{
						LogPrint(LOG_DEBUG, "Info->nAddPartnerCount : %d, Info->agent->nAddPartnerCount : %d\n", Info->nAddPartnerCount, Info->agent->nAddPartnerCount);
						if (Info->nAddPartnerCount > Info->agent->nAddPartnerCount)
						{
							Info->nAddPartnerCount = 0;

							if (Info->agent->nIsPODO)
								sendPARTNER(Info, PODOBuffer_getCurrentDP(Info->strKey));
							else
								sendPARTNER(Info, prepBuffer_getCurrentDP(Info->strKey));
						}
						else
						{
							Info->nRetryCount++;
							SLEEP(1000);

							if (Info->agent->nIsPODO)
								sendREFRESH(Info, PODOBuffer_getCurrentDP(Info->strKey));
							else
								sendREFRESH(Info, prepBuffer_getCurrentDP(Info->strKey));
						}
					}
				}
			}
		}
	}

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_DATA [END]\n");
	
	return 1;
}

int sendDATA(PeerInfo_t * Info, int piece_index) 
{
	int ret;
	int result = 0;

	Data data;
	data.PieceIndex = piece_index;
	data.Offset = 0;
	data.DataSize = Info->agent->nPieceSize;
	data.DataBin = new char[data.DataSize];

	LogPrint(LOG_DEBUG, "\t\t----> if(piece_index > -1) \n");
	if (Info->agent->nIsPODO)
	{
		result = PODOBuffer_getPieceData(Info->strKey, piece_index, data.DataBin);
	}
	else
	{
		result = prepBuffer_getPieceData(Info->strKey, piece_index, data.DataBin);
		data.TimeStamp = prepBuffer_getPieceDataTimestamp(Info->strKey, piece_index);
	}

	int len = 0;

	const char* buf = data.GetBin(len);

	LogPrint(LOG_DEBUG, "\t\t----> send DATA [START] : %d\n", piece_index);

	{
		int sent_len=0;
		int sendingSize=0;
		
		sendingSize = len;

		LogPrint(LOG_DEBUG, "\t\t----> sendingSize -- %d \n", sendingSize);
		LogPrint(LOG_DEBUG, "\t\t----> result -- %d \n", result);
		LogPrint(LOG_DEBUG, "\t\t----> sent_len -- %d \n", sent_len);

		while(result && sent_len < sendingSize)
		{
			int sendSize = 1024;
			int remainder = sendingSize - sent_len;

			//LogPrint(LOG_DEBUG, "\t\t----> remainder -- %d \n", remainder);

			while (sendingSize < sendSize && sendSize > 0)
			{
				sendSize /= 2;
			}

			//LogPrint(LOG_DEBUG, "\t\t----> sendSize -- %d \n", sendSize);

			if (remainder > 0 && remainder < sendSize)
			{
				sendSize = remainder;
				//LogPrint(LOG_DEBUG, "\t\t----> sendSize = remainder -- %d \n", sendSize);
			}

			while (!Info->agent->nClose && Info->agent->dUploadBpsLimit > 0 && Info->agent->dSecUploadBytes >= Info->agent->dUploadBpsLimit)
			{
				SLEEP(100);
			}

			while (!Info->agent->nClose && Info->agent->dAllUploadBpsLimit > 0 && Info->agent->dSecUploadBytes >= Info->agent->dAllUploadBpsLimit)
			{
				SLEEP(100);
			}

			ret = send(Info->socket, buf + sent_len, sendSize, 0);

			LogPrint(LOG_DEBUG, "\t\t----> send ret -- %d \n", ret);

			if(ret<=0)
			{
				break;
			}

			//sleep(1);

			sent_len += ret;

			LogPrint(LOG_DEBUG, "\t\t----> sent_len -- %d \n", sent_len);

			Info->agent->dTotalUploadBytes += ret;
			Info->agent->dSecUploadBytes += ret;

			//LogPrint(LOG_DEBUG, "\t\t----> sent_len -- %d \n", sent_len);

			if (sent_len == sendingSize && !Info->agent->nClose)
			{
				LogPrint(LOG_DEBUG, "\tPREP_EVENT_UPLOAD_PIECE\n");
				LogPrint(LOG_DEBUG, Info->strKey);
				LogPrint(LOG_DEBUG, Info->agent->strPAID);
				//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_UPLOAD_PIECE, Info->strKey, Info->agent->strPAID, NULL, piece_index, sendingSize);

				char paid[200] = { '\0', };

				if (Info->nPartnerId >= 0)
				{
					Info->agent->recvPartnerMutex.lock();
					PartnerMapIter it = Info->agent->recvPartnerMap.find(Info->nPartnerId);

					if (it != Info->agent->recvPartnerMap.end())
					{
						sprintf_s(paid, it->second->peerData->pa_id);
					}
					Info->agent->recvPartnerMutex.unlock();
				}
				else
				{
					Info->agent->totalPeerMutex.lock();
					PeerMapIter it = Info->agent->totalPeerMap.find(Info->nPeerId);

					if (it != Info->agent->totalPeerMap.end())
					{
						sprintf_s(paid, it->second->pa_id);
					}
					Info->agent->totalPeerMutex.unlock();
				}
				
				if (Info->agent->nPAMInterval > 0)
				{
					PieceEvent_t *pe = new PieceEvent_t();
					pe->type = PAMP_OVERLAY_EVENT_UPLOADED;
					pe->id = piece_index;
					pe->integrity = true;
					pe->from = Info->agent->strPAID;
					pe->to = strlen_s(paid) > 0 ? paid : "Unknown";
					Info->agent->pieceEventMutex.lock();
					Info->agent->pieceEventList.push_back(pe);
					Info->agent->pieceEventMutex.unlock();
				}

				LogPrint(LOG_DEBUG, "\tPREP_EVENT_UPLOAD_PIECE - END\n");
				break;
			}
		}
		
		/*{
			FILE *fp = fopen("D:\\preptemp\\123.mp4", "ab");
			fwrite(pieceData, Info->agent->nPieceSize, 1, fp );
			fclose(fp);
		}*/

		//free(pieceData);
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_DATA [END]\n");

	return 1;	
}

int recvBUSY(PeerInfo_t * Info, bsonobj& bson)
{
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_BUSY [START]\n");
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_BUSY [END]\n");
	return -1;
}

int sendBUSY(PeerInfo_t * Info) 
{
	int ret;

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_BUSY [START]\n");

	Busy busy;
	busy.Reason = "Unknown";

	int len = 0;
	const char* buf = busy.GetBin(len);
	ret = send(Info->socket, buf, len, 0);
	if (ret <= 0)
	{
		return 0;
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_BUSY [END]\n");

	return 1;	
}

int recvDATACANCEL(PeerInfo_t * Info, bsonobj& bson)
{
	int ret = -1;
	
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_DATACANCEL [data_cancel]\n");
	/*if(ret<=0) {
		return ret;
	}*/
	/*
	prepDataCancel.piece_index=align2MyEndianI(prepDataCancel.piece_index);
	prepDataCancel.reason=align2MyEndianI(prepDataCancel.reason);

	if (Info->agent->nIsPODO)
		PODOBuffer_setDownloadMapStatusByKey(Info->strKey, prepDataCancel.piece_index, PIECE_STATUS_EMPTY);
	else
		prepBuffer_setDownloadMapStatusByKey(Info->strKey, prepDataCancel.piece_index, PIECE_STATUS_EMPTY);
	*/
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_DATACANCEL [END]\n");

	return ret;
}

int sendDATACANCEL(PeerInfo_t * Info, unsigned int piece_index, unsigned int reason) 
{
//	int ret;

	ProtocolDataCancel_t prepDataCancel;
	
	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_DATACANCEL [START]\n");

	prepDataCancel.piece_index =align2LittleEndianI(piece_index);
	prepDataCancel.reason =align2LittleEndianI(reason);

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_DATACANCEL [END]\n");
	return 1;
}

int recvREFRESH(PeerInfo_t * Info, bsonobj& bson)
{
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_REFRESH [START]\n");

	Refresh refresh(bson);
	
	sendBUFFERMAP(Info, refresh.PieceIndex, refresh.PieceNumber);

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_REFRESH [END]\n");
	
	return 1;
}

int sendREFRESH(PeerInfo_t * Info, unsigned int piece_index) 
{
	int ret;

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_REFRESH [START]\n");

	Refresh refresh;
	refresh.PieceIndex = piece_index;
	refresh.PieceNumber = 0;

	int len = 0;
	const char * buf = refresh.GetBin(len);

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_REFRESH [refresh]\n");
	ret = send(Info->socket, buf, len, 0);
	if(ret <=0 )
	{
		LogPrint(LOG_CRITICAL, "sendREFRESH : send error\n");
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_REFRESH [END]\n");

	return 1;
}

int recvBUFFERMAP(PeerInfo_t * Info, bsonobj& bson)
{
	ProtocolBuffermap_t PrepBuffermap;
	int piece_index = 0;

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_BUFFERMAP [START]\n");
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_BUFFERMAP [buffermap]\n");
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_BUFFERMAP [download_map]\n");

	Buffermap buffermap(bson);

	PrepBuffermap.piece_index = buffermap.PieceIndex;
	PrepBuffermap.complete_length = buffermap.CPLength;
	PrepBuffermap.dp_index = buffermap.DPIndex;
	PrepBuffermap.ds_length = buffermap.DSLength;

	PrepBuffermap.download_map = (unsigned char *)malloc(sizeof(unsigned char)*PrepBuffermap.ds_length);
	if (PrepBuffermap.download_map != NULL)
	{
		memset(PrepBuffermap.download_map, 0, sizeof(unsigned char)*PrepBuffermap.ds_length);
		cpymem(PrepBuffermap.download_map, buffermap.BuffermapBin, buffermap.DSLength);
	}

	int refreshRslt = FAIL;

	if (Info->agent->nIsPODO)
		refreshRslt = PODOBuffer_refreshDownloadMap(Info->strKey, PrepBuffermap.piece_index, PrepBuffermap.complete_length, PrepBuffermap.dp_index, PrepBuffermap.ds_length, PrepBuffermap.download_map);
	else
		refreshRslt = prepBuffer_refreshDownloadMap(Info->strKey, PrepBuffermap.piece_index, PrepBuffermap.complete_length, PrepBuffermap.dp_index, PrepBuffermap.ds_length, PrepBuffermap.download_map);

	if (refreshRslt == SENDING)
	{
		_refreshPeers(Info);
		_stopPartners(Info);
	}

	Info->peerDownloadMapInfo->piece_index = PrepBuffermap.piece_index;
	Info->peerDownloadMapInfo->complete_length = PrepBuffermap.complete_length;
	Info->peerDownloadMapInfo->dp_index = PrepBuffermap.dp_index;
	Info->peerDownloadMapInfo->ds_length = PrepBuffermap.ds_length;
	if (Info->peerDownloadMapInfo->download_map != NULL)
	{
		free(Info->peerDownloadMapInfo->download_map);
		Info->peerDownloadMapInfo->download_map = NULL;
	}

	if (PrepBuffermap.ds_length > 0)
	{
		Info->peerDownloadMapInfo->download_map = PrepBuffermap.download_map;
	}
	
	if (Info->agent->nIsPODO)
		piece_index = PODOBuffer_getPieceIndex4Download(Info->strKey, PrepBuffermap.piece_index, PrepBuffermap.complete_length, PrepBuffermap.dp_index, PrepBuffermap.ds_length, PrepBuffermap.download_map);
	else
		piece_index = prepBuffer_getPieceIndex4Download(Info->strKey, PrepBuffermap.piece_index, PrepBuffermap.complete_length, PrepBuffermap.dp_index, PrepBuffermap.ds_length, PrepBuffermap.download_map);

	if(piece_index >= 0)
	{
		{
			Info->nAddPartnerCount++;
			Info->nRetryCount=0; //RESET retry counter
			
			if (Info->agent->nIsPODO)
				PODOBuffer_setDownloadMapStatusByKey(Info->strKey, piece_index, PIECE_STATUS_DOWNLOADING);
			else 
				prepBuffer_setDownloadMapStatusByKey(Info->strKey, piece_index, PIECE_STATUS_DOWNLOADING);

			Info->nDownSetPiece = piece_index;

			LogPrint(LOG_DEBUG, "recvBuffermap sendGet\n");
			sendGET(Info, piece_index);
		}
	}
	else
	{
		if(Info->nRetryCount >= Info->agent->nMaxRetryCount)
		{
			LogPrint(LOG_DEBUG, "No more Interest\n");
			return -1;
		}
		else
		{
			Info->nRetryCount++;

			SLEEP(1000);

			if (Info->agent->nIsPODO)
				sendREFRESH(Info, PODOBuffer_getCurrentDP(Info->strKey));
			else
				sendREFRESH(Info, prepBuffer_getCurrentDP(Info->strKey));
			
		}
	}

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_BUFFERMAP [END]\n");

	return 1;
}

int sendBUFFERMAP(PeerInfo_t * Info, unsigned int piece_index, unsigned int number) 
{
	int ret;
	ProtocolBuffermap_t prepBuffermap;
	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_BUFFERMAP [START]\n");
	memset(&prepBuffermap, 0, sizeof(ProtocolBuffermap_t));

	Buffermap buffermap;
	buffermap.PieceIndex = piece_index;

	if (Info->agent->nIsPODO)
		PODOBuffer_getDownloadMap4BUFFERMAP(Info->strKey, &prepBuffermap, piece_index, number);
	else
	{
		prepBuffer_getDownloadMap4BUFFERMAP(Info->strKey, &prepBuffermap, piece_index, number);
		buffermap.TimeStamp = (long long)prepBuffer_getPieceDataTimestamp(Info->strKey, piece_index);
	}

	buffermap.CPLength = prepBuffermap.complete_length;
	buffermap.DPIndex = prepBuffermap.dp_index;
	buffermap.DSLength = prepBuffermap.ds_length;

	if (prepBuffermap.ds_length > 0)
	{
		buffermap.BuffermapBin = new char[buffermap.DSLength];
		cpymem(buffermap.BuffermapBin, prepBuffermap.download_map, buffermap.DSLength);
	}

	int len = 0;
	const char* buf = buffermap.GetBin(len);

	ret = send(Info->socket, buf, len, 0);

	if (prepBuffermap.download_map != NULL)
	{
		free(prepBuffermap.download_map);
		prepBuffermap.download_map = NULL;
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_BUFFERMAP [END]\n");
	return 1;	
}

int recvBYE(PeerInfo_t * Info, bsonobj& bson)
{
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_BYE [START]\n");

	/*char *buf = new char[len];
	int ret = recv(Info->socket, buf, len, 0);
	delete[] buf;*/

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_BYE [END]\n");
	return -2;
}

int sendBYE(PeerInfo_t * Info) 
{
	int ret;

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_BYE [START]\n");

	Bye bye;

	int len = 0;
	const char* buf = bye.GetBin(len);
	ret = send(Info->socket, buf, len, 0);
	if(ret <=0 )
	{
		LogPrint(LOG_CRITICAL, "sendBYE : send error\n");
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_BYE [END]\n");

	return 1;
}

int recvPARTNER(PeerInfo_t * Info, bsonobj& bson)
{
	int result;
	ProtocolPartner_t ProtocolPartner;
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_PARTNER [START]\n");
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_PARTNER [partner]\n");
	
	PartnerRequest partnerreq(bson);
	
	ProtocolPartner.starting_piece_index = partnerreq.StartIndex;

	if (Info->prepMode == PREP_SERVER_MODE && Info->agent->nIsPODO)
	{
		LogPrint(LOG_DEBUG, "\t----> PODO Server!! recv PREP_PROTOCOL_PARTNER [partner]\n");
	}
	else
	{
		if (Info->agent->nMaxPartnerCount > Info->agent->recvPartnerMap.size())
		{
			PartnerData_t * partner = (PartnerData_t *)malloc(sizeof(PartnerData_t));
			if (partner != NULL)
			{
				memset(partner, 0, sizeof(PartnerData_t));
				partner->peerData = Info->agent->totalPeerMap[Info->nPeerId];
				partner->socket = Info->socket;

				partner->nNotifyCount = 0;
				partner->notifyTime = GetNTPTimestamp();

				partner->notifyData = NULL;
				Info->nPartnerId = Info->agent->nPartnerIdNext++;

				Info->agent->recvPartnerMutex.lock();
				Info->agent->recvPartnerMap[Info->nPartnerId] = partner;
				Info->agent->recvPartnerMutex.unlock();
			}
		}
	}

	result = Info->nPartnerId < 0 ? 0 : 1;

	if(result == 0)
	{
		LogPrint(LOG_DEBUG, "Num of Partner : %d is larger than %d\n", Info->agent->recvPartnerMap.size(), Info->agent->nMaxPartnerCount);
	}
	else
	{
		LogPrint(LOG_DEBUG, "Adding Partner : %d\n", Info->socket);
	}
	
	sendRESULT(Info, result);

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_PARTNER [END]\n");

	return result;
}

int sendPARTNER(PeerInfo_t * Info, unsigned int starting_piece_index) 
{
	int ret;

	PartnerRequest partnerreq;
	partnerreq.StartIndex = starting_piece_index;

	int len = 0;
	const char *buf = partnerreq.GetBin(len);

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_PARTNER [START]\n");

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_PARTNER [partner]\n");
	ret = send(Info->socket, buf, len, 0);
	if(ret <=0 )
	{
		LogPrint(LOG_CRITICAL, "sendPartner : send error\n");
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_PARTNER [END]\n");

	return 1;
}

int recvRESULT(PeerInfo_t * Info, bsonobj& bson)
{
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_RESULT [START]\n");

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_RESULT [result]\n");

	PartnerResponse partnerrsp(bson);

	if(partnerrsp.Result)
	{
		int min = 9999999;

		PartnerData_t *lower = NULL;

		if (Info->agent->nMaxPartnerCount > Info->agent->sendPartnerMap.size())
		{
			PartnerData_t *partner = (PartnerData_t *)malloc(sizeof(PartnerData_t));
			if (partner != NULL)
			{
				memset(partner, 0, sizeof(PartnerData_t));
				
				partner->nNotifyCount = 0;
				partner->notifyTime = GetNTPTimestamp();

				partner->peerData = Info->agent->totalPeerMap[Info->nPeerId];

				partner->socket = Info->socket;
				partner->notifyData = NULL;
				Info->nPartnerId = Info->agent->nPartnerIdNext++;
				lower = NULL;

				Info->agent->sendPartnerMutex.lock();
				Info->agent->sendPartnerMap[Info->nPartnerId] = partner;
				Info->agent->sendPartnerMutex.unlock();

				LogPrint(LOG_DEBUG, "\t----> sendPartnerData 파트너 연결, nPartnerId : %d\n", Info->nPartnerId);
			}
		}
		else
		{
			Info->agent->sendPartnerMutex.lock();
			
			for (PartnerMapIter it = Info->agent->sendPartnerMap.begin(); it != Info->agent->sendPartnerMap.end(); ++it)
			{
				if (it->second->nNotifyCount < min)
				{
					min = it->second->nNotifyCount;
					lower = it->second;
				}
			}

			Info->agent->sendPartnerMutex.unlock();
		}
		
		if (lower != NULL)
		{
			LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_RESULT [BYE!!!!!!!!!!!!!]\n");
			LogPrint(LOG_CRITICAL, "\t!!!!!! 파트너 개수 제한으로 예전 파트너 삭제. 현재 파트너 개수 : %d !!!!!!!]\n", Info->agent->sendPartnerMap.size());
			Info->agent->sendPartnerMutex.lock();

			lower->nBYE = 1;
			shutdown(lower->socket, 2);
			close(lower->socket);

			Info->agent->sendPartnerMutex.unlock();

			while (Info->agent->sendPartnerMap.size() >= Info->agent->nMaxPartnerCount)
			{
				SLEEP(100);
			}

			PartnerData_t *partner = (PartnerData_t *)malloc(sizeof(PartnerData_t));
			if (partner != NULL)
			{
				memset(partner, 0, sizeof(PartnerData_t));
				
				partner->nNotifyCount = 0;
				partner->notifyTime = GetNTPTimestamp();

				partner->peerData = Info->agent->totalPeerMap[Info->nPeerId];

				partner->socket = Info->socket;
				partner->notifyData = NULL;
				Info->nPartnerId = Info->agent->nPartnerIdNext++;

				Info->agent->sendPartnerMutex.lock();
				Info->agent->sendPartnerMap[Info->nPartnerId] = partner;
				Info->agent->sendPartnerMutex.unlock();

				LogPrint(LOG_DEBUG, "\t----> sendPartnerData 파트너 연결, nPartnerId : %d\n", Info->nPartnerId);
			}
		}
	}

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_RESULT [END]\n");

	return partnerrsp.Result;
}

int sendRESULT(PeerInfo_t * Info, unsigned int result) 
{
	int ret;

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_RESULT [START]\n");

	PartnerResponse partnerrsp;
	partnerrsp.Result = result > 0 ? true : false;

	if (result <= 0)
	{
		partnerrsp.Reason = PARTNER_RESPONSE_REASON_NO_MORE_PARTNER;
	}

	int len = 0;
	const char* buf = partnerrsp.GetBin(len);
	
	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_RESULT [result]\n");
	ret=send(Info->socket, buf, len, 0);
	if(ret <=0 )
	{
		LogPrint(LOG_CRITICAL, "sendRESULT : send error\n");
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_RESULT [START]\n");

	return 1;
}

int recvNOTIFY(PeerInfo_t * Info, bsonobj& bson)
{
	int status = PIECE_STATUS_EMPTY;
	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_NOTIFY [START]\n");

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_NOTIFY [notify]\n");
	
	Notify notify(bson);
	
	if (Info->nPartnerId < 0 || Info->agent->sendPartnerMap.size() <= 0 || Info->agent->sendPartnerMap.find(Info->nPartnerId) == Info->agent->sendPartnerMap.end())
	{
		LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_NOTIFY [END!!!!!!!!!!!!!]\n");
		return 0;
	}

	Info->agent->sendPartnerMap[Info->nPartnerId]->nNotifyCount++;
	Info->agent->sendPartnerMap[Info->nPartnerId]->notifyTime = GetNTPTimestamp();

	if (Info->agent->nIsPODO)
		status = PODOBuffer_getDownloadMapStatusByKey(Info->strKey, notify.PieceIndex);
	else
		status = prepBuffer_getDownloadMapStatusByKey(Info->strKey, notify.PieceIndex);

	if( status == PIECE_STATUS_EMPTY || status == PIECE_STATUS_ERROR)
	{
		if (Info->agent->nIsPODO)
		{
			PODOBuffer_setDownloadMapStatusByKey(Info->strKey, notify.PieceIndex, PIECE_STATUS_DOWNLOADING);

			LogPrint(LOG_DEBUG, "\t----> recv NOTIFY - 내놔 [Piece : %d]\n", notify.PieceIndex);

			LogPrint(LOG_DEBUG, "recvNotify sendGet\n");
			sendGET(Info, notify.PieceIndex);
		}
		else
		{
			if (prepBuffer_getCurrentPP(Info->strKey) < prepBuffer_getCurrentSP(Info->strKey))
			{
				Info->agent->sendPartnerMutex.lock();

				LogPrint(LOG_CRITICAL, "\t!!!!!! PP가 SP 보다 작아서 파트너 삭제 !!!!! \n", notify.PieceIndex);
				Info->agent->sendPartnerMap[Info->nPartnerId]->nBYE = 1;

				Info->agent->sendPartnerMutex.unlock();

				return -1;
			}
			else
			{

				prepBuffer_setDownloadMapStatusByKey(Info->strKey, notify.PieceIndex, PIECE_STATUS_DOWNLOADING);

				Info->nDownSetPiece = notify.PieceIndex;

				LogPrint(LOG_DEBUG, "\t----> recv NOTIFY - 내놔 [Piece : %d]\n", notify.PieceIndex);

				LogPrint(LOG_DEBUG, "recvNotify sendGet\n");
				sendGET(Info, notify.PieceIndex);
			}
		}
	}
	else
	{
		LogPrint(LOG_DEBUG, "\t----> recv NOTIFY - 이미 받은 [Piece : %d]\n", notify.PieceIndex);
	}

	LogPrint(LOG_DEBUG, "\t----> recv PREP_PROTOCOL_NOTIFY [END]\n");

	return 1;
}

int sendNOTIFY(PeerInfo_t * Info, SOCKET socket, unsigned int piece_index) 
{
	int ret;

	Notify notify;
	notify.PieceIndex = piece_index;

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_NOTIFY [START] : %d\n", piece_index);

	int len = 0;
	const char* buf = notify.GetBin(len);

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_NOTIFY [notify]\n");
	ret=send(socket, buf, len, 0);
	if(ret <=0 )
	{
		LogPrint(LOG_CRITICAL, "sendNotify : send error\n");
		return 0;
	}

	LogPrint(LOG_DEBUG, "\t\t----> send PREP_PROTOCOL_NOTIFY [END]\n");
	return 1;
}

#include <stdio.h>
#include <stdlib.h>
#include "commonDefine.h"
#include "PODOBuffer.h"
#include <string>

//using namespace std;

//int PrepAgent_InitPrepAgent(char* strPrepAgentID, unsigned int nPrepAgentPort);
//int PrepAgent_InitPrepNetwork(char* strChannelServerURL, char* strOverlayServerURL);
//int pppggg(char* strChannelServerURL, char* strUserID, char* strSubject, char* strOverlayID);
void PrepAgent_Init();
void PrepAgent_Close();
void PrepAgent_SetBandwidthBps(double upBps, double downBps);
int PrepAgent_SetOverlayBandwidth(char* overlayID, double up, double down);
int PrepAgent_SetOverlayMaxPeerCount(char* overlayID, unsigned int count);
int PrepAgent_PauseChannel(char* strOverlayID, int pause);
char* PrepAgent_CreateChannel(PrepAgentInfo_t prepAgent, char* strSubject, char *strOverlayID, int nCreateDash, char* imageBase64);
ChannelItem_t ** PrepAgent_RetrieveChannelInformation(char* strChannelServerURL, char* strUserID, char* strSubject, int* nCount, char* strOverlayID);
int PrepAgent_DeleteChannel(char* strPAID, char* strCsURL, char* strOsURL, char* strOverlayID);
//OverlayItem_t ** PrepAgent_RetrieveOverlayInformation(char* strOverlayServerURL, char* strOverlayID, int* nCount, char* strMyPAID);
void PrepAgent_FreeChannelItem(ChannelItem_t ** item, int cnt);
void PrepAgent_FreeOverlayItem(OverlayItem_t ** item, int cnt);
int PrepAgent_ViewChannel(char* strPAID, char* strOverlayServerURL, char* strOverlayID, unsigned int nAgentPort, unsigned int nRecordPort, unsigned int nPieceSize);
int PrepAgent_JoinChannel(const char* strPAID, const char* strOverlayServerURL, const char* strOverlayID, unsigned int nAgentPort, unsigned int nRecordPort, unsigned int nCommunicatePort, unsigned int nPieceSize, int outfile, int pamInterval, std::string pamsURL, int peerType);
int PrepAgent_LeaveChannel(const char* strPAID, const char* strOverlayServerURL, const char* strOverlayID);
void *RecordThread(void *pInfo);
void *ServerThread(void *pInfo);
void *CommunicateThread(void *pInfo);
void *PAMReportThread(void *pInfo);
//void *ServerPeerThread(void *pInfo);
void *PlayThread(void *pInfo);
void *VirtualPlayThread(void *pInfo);
void *SpeedThread(void *pInfo);
void *ClientThread(void *pInfo);
//void *ClientPeerThread(void *pInfo);
void *TotalPeerThread(void *pInfo);
void ProcessPeer(void *pInfo, int nTimeout);
int PrepAgent_RunPrepAgent(const char* strPAID, unsigned int nRecordPort, unsigned int nPeerPort, unsigned int nCommunicatePort, const char* strOverlayID, unsigned int nPieceSize, int pamInterval, std::string pamsURL, int peerType, const char* overlayURL);
void PrepAgent_StopPrepAgent(const char* strOverlayID, int removeData);
//double PrepAgent_GetSpeed(char* strOverlayID);
//void PrepAgent_SetSpeedCheck(int chk);
Progress_t* PrepAgent_GetStatus(char* overlayID);
Property_t* PrepAgent_GetProperty(char* overlayID);
FileInfo_t** PrepAgent_GetFileInfos(char* overlayID, int* cnt);

//typedef void (__stdcall *PrepDelegate)(char* key, char* overlayId, char* peerId, char* remotePeerId, unsigned int pieceId, unsigned int pieceSize);

//void PrepAgent_SetCallback(PrepDelegate pd);
int PrepAgent_RunPODOAgent(char* strPAID, unsigned int nPeerPort, char* strOverlayID, unsigned int nPieceSize, unsigned int nFileCount, FileInfo_t** fileInfos, int totalPieceCount, char* downDir, char* completeDir, unsigned int nVersion, unsigned int nIsServer);
int PrepAgent_UpdatePODOAgent(char* strOverlayID, unsigned int nFileCount, FileInfo_t** fileInfos, int totalPieceCount, unsigned int nVersion);
//OverlayItem_t ** PrepAgent_RetrievePODOOverlayInformation(char* strOverlayServerURL, char* strOverlayID, int* nCount, char* strMyPAID);
int PrepAgent_JoinPODOChannel(char* strPAID, char* strOverlayServerURL, char* strOverlayID, unsigned int nAgentPort, unsigned int nPieceSize, unsigned int nFileCount, FileInfo_t** fileInfos, int nTotalPieceCount, char* downDir, char* completeDir, int nVersion);
void PrepAgent_PODOInit();
void PrepAgent_SetPlaySync(int dfrag, int dtime, int playsync);

#include "prepAgentManager.h"

#ifdef WIN32
#define _CRTDBG_MAP_ALLOC
#include "crtdbg.h"
#include <winsock.h>
#define close(x)			closesocket(x)
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <signal.h>
#define SOCKET_ERROR            (-1)
#define TRUE 1
#define FALSE 0
#endif
#include "string.h"
#include <sstream>

#include "commonDefine.h"
#include "overlayAction.h"
#include "prepBuffer.h"
#include "PODOBuffer.h"
#include "prepProtocol.h"
#include "prepProtocolControl.h"
#include "NetworkUtil.h"
#include "commonStruct.h"
#include "Protocol/JsonKey.h"
#include "HttpREST.h"
#include "Util.h"

#define CONF_KEY_BUFFER_SIZE			"[BUFFER_SIZE]"
#define CONF_KEY_MAX_PEER_COUNT			"[MAX_PEER_COUNT]"
#define CONF_KEY_MAX_AGENT_COUNT		"[MAX_AGENT_COUNT]"
#define CONF_KEY_EMPTY_SECTION_SIZE		"[EMPTY_SECTION_SIZE]"
#define CONF_KEY_MAX_PARTNER_COUNT		"[MAX_PARTNER_COUNT]"
#define CONF_KEY_MAX_RETRY_COUNT		"[MAX_RETRY_COUNT]"
#define CONF_KEY_DOWNLOAD_WINDOW_SIZE	"[DOWNLOAD_WINDOW_SIZE]"
#define CONF_KEY_MAX_SKIP_COUNT			"[MAX_SKIP_COUNT]"
#define CONF_KEY_ADD_PARTNER_COUNT		"[ADD_PARTNER_COUNT]"
#define CONF_KEY_MAX_UPLOAD_BYTE		"[MAX_UPLOAD_BYTE]"
#define CONF_KEY_MAX_DOWNLOAD_BYTE		"[MAX_DOWNLOAD_BYTE]"
#define CONF_KEY_SP_START_PERCENT		"[SP_START_PERCENT]"
#define CONF_LOG_PRINT_LEVEL			"[LOG_PRINT_LEVEL]"
#define CONF_SIMULATION_LOG_PRINT		"[SIMULATION_LOG_PRINT]"
#define CONF_DTIME						"[CONF_DTIME]"
#define CONF_DFRAG						"[CONF_DFRAG]"
#define CONF_PLAYSYNC					"[CONF_PLAYSYNC]"
#define CONF_USE_PELLO					"[USE_PELLO]"
#define CONF_USE_NTPTIMESTAMP			"[USE_NTPTIMESTAMP]"
#define CONF_PARTNER_TIMEOUT			"[PARTNER_TIMEOUT]"

PrepAgent_t **gPrepAgentArray;
pthread_t gSpeedHandle;

static double gDownloadBps = 0;
static double gDownloadBytes = 0;
static double gSecDownloadBytes = 0;

static double gUploadBps = 0;
static double gUploadBytes = 0;
static double gSecUploadBytes = 0;

static double gUploadLimitBps = 0;
static double gDownloadLimitBps = 0;

static unsigned int gnBufferSize = 300;
static unsigned int gnMaxPeerCount = 50;
static unsigned int gnMaxAgentCount = 2;
static unsigned int gnMaxPartnerCount = 10;
static unsigned short gnMaxRetryCount = 5;
static unsigned int gnEmptySectionSize = 10;
static unsigned int gnDownloadWindowSize = 30;
static unsigned int gnMaxSkipCount = 3;
static unsigned int gnAddPartnerCount = 3;

static unsigned int gnCurrentAgentCount = 0;

static unsigned short gnSpStartPercent = 10;
static unsigned int gnLogPrintLevel = LOG_WARNING;
static unsigned int gnSimulationLogPrint = 0;
static unsigned int gnDtime = 0;
static unsigned int gnPlaySync = 0;
static unsigned int gnDfrag = 0;

static unsigned int gnUsePello = 0;

static unsigned int gnUseNTPTimestamp = 1;

static int gStopPrepAgent = 0;

static int gPartnerTimeout = 0;
static short gPartnerTimeoutMode = MODE_TIMEOUT_SEC;

//static PrepDelegate PrepProgress;

void _readConfigFile()
{
	LogPrint(LOG_DEBUG, "conf!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
	FILE *fp;
	char buf[80] = { 0, };

	fp=fopen("prepagent.conf", "r");
	if(fp != NULL) 
	{
		LogPrint(LOG_DEBUG, "read!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
		int tmpval = 0;
		while(!feof(fp))
		{
			if (fgets(buf, 80, fp) == NULL)
				break;

			std::string line(buf);

			LogPrint(LOG_DEBUG, buf);
			LogPrint(LOG_DEBUG, "\n");

			if (line[0] == '#') continue;

			if (!line.find(CONF_KEY_BUFFER_SIZE))
			{
				LogPrint(LOG_DEBUG, "11111  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 2000)
						{
							gnBufferSize = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_MAX_AGENT_COUNT))
			{
				LogPrint(LOG_DEBUG, "4444  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 100)
						{
							gnMaxAgentCount = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_MAX_PEER_COUNT))
			{
				LogPrint(LOG_DEBUG, "5555  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 100)
						{
							gnMaxPeerCount = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_EMPTY_SECTION_SIZE))
			{
				LogPrint(LOG_DEBUG, "6666  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 1000)
						{
							gnEmptySectionSize = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_MAX_PARTNER_COUNT))
			{
				LogPrint(LOG_DEBUG, "7777  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 1000)
						{
							gnMaxPartnerCount = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_MAX_RETRY_COUNT))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 100)
						{
							gnMaxRetryCount = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_DOWNLOAD_WINDOW_SIZE))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 1000)
						{
							gnDownloadWindowSize = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_MAX_SKIP_COUNT))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 100)
						{
							gnMaxSkipCount = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_ADD_PARTNER_COUNT))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval > 0 && tmpval < 100)
						{
							gnAddPartnerCount = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_MAX_UPLOAD_BYTE))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 9)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval < 1000000000)
						{
							gUploadLimitBps = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_MAX_DOWNLOAD_BYTE))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 9)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval < 1000000000)
						{
							gDownloadLimitBps = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_KEY_SP_START_PERCENT))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval <= 100)
						{
							gnSpStartPercent = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_LOG_PRINT_LEVEL))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval <= 10)
						{
							gnLogPrintLevel = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_SIMULATION_LOG_PRINT))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval <= 10)
						{
							gnSimulationLogPrint = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_DTIME))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 9)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval <= 1000 * 60 * 10)
						{
							gnDtime = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_DFRAG))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval <= 1000)
						{
							gnDfrag = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_PLAYSYNC))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval <= 1)
						{
							gnPlaySync = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_USE_PELLO))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval <= 1)
						{
							gnUsePello = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_USE_NTPTIMESTAMP))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					if (strlen_s(buf) < 5)
					{
						tmpval = atoi(buf);

						if (tmpval >= 0 && tmpval <= 1)
						{
							gnUseNTPTimestamp = tmpval;
						}
					}
				}
			}
			else if (!line.find(CONF_PARTNER_TIMEOUT))
			{
				if (fgets(buf, 80, fp) == NULL)
					break;
				else
				{
					int len = strlen_s(buf);
					if (len < 5)
					{
						if (buf[len - 1] == 'x')
						{
							gPartnerTimeoutMode = MODE_TIMEOUT_PIECE;
						}
						else if (buf[len - 1] == 's')
						{
							gPartnerTimeoutMode = MODE_TIMEOUT_SEC;
						}

						buf[len - 1] = '\0';

						tmpval = atoi(buf);

						if (tmpval >= 0)
						{
							gPartnerTimeout = tmpval;

							if (gPartnerTimeoutMode == MODE_TIMEOUT_PIECE)
							{
								gPartnerTimeout *= -1;
							}
						}
					}
				}
			}
		}

		fclose(fp);
	}

	if (gnBufferSize < 10)
	{
		gnBufferSize = 10;
	}

	if (gnDownloadWindowSize > gnBufferSize - 1)
	{
		gnDownloadWindowSize = gnBufferSize - 1;
	}

	if (gnDownloadWindowSize + gnEmptySectionSize > gnBufferSize)
	{
		if (gnBufferSize - gnDownloadWindowSize < 1000000000)
			gnEmptySectionSize = gnBufferSize - gnDownloadWindowSize;
	}
}

int _checkInitData(PrepAgentInfo_t prepAgent)
{
	if (prepAgent.strPAID == NULL || !strlen_s(prepAgent.strPAID))
		return FAIL;

	if (prepAgent.strLocalIP == NULL || !strlen_s(prepAgent.strLocalIP))
		return FAIL;

	if (prepAgent.nLocalPort <= 0)
		return FAIL;

	if (prepAgent.strChannelServerURL == NULL || !strlen_s(prepAgent.strChannelServerURL))
		return FAIL;

	if (prepAgent.strOverlayServerURL == NULL || !strlen_s(prepAgent.strOverlayServerURL))
		return FAIL;

	return SUCCESS;
}

int _getServerInfoInURL(char* url, char* ip, unsigned int *port, char* path)
{
	//char tmp[80], tmp2[10], tmp3[80];
	char *ch = strstr(url, "http://");

	if (ch != NULL)
	{
		url += strlen_s("http://");
	}

	/*
	strcpy(tmp, url);
	strcpy(tmp3, url);

	strcpy(ip, strtok(tmp, ":"));

	//sscanf(url, "%[^':']", ip);

	url += strlen(ip) + 1;
	//sscanf(url, "%[^'/']", tmp);
	strcpy(tmp, url);

	strcpy(tmp2, strtok(tmp, "/"));

	*port = atoi(tmp2);
	url += strlen(tmp2);
	//sscanf(url, "%s", path);
	strcpy(path, url);
	*/

	std::string stmp = url;

	int sidx = stmp.find(":");
	int eidx = stmp.find("/");

	std::string ipstr = stmp.substr(0, sidx);

	sprintf_s(ip, 32, ipstr.c_str());

	std::string portstr = stmp.substr(sidx + 1, eidx - sidx - 1);

	*port = atoi(portstr.c_str());

	std::string pathstr = stmp.substr(eidx);

	sprintf_s(path, 128, pathstr.c_str());

	return SUCCESS;
}

PrepAgent_t * _newAgent(const char* strOverlayID, const char* strPAID, unsigned int nPieceSize, unsigned int nRecordPort, unsigned int nPeerPort, unsigned int nCommunicatePort, int outfile)
{
	unsigned int i=0;
	PrepAgent_t * agent = NULL;

	if (gnMaxAgentCount <= gnCurrentAgentCount)
	{
		return NULL;
	}

	if (!prepBuffer_newBuffer(strOverlayID, gnBufferSize, nPieceSize, gnEmptySectionSize, gnDownloadWindowSize, outfile, gnSpStartPercent))
	{
		return NULL;
	}

	agent = new PrepAgent_t();

	//agent = (PrepAgent_t *)malloc(sizeof(PrepAgent_t));
	//memset(agent, 0, sizeof(PrepAgent_t));

	agent->strOverlayID = _strdup(strOverlayID);
	agent->strPAID = _strdup(strPAID);
	agent->nPieceSize = nPieceSize;
	agent->nRecordPort = nRecordPort;
	agent->nPeerPort = nPeerPort;
	agent->nCommunicatePort = nCommunicatePort;
	agent->nAddPartnerCount = gnAddPartnerCount;
	/*agent->sendPeerData = (PeerData_t **)malloc(sizeof(PeerData_t *) * gnMaxPeerCount);
	memset(agent->sendPeerData, 0, sizeof(PeerData_t *) * gnMaxPeerCount);
	agent->recvPeerData = (PeerData_t **)malloc(sizeof(PeerData_t *) * gnMaxPeerCount);
	memset(agent->recvPeerData, 0, sizeof(PeerData_t *) * gnMaxPeerCount);*/

	/*agent->sendPartnerData = (PartnerData_t **)malloc(sizeof(PartnerData_t *) * gnMaxPartnerCount);
	memset(agent->sendPartnerData, 0, sizeof(PartnerData_t *) * gnMaxPartnerCount);
	agent->recvPartnerData = (PartnerData_t **)malloc(sizeof(PartnerData_t *) * gnMaxPartnerCount);
	memset(agent->recvPartnerData, 0, sizeof(PartnerData_t *) * gnMaxPartnerCount);*/

	agent->nMaxPartnerCount = gnMaxPartnerCount;
	agent->nMaxPeerCount = gnMaxPeerCount;
	agent->nMaxRetryCount = gnMaxRetryCount;

	agent->dAllDownloadBpsLimit = gDownloadLimitBps;
	agent->dAllUploadBpsLimit = gUploadLimitBps;

	agent->nSpStartPercent = gnSpStartPercent;

	agent->nIsHEVC = outfile;

	agent->nUsePello = gnUsePello;

	agent->nPartnerTimeoutMode = gPartnerTimeoutMode;
	agent->nPartnerTimeout = gPartnerTimeout;
	
	if (gPartnerTimeoutMode == MODE_TIMEOUT_SEC)
	{
		agent->nPartnerTimeout *= 1000;
	}

	if (gnPlaySync > 0)
	{
		agent->nStartTimestamp = GetNTPTimestamp() - (gnDtime * 1000);

		LogPrint(LOG_DEBUG, "agent->nStartTimestamp : %.0lf", agent->nStartTimestamp);
	}

	for (i=0; i<gnMaxAgentCount; i++)
	{
		if (gPrepAgentArray[i] == NULL)
		{
			gPrepAgentArray[i] = agent;
			break;
		}
	}

	gnCurrentAgentCount++;

	return agent;
}

PrepAgent_t * _newAgentPODO(char* strOverlayID, char* strPAID, unsigned int nPieceSize, unsigned int nPeerPort, unsigned int nFileCount, FileInfo_t** fileInfos, int nTotalPieceCount, char* downDir, char* completeDir, int nVersion, int nIsServer)
{
	unsigned int i=0;
	PrepAgent_t * agent = NULL;

	if (gnMaxAgentCount <= gnCurrentAgentCount)
	{
		return NULL;
	}

	if (!PODOBuffer_newBuffer(strOverlayID, nPieceSize, nFileCount, fileInfos, nTotalPieceCount, downDir, completeDir, nVersion, nIsServer))
	{
		return NULL;
	}

	agent = new PrepAgent_t();
	//agent = (PrepAgent_t *)malloc(sizeof(PrepAgent_t));
	//memset(agent, 0, sizeof(PrepAgent_t));

	agent->strOverlayID = _strdup(strOverlayID);
	agent->strPAID = _strdup(strPAID);
	agent->nPieceSize = nPieceSize;
	agent->nPeerPort = nPeerPort;
	agent->nAddPartnerCount = gnAddPartnerCount;
	/*agent->sendPeerData = (PeerData_t **)malloc(sizeof(PeerData_t *) * gnMaxPeerCount);
	memset(agent->sendPeerData, 0, sizeof(PeerData_t *) * gnMaxPeerCount);
	agent->recvPeerData = (PeerData_t **)malloc(sizeof(PeerData_t *) * gnMaxPeerCount);
	memset(agent->recvPeerData, 0, sizeof(PeerData_t *) * gnMaxPeerCount);*/

	/*agent->sendPartnerData = (PartnerData_t **)malloc(sizeof(PartnerData_t *) * gnMaxPartnerCount);
	memset(agent->sendPartnerData, 0, sizeof(PartnerData_t *) * gnMaxPartnerCount);
	agent->recvPartnerData = (PartnerData_t **)malloc(sizeof(PartnerData_t *) * gnMaxPartnerCount);
	memset(agent->recvPartnerData, 0, sizeof(PartnerData_t *) * gnMaxPartnerCount);*/
	
	agent->nMaxPartnerCount = gnMaxPartnerCount;
	agent->nMaxPeerCount = gnMaxPeerCount;
	agent->nMaxRetryCount = gnMaxRetryCount;

	agent->dAllDownloadBpsLimit = gDownloadLimitBps;
	agent->dAllUploadBpsLimit = gUploadLimitBps;

	agent->nIsPODO = 1;

	for (i=0; i<gnMaxAgentCount; i++)
	{
		if (gPrepAgentArray[i] == NULL)
		{
			gPrepAgentArray[i] = agent;
			break;
		}
	}

	gnCurrentAgentCount++;

	return agent;
}

PrepAgent_t * _getAgentByKey(char *key)
{
	unsigned int i=0;

	if (gPrepAgentArray == NULL) return NULL;

	if (key == NULL) return NULL;

	for (i=0; i<gnMaxAgentCount; i++)
	{
		if (gPrepAgentArray[i] != NULL)
		{
			if (!strcmp(gPrepAgentArray[i]->strOverlayID, key))
			{
				return gPrepAgentArray[i];
			}
		}
	}

	return NULL;
}

void *_sleepThread(void *p)
{
	PrepAgent_t * agent = NULL;
	ClientInfo_t *cInfo = (ClientInfo_t *)p;
	//pthread_cond_t clientCond = cInfo->ClientCond;
	unsigned int nMilliseconds = cInfo->waitSecond * 1000;
	unsigned int count = 0;

	if (cInfo != NULL && cInfo->strKey != NULL && strlen_s(cInfo->strKey) > 0)
	{
		agent = _getAgentByKey(cInfo->strKey);
	}

	while(count < nMilliseconds && agent != NULL && agent->nClose != 1) {
		SLEEP(10);
		count += 10;
	}

	if(agent != NULL && agent->nClose != 1) {
		cInfo->ClientFireTID = NULL;
		pthread_cond_signal(&cInfo->ClientCond);
	}

	return NULL;
}

void _fireNextEvent(ClientInfo_t *cInfo, unsigned int second) {
	if (cInfo != NULL)
	{
		if(cInfo->ClientFireTID == NULL) {
			cInfo->waitSecond = second;
			cInfo->ClientFireTID = PTHREAD_CREATE(_sleepThread, (void*)cInfo);
		}
	}
}

void _cleanupServerThread(void* arg)
{
	//int i=0;

	PrepAgent_t * agent = NULL;
	ServerInfo_t *Info = (ServerInfo_t *)arg;

	shutdown(Info->socket, 2);
	close(Info->socket);

	agent = _getAgentByKey(Info->strKey);

	if (Info->strKey != NULL && strlen_s(Info->strKey))
	{
		free(Info->strKey);
	}

	free(Info);

	agent->ServerHandle = NULL;

	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
	LogPrint(LOG_DEBUG, "ServerThread 메인이 종료 되었습니다.\n");
	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
}

void _cleanupCommunicateThread(void* arg)
{
	//int i = 0;

	PrepAgent_t * agent = NULL;
	ServerInfo_t *Info = (ServerInfo_t *)arg;

	shutdown(Info->socket, 2);
	close(Info->socket);

	agent = _getAgentByKey(Info->strKey);

	if (Info->strKey != NULL && strlen_s(Info->strKey))
	{
		free(Info->strKey);
	}

	free(Info);

	agent->CommunicateHandle = NULL;

	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
	LogPrint(LOG_DEBUG, "CommunicateThread 종료 되었습니다.\n");
	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
}

void _cleanupPAMReportThread(void* arg)
{
	//int i = 0;

	PrepAgent_t * agent = NULL;
	PAMInfo_t *Info = (PAMInfo_t *)arg;

	agent = _getAgentByKey(Info->strKey);

	int resCode = 0;

	if (Info->strPAMSURL != NULL && strlen_s(Info->strPAMSURL) > 2)
	{
		std::string rslt = HttpREST::Delete(Info->strPAMSURL, "", &resCode);
	}
	
	if (Info->strKey != NULL && strlen_s(Info->strKey))
	{
		free(Info->strKey);
	}

	if (Info->strPAMSURL != NULL && strlen_s(Info->strPAMSURL))
	{
		free(Info->strPAMSURL);
	}

	free(Info);

	agent->PAMReoprtHandle = NULL;

	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
	LogPrint(LOG_DEBUG, "PAMReoprtThread 종료 되었습니다.\n");
	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
}

void _cleanupRecordThread(void* arg)
{
	//int i=0;

	PrepAgent_t * agent = NULL;
	ServerInfo_t *Info = (ServerInfo_t *)arg;

	shutdown(Info->socket, 2);
	close(Info->socket);

	agent = _getAgentByKey(Info->strKey);

	if (Info->strKey != NULL && strlen_s(Info->strKey))
	{
		free(Info->strKey);
	}

	free(Info);

	agent->recordHandle = NULL;

	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
	LogPrint(LOG_DEBUG, "RecordThread 가 종료 되었습니다.\n");
	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
}

void _cleanupPlayThread(void* arg)
{
	PrepAgent_t * agent = NULL;
	ClientInfo_t * playInfo = (ClientInfo_t *)arg;
	agent = _getAgentByKey(playInfo->strKey);

	//close(playInfo->socket);
	shutdown(agent->PlayServerSocket, 2);
	close(agent->PlayServerSocket);
	shutdown(agent->PlaySocket, 2);
	close(agent->PlaySocket);

	if (playInfo->strKey != NULL && strlen_s(playInfo->strKey))
	{
		free(playInfo->strKey);
	}

	free(playInfo);

	agent->PlayHandle = NULL;

	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
	LogPrint(LOG_DEBUG, "PlayThread가 종료 되었습니다.\n");
	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
}

void _cleanupVirtualPlayThread(void* arg)
{
	PrepAgent_t * agent = NULL;
	ClientInfo_t * playInfo = (ClientInfo_t *)arg;
	agent = _getAgentByKey(playInfo->strKey);

	if (playInfo->strKey != NULL && strlen_s(playInfo->strKey))
	{
		free(playInfo->strKey);
	}

	free(playInfo);

	agent->PlayHandle = NULL;

	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
	LogPrint(LOG_DEBUG, "VirtualPlayThread가 종료 되었습니다.\n");
	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
}

void _cleanupSpeedThread(void* arg)
{
	gSpeedHandle = NULL;

	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
	LogPrint(LOG_DEBUG, "SpeedThread가 종료 되었습니다.\n");
	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
}


void _cleanupClientThread(void* arg)
{
	//int i=0;

	PrepAgent_t * agent = NULL;
	ClientInfo_t *Info = (ClientInfo_t *)arg;

	shutdown(Info->socket, 2);
	close(Info->socket);

	agent = _getAgentByKey(Info->strKey);

	if (Info->strKey != NULL && strlen_s(Info->strKey))
	{
		free(Info->strKey);
	}

	if (Info->strOverlayID != NULL && strlen_s(Info->strOverlayID))
	{
		free(Info->strOverlayID);
	}

	if (Info->strServerIP != NULL && strlen_s(Info->strServerIP))
	{
		free(Info->strServerIP);
	}

	if (Info->strServerPath != NULL && strlen_s(Info->strServerPath))
	{
		free(Info->strServerPath);
	}

	free(Info);
	Info = NULL;

	agent->ClientInfo = NULL;

	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
	LogPrint(LOG_DEBUG, "ClientThread 메인이 종료 되었습니다.\n");
	LogPrint(LOG_DEBUG, "----------------------------------------------------------------------\n");
}

void _cleanupTotalPeerThread(void* arg)
{
	//int i=0;

	PrepAgent_t * agent = NULL;
	PeerInfo_t *Info = (PeerInfo_t *)arg;

	shutdown(Info->socket, 2);
	close(Info->socket);

	if (Info->nDownSetPiece >= 0)
	{
		prepBuffer_setDownloadMapStatusByKey(Info->strKey, Info->nDownSetPiece, PIECE_STATUS_ERROR);
	}

	agent = _getAgentByKey(Info->strKey);

	if (Info->nPartnerId < 0)
	{
		if (Info->prepMode == PREP_SERVER_MODE)
		{
			agent->nCurRecvPeerCount--;
		}
		else
		{
			agent->nCurSendPeerCount--;
		}

		agent->totalPeerMutex.lock();
		PeerMapIter it = agent->totalPeerMap.find(Info->nPeerId);

		if (it != agent->totalPeerMap.end())
		{
			free(it->second);
			agent->totalPeerMap.erase(it);
		}
		agent->totalPeerMutex.unlock();
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

	if (Info->nPartnerId >= 0)
	{
		if (Info->prepMode == PREP_SERVER_MODE)
		{
			Info->agent->recvPartnerMutex.lock();
			PartnerMapIter it = Info->agent->recvPartnerMap.find(Info->nPartnerId);

			if (it != Info->agent->recvPartnerMap.end() && it->second != NULL)
			{
				if (it->second->notifyData != NULL)
				{
					while (1)
					{
						NotifyData_t * data = it->second->notifyData;

						if (data == NULL)
						{
							break;
						}

						it->second->notifyData = data->next;

						free(data);
					}
				}

				if (it->second->peerData != NULL)
				{
					free(it->second->peerData);
				}

				free(it->second);
				Info->agent->recvPartnerMap.erase(it);
			}
			Info->agent->recvPartnerMutex.unlock();
		}
		else
		{
			Info->agent->sendPartnerMutex.lock();
			PartnerMapIter it = Info->agent->sendPartnerMap.find(Info->nPartnerId);

			if (it != Info->agent->sendPartnerMap.end() && it->second != NULL)
			{
				if (it->second->notifyData != NULL)
				{
					while (1)
					{
						NotifyData_t * data = it->second->notifyData;

						if (data == NULL)
						{
							break;
						}

						it->second->notifyData = data->next;

						free(data);
					}
				}

				if (it->second->peerData != NULL)
				{
					free(it->second->peerData);
				}

				free(it->second);

				Info->agent->sendPartnerMap.erase(it);
			}
			Info->agent->sendPartnerMutex.unlock();
		}
	}

	if (Info->strKey != NULL && strlen_s(Info->strKey))
	{
		free(Info->strKey);
	}

	if (Info->ip != NULL)
	{
		free(Info->ip);
	}

	if (Info->id != NULL)
	{
		free(Info->id);
	}

	_fireNextEvent(Info->parentClient, 0);

	free(Info);

	LogPrint(LOG_INFO, "----------------------------------------------------------------------\n");
	LogPrint(LOG_INFO, "TotalPeerThread가 종료 되었습니다.\n");
	LogPrint(LOG_INFO, "----------------------------------------------------------------------\n");
}

pthread_t _clientManager_Startup(ClientInfo_t *Info)
{
	pthread_t ClientManagerTID;
	pthread_attr_t 	ClientManagerAttr;

	if( pthread_mutex_init(&Info->ClientMutex,NULL) != 0 )
	{
		return NULL;
	}
	if( pthread_cond_init(&Info->ClientCond,NULL) != 0 )
	{
		pthread_mutex_destroy(&Info->ClientMutex);

		return NULL;
	}

	pthread_attr_init(&ClientManagerAttr);
	pthread_attr_setdetachstate(&ClientManagerAttr,PTHREAD_CREATE_DETACHED);

	if( pthread_create(&ClientManagerTID,&ClientManagerAttr,ClientThread,Info) != 0 )
	{
		pthread_mutex_destroy(&Info->ClientMutex);
		pthread_attr_destroy(&ClientManagerAttr);
		return NULL;
	}

	_fireNextEvent(Info, 1);

	Info->ClientHandle = ClientManagerTID;

	return ClientManagerTID;
}

void _clientPeerStart(void *pInfo)
{
	PeerInfo_t *Info = (PeerInfo_t *)pInfo;
	LogPrint(LOG_DEBUG, "-------------------------------------------\n");
	LogPrint(LOG_DEBUG, "socket: %d, Hello send.\n", Info->socket);
	LogPrint(LOG_DEBUG, "-------------------------------------------\n");

	if (Info->agent->nAgentType == PAMP_TYPE_SEEDER || Info->agent->nUsePello > 0)
	{
		sendPELLO(Info);
	}
	else
	{
		sendHELLO(Info, 0);
	}
}

//////////////////////////////////////////////////////////////////////////

void PrepAgent_Init()
{
	//int i=0;
	_readConfigFile();

	SetLogLevel(gnLogPrintLevel);
	SetSimulationLogPrint(gnSimulationLogPrint);
	SetNTPTimestamp(gnUseNTPTimestamp);

	LogPrint(LOG_DEBUG, "Init!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");

	gSpeedHandle = NULL;

	gPrepAgentArray = new PrepAgent_t*[gnMaxAgentCount];
	//gPrepAgentArray = (PrepAgent_t **)malloc(sizeof(PrepAgent_t *) * gnMaxAgentCount);
	memset(gPrepAgentArray, 0, sizeof(PrepAgent_t *) * gnMaxAgentCount);

	prepBuffer_initBufferArray(gnMaxAgentCount);

	HTTP_Startup();
}

void PrepAgent_PODOInit()
{
	//int i=0;
	_readConfigFile();

	LogPrint(LOG_DEBUG, "Init!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");

	gSpeedHandle = NULL;
	
	gPrepAgentArray = new PrepAgent_t*[gnMaxAgentCount];
	//gPrepAgentArray = (PrepAgent_t **)malloc(sizeof(PrepAgent_t *) * gnMaxAgentCount);
	memset(gPrepAgentArray, 0, sizeof(PrepAgent_t *) * gnMaxAgentCount);

	PODOBuffer_initBufferArray(gnMaxAgentCount);
	
	HTTP_Startup();
}

void PrepAgent_SetBandwidthBps(double upBps, double downBps)
{
	int i = 0;
	gUploadLimitBps = upBps;
	gDownloadLimitBps = downBps;
	
	if (gPrepAgentArray != NULL)
	{
		for (i = 0; i < gnMaxAgentCount; i++)
		{
			if (gPrepAgentArray[i] != NULL)
			{
				gPrepAgentArray[i]->dAllDownloadBpsLimit = gDownloadLimitBps;
				gPrepAgentArray[i]->dAllUploadBpsLimit = gUploadLimitBps;
			}
		}
	}

	//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_BANDWIDTH, NULL, NULL, NULL, (unsigned int)upBps, (unsigned int)downBps);
}

void PrepAgent_Close()
{
	unsigned int i=0;
	//unsigned int j=0;

	LogPrint(LOG_DEBUG, "PrepAgent_Close start!!\n");

	gStopPrepAgent = 1;

	for (i=0; i<gnMaxAgentCount; i++)
	{
		if (gPrepAgentArray[i] != NULL)
		{
			gPrepAgentArray[i]->nClose = 1;

			if (gPrepAgentArray[i]->recordHandle != NULL)
			{
				shutdown(gPrepAgentArray[i]->recordSocket, 2);
				close(gPrepAgentArray[i]->recordSocket);
				while(gPrepAgentArray[i]->recordHandle != NULL) {
					SLEEP(100);
				}
			}
			LogPrint(LOG_DEBUG, "PrepAgent_Close - record end!!\n");
			if (gPrepAgentArray[i]->ServerHandle != NULL)
			{
				shutdown(gPrepAgentArray[i]->ServerSocket, 2);
				close(gPrepAgentArray[i]->ServerSocket);
				while(gPrepAgentArray[i]->ServerHandle != NULL) {
					SLEEP(100);
				}
			}
			if (gPrepAgentArray[i]->CommunicateHandle != NULL)
			{
				shutdown(gPrepAgentArray[i]->CommunicateSocket, 2);
				close(gPrepAgentArray[i]->CommunicateSocket);
				while (gPrepAgentArray[i]->CommunicateHandle != NULL) {
					SLEEP(100);
				}
			}
			if (gPrepAgentArray[i]->PAMReoprtHandle != NULL)
			{
				while (gPrepAgentArray[i]->PAMReoprtHandle != NULL) {
					SLEEP(100);
				}
			}
			LogPrint(LOG_DEBUG, "PrepAgent_Close - server end!!\n");
			if (gPrepAgentArray[i]->ClientInfo != NULL)
			{
				while(gPrepAgentArray[i]->ClientInfo != NULL)
				{
					SLEEP(100);

					if (gPrepAgentArray[i]->ClientInfo != NULL)
					{
						pthread_cond_signal(&gPrepAgentArray[i]->ClientInfo->ClientCond);
					}
				}
			}
			LogPrint(LOG_DEBUG, "PrepAgent_Close - client end!!\n");

			while (!gPrepAgentArray[i]->totalPeerMap.empty())
			{
				SLEEP(100);
			}
			
			LogPrint(LOG_DEBUG, "PrepAgent_Close - peer end!!\n");

			while (1)
			{
				gPrepAgentArray[i]->sendPartnerMutex.lock();
				int size = gPrepAgentArray[i]->sendPartnerMap.size();

				if (size <= 0)
				{
					gPrepAgentArray[i]->sendPartnerMutex.unlock();
					break;
				}

				PartnerData_t *partner = gPrepAgentArray[i]->sendPartnerMap.begin()->second;
				gPrepAgentArray[i]->sendPartnerMutex.unlock();

				shutdown(partner->socket, 2);
				close(partner->socket);
				while (size <= gPrepAgentArray[i]->sendPartnerMap.size())
				{
					SLEEP(100);
				}
			}

			while (1)
			{
				gPrepAgentArray[i]->recvPartnerMutex.lock();
				int size = gPrepAgentArray[i]->recvPartnerMap.size();

				if (size <= 0)
				{
					gPrepAgentArray[i]->recvPartnerMutex.unlock();
					break;
				}

				PartnerData_t *partner = gPrepAgentArray[i]->recvPartnerMap.begin()->second;
				gPrepAgentArray[i]->recvPartnerMutex.unlock();

				shutdown(partner->socket, 2);
				close(partner->socket);
				while (size <= gPrepAgentArray[i]->recvPartnerMap.size())
				{
					SLEEP(100);
				}
			}

			LogPrint(LOG_DEBUG, "PrepAgent_Close - partner end!!\n");

			if (gPrepAgentArray[i]->PlayHandle != NULL)
			{
				if (gPrepAgentArray[i]->PlayServerSocket > 0)
				{
					shutdown(gPrepAgentArray[i]->PlayServerSocket, 2);
					close(gPrepAgentArray[i]->PlayServerSocket);
				}

				if (gPrepAgentArray[i]->PlaySocket > 0)
				{
					shutdown(gPrepAgentArray[i]->PlaySocket, 2);
					close(gPrepAgentArray[i]->PlaySocket);
				}

				while(gPrepAgentArray[i]->PlayHandle != NULL) {
					SLEEP(100);
				}
			}
			LogPrint(LOG_DEBUG, "PrepAgent_Close - play end!!\n");

			if (gPrepAgentArray[i]->strOverlayID != NULL && strlen_s(gPrepAgentArray[i]->strOverlayID))
			{
				free(gPrepAgentArray[i]->strOverlayID);
				gPrepAgentArray[i]->strOverlayID = NULL;
			}

			if (gPrepAgentArray[i]->strPAID != NULL && strlen_s(gPrepAgentArray[i]->strPAID))
			{
				free(gPrepAgentArray[i]->strPAID);
				gPrepAgentArray[i]->strPAID = NULL;
			}

			if (gSpeedHandle != NULL)
			{
				while (gSpeedHandle != NULL) {
					SLEEP(100);
				}
			}
			LogPrint(LOG_DEBUG, "PrepAgent_Close - speed end!!\n");

			delete gPrepAgentArray[i];
			gPrepAgentArray[i] = NULL;
		}
	}

	delete[] gPrepAgentArray;

	prepBuffer_freeBufferArray();
	PODOBuffer_freeBufferArray();

	HTTP_Cleanup();

	gnCurrentAgentCount = 0;

	LogPrint(LOG_DEBUG, "PrepAgent_Close - All end!!\n");
}
/*
OverlayItem_t ** PrepAgent_RetrieveOverlayInformation(char* strOverlayServerURL, char* strOverlayID, int* nCount, char* strMyPAID)
{
	char strServerIP[32] = { 0, }, strServerPath[128] = { 0, }, *urlTmp;
	//char *ch;
	unsigned int nServerPort;

	urlTmp = _strdup(strOverlayServerURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);

	return overlayAction_RetrieveOverlayNetwork(strOverlayID, strServerIP, nServerPort, strServerPath, nCount, strMyPAID);
}

OverlayItem_t ** PrepAgent_RetrievePODOOverlayInformation(char* strOverlayServerURL, char* strOverlayID, int* nCount, char* strMyPAID)
{
	char strServerIP[32] = { 0, }, strServerPath[128] = { 0, }, *urlTmp;
	//char *ch;
	unsigned int nServerPort;

	urlTmp = _strdup(strOverlayServerURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);

	return overlayAction_RetrievePODOOverlayNetwork(strOverlayID, strServerIP, nServerPort, strServerPath, nCount, strMyPAID);
}
*/
/*char* PrepAgent_CreateChannel(PrepAgentInfo_t prepAgent, char* strSubject, char *strOverlayID, int nCreateDash, char* imageBase64)
{
	int ret = 0;

	char *overlayNetworkID = NULL;

	char ip[24], path[124];

	//if (!HTTP_Startup()) return NULL;
	strGet_NIC_address(ip);
	//HTTP_Cleanup();

	prepAgent.strLocalIP = _strdup(ip);

	if (!_checkInitData(prepAgent))
		return NULL;

	_getServerInfoInURL(prepAgent.strChannelServerURL, ip, &prepAgent.nChannelServerPort, path);
	prepAgent.strChannelServerIP = _strdup(ip);
	prepAgent.strChannelServerPath = _strdup(path);

	_getServerInfoInURL(prepAgent.strOverlayServerURL, ip, &prepAgent.nOverlayServerPort, path);
	prepAgent.strOverlayServerIP = _strdup(ip);
	prepAgent.strOverlayServerPath = _strdup(path);

	overlayNetworkID = channelAction_CreateChannelInformation(prepAgent.strPAID, prepAgent.strChannelServerIP,
		prepAgent.nChannelServerPort, prepAgent.strChannelServerPath, strSubject, prepAgent.nPieceSize, prepAgent.strOverlayServerURL, strOverlayID, nCreateDash, imageBase64);

	if (overlayNetworkID == NULL || !strlen(overlayNetworkID))
		return NULL;

	ret = overlayAction_CreateOverlayNetwork(prepAgent.strPAID, prepAgent.strOverlayServerIP, prepAgent.nOverlayServerPort, prepAgent.strOverlayServerPath,
		overlayNetworkID, prepAgent.strLocalIP, prepAgent.nLocalPort, 10);

	if (ret != RESPONSE_CODE_OK)
	{
		channelAction_DeleteChannelInformation(prepAgent.strPAID, prepAgent.strChannelServerIP,
			prepAgent.nChannelServerPort, prepAgent.strChannelServerPath, overlayNetworkID);

		return NULL;
	}

	return overlayNetworkID;
}

int PrepAgent_PauseChannel(char* strOverlayID, int pause)
{
	int i = 0, rslt = 0;

	for (i = 0; i < gnMaxAgentCount; i++)
	{
		if (gPrepAgentArray[i] != NULL)
		{
			if (!strcmp(gPrepAgentArray[i]->strOverlayID, strOverlayID))
			{
				gPrepAgentArray[i]->nPause = pause;

				if (pause > 0)
				{
					if (PrepProgress != NULL) PrepProgress(PREP_EVENT_PAUSE, gPrepAgentArray[i]->strOverlayID, gPrepAgentArray[i]->strPAID, NULL, 0, 0);
				}
				else
				{
					if (PrepProgress != NULL) PrepProgress(PREP_EVENT_RESUME, gPrepAgentArray[i]->strOverlayID, gPrepAgentArray[i]->strPAID, NULL, 0, 0);
				}

				rslt = 1;
			}
		}
	}

	return rslt;
}

int PrepAgent_DeleteChannel(char* strPAID, char* strCsURL, char* strOsURL, char* strOverlayID)
{
	int ret = 0;

	char strServerIP[32], strServerPath[128], *urlTmp;
	//char *ch;
	unsigned int nServerPort;

	urlTmp = _strdup(strCsURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);

	ret = channelAction_DeleteChannelInformation(strPAID, strServerIP, nServerPort, strServerPath, strOverlayID);

	if (ret != RESPONSE_CODE_OK)
	{
		return FAIL;
	}

	urlTmp = _strdup(strOsURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);

	ret = overlayAction_DeleteOverlayNetwork(strPAID, strServerIP, nServerPort, strServerPath, strOverlayID, "", 0);

	if (ret != RESPONSE_CODE_OK)
	{
		return FAIL;
	}

	return SUCCESS;
}

void PrepAgent_FreeChannelItem(ChannelItem_t ** item, int cnt)
{
	int i=0;
	for (i=0; i<cnt; i++)
	{
		if (item[i]->strDescription != NULL && strlen(item[i]->strDescription))
			free(item[i]->strDescription);
		if (item[i]->strDescriptionImage != NULL && strlen(item[i]->strDescriptionImage))
			free(item[i]->strDescriptionImage);
		if (item[i]->strOverlayID != NULL && strlen(item[i]->strOverlayID))
			free(item[i]->strOverlayID);
		if (item[i]->strOverlayURL != NULL && strlen(item[i]->strOverlayURL))
			free(item[i]->strOverlayURL);
		if (item[i]->strProvider != NULL && strlen(item[i]->strProvider))
			free(item[i]->strProvider);
		if (item[i]->strPAID != NULL && strlen(item[i]->strPAID))
			free(item[i]->strPAID);
		if (item[i]->strSubject != NULL && strlen(item[i]->strSubject))
			free(item[i]->strSubject);

		free(item[i]);
	}

	free(item);
}*/

void PrepAgent_FreeOverlayItem(OverlayItem_t ** item, int cnt)
{
	int i=0;
	for (i=0; i<cnt; i++)
	{
		if (item[i]->strAction != NULL && strlen_s(item[i]->strAction))
			free(item[i]->strAction);
		if (item[i]->strAgentIP != NULL && strlen_s(item[i]->strAgentIP))
			free(item[i]->strAgentIP);
		if (item[i]->strOverlayID != NULL && strlen_s(item[i]->strOverlayID))
			free(item[i]->strOverlayID);
		if (item[i]->strAttribute != NULL && strlen_s(item[i]->strAttribute))
			free(item[i]->strAttribute);
		if (item[i]->strPAID != NULL && strlen_s(item[i]->strPAID))
			free(item[i]->strPAID);

		free(item[i]);
	}

	free(item);
}

int PrepAgent_JoinChannel(const char* strPAID, const char* strOverlayServerURL, const char* strOverlayID, unsigned int nAgentPort, unsigned int nRecordPort, unsigned int nCommunicatePort, unsigned int nPieceSize, int outfile, int pamInterval, std::string pamsURL, int peerType)
{
	//int cnt = 0, ret = 0;
	//OverlayItem_t ** item = NULL;

	//char ip[24];//, path[124];

	char strServerIP[32] = { 0, }, strServerPath[128] = { 0, }, *urlTmp;
	unsigned int nServerPort;

	ClientInfo_t *Info = NULL;
	ServerInfo_t *serverInfo = NULL;
	ServerInfo_t *communicateInfo = NULL;
	PrepAgent_t * agent = NULL;

	urlTmp = _strdup(strOverlayServerURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);

	agent = _newAgent(strOverlayID, strPAID, nPieceSize, nRecordPort, nAgentPort, nCommunicatePort, outfile);

	if (agent == NULL)
	{
		return FAIL;
	}

	Info = (ClientInfo_t *)malloc(sizeof(ClientInfo_t));
	if (Info != NULL)
	{
		memset(Info, 0, sizeof(ClientInfo_t));
		Info->strKey = _strdup(strOverlayID);
		Info->nServerPort = nServerPort;
		Info->strOverlayID = _strdup(strOverlayID);
		Info->strServerIP = _strdup(strServerIP);
		Info->strServerPath = _strdup(strServerPath);
	}

	serverInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	if (serverInfo != NULL)
	{
		memset(serverInfo, 0, sizeof(ServerInfo_t));
		serverInfo->strKey = _strdup(strOverlayID);
	}
	
	communicateInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	if (communicateInfo != NULL)
	{
		memset(communicateInfo, 0, sizeof(ServerInfo_t));
		communicateInfo->strKey = _strdup(strOverlayID);
	}	

	if (peerType == PAMP_TYPE_CS)
	{
		//agent->PlayHandle = PTHREAD_CREATE(VirtualPlayThread, Info);
	}
	else
	{
		//agent->PlayHandle = PTHREAD_CREATE(PlayThread, Info);
		agent->PlayHandle = PTHREAD_CREATE(VirtualPlayThread, Info);
	}

	agent->ServerHandle = PTHREAD_CREATE(ServerThread, serverInfo);
	agent->CommunicateHandle = PTHREAD_CREATE(CommunicateThread, communicateInfo);

	if (pamInterval > 0)
	{
		PAMInfo_t *PAMInfo = NULL;
		PAMInfo = (PAMInfo_t *)malloc(sizeof(PAMInfo_t));
		if (PAMInfo != NULL)
		{
			memset(PAMInfo, 0, sizeof(PAMInfo_t));
			PAMInfo->strKey = _strdup(strOverlayID);
			PAMInfo->strPAMSURL = _strdup(pamsURL.c_str());

			agent->PAMReoprtHandle = PTHREAD_CREATE(PAMReportThread, PAMInfo);
			agent->nPAMInterval = pamInterval;
		}
	}

	_clientManager_Startup(Info);/*Info->ClientHandle = */
	agent->ClientInfo = Info;

	if (gSpeedHandle == NULL)
	{
		gSpeedHandle = PTHREAD_CREATE(SpeedThread, NULL);
	}

	agent->nAgentType = peerType;

	return SUCCESS;
}

int PrepAgent_JoinPODOChannel(char* strPAID, char* strOverlayServerURL, char* strOverlayID, unsigned int nAgentPort, unsigned int nPieceSize, unsigned int nFileCount, FileInfo_t** fileInfos, int nTotalPieceCount, char* downDir, char* completeDir, int nVersion)
{
	//int cnt = 0, ret = 0;
	//OverlayItem_t ** item = NULL;

	//char ip[24];//, path[124];

	char strServerIP[32] = { 0, }, strServerPath[128] = { 0, }, *urlTmp;
	unsigned int nServerPort;

	ClientInfo_t *Info = NULL;
	ServerInfo_t *serverInfo = NULL;
	PrepAgent_t * agent = NULL;

	urlTmp = _strdup(strOverlayServerURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);

	agent = _newAgentPODO(strOverlayID, strPAID, nPieceSize, nAgentPort, nFileCount, fileInfos, nTotalPieceCount, downDir, completeDir, nVersion, 0);

	if (agent == NULL)
	{
		return FAIL;
	}

	Info = (ClientInfo_t *)malloc(sizeof(ClientInfo_t));
	if (Info != NULL)
	{
		memset(Info, 0, sizeof(ClientInfo_t));
		Info->strKey = _strdup(strOverlayID);
		Info->nServerPort = nServerPort;
		Info->strOverlayID = _strdup(strOverlayID);
		Info->strServerIP = _strdup(strServerIP);
		Info->strServerPath = _strdup(strServerPath);
	}	

	serverInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	if (serverInfo != NULL)
	{
		memset(serverInfo, 0, sizeof(ServerInfo_t));
		serverInfo->strKey = _strdup(strOverlayID);

		agent->ServerHandle = PTHREAD_CREATE(ServerThread, serverInfo);
	}

	//agent->PlayHandle = PTHREAD_CREATE(PlayThread, Info);

	_clientManager_Startup(Info);/*Info->ClientHandle = */
	agent->ClientInfo = Info;

	if (gSpeedHandle == NULL)
	{
		gSpeedHandle = PTHREAD_CREATE(SpeedThread, NULL);
	}

	return SUCCESS;
}

int PrepAgent_ViewChannel(char* strPAID, char* strOverlayServerURL, char* strOverlayID, unsigned int nAgentPort, unsigned int nRecordPort, unsigned int nPieceSize)
{
	//int cnt = 0, ret = 0;
	//OverlayItem_t ** item = NULL;

	//char ip[24];//, path[124];

	char strServerIP[32] = { 0, }, strServerPath[128] = { 0, }, *urlTmp;
	unsigned int nServerPort;

	ClientInfo_t *Info = NULL;
	ServerInfo_t *serverInfo = NULL;
	PrepAgent_t * agent = NULL;

	urlTmp = _strdup(strOverlayServerURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);
	
	agent = _newAgent(strOverlayID, strPAID, nPieceSize, nRecordPort, nAgentPort, 0, 0);

	if (agent == NULL)
	{
		return FAIL;
	}

	Info = (ClientInfo_t *)malloc(sizeof(ClientInfo_t));
	if (Info != NULL)
	{
		memset(Info, 0, sizeof(ClientInfo_t));
		Info->strKey = _strdup(strOverlayID);
		Info->nServerPort = nServerPort;
		Info->strOverlayID = _strdup(strOverlayID);
		Info->strServerIP = _strdup(strServerIP);
		Info->strServerPath = _strdup(strServerPath);

		agent->PlayHandle = PTHREAD_CREATE(PlayThread, Info);

		agent->ClientInfo = Info;
	}
	
	serverInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	if (serverInfo != NULL)
	{
		memset(serverInfo, 0, sizeof(ServerInfo_t));
		serverInfo->strKey = _strdup(strOverlayID);
		agent->ServerHandle = PTHREAD_CREATE(ServerThread, serverInfo);
	}	

	_clientManager_Startup(Info);/*Info->ClientHandle = */	

	return SUCCESS;
}

int PrepAgent_LeaveChannel(const char* strPAID, const char* strOverlayServerURL, const char* strOverlayID)
{
	//int cnt = 0, ret = 0;

	char strServerIP[32] = { 0, }, strServerPath[128] = { 0, }, *urlTmp;
	unsigned int nServerPort;

	urlTmp = _strdup(strOverlayServerURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);

	/*ret = overlayAction_DeleteOverlayNetwork(strPAID, strServerIP, nServerPort, strServerPath, strOverlayID, "", 0);
	if (ret != RESPONSE_CODE_OK)
	{
		return FAIL;
	}*/

	PrepAgent_StopPrepAgent(strOverlayID, 0);

	return SUCCESS;
}

int PrepAgent_RunPrepAgent(const char* strPAID, unsigned int nRecordPort, unsigned int nPeerPort, unsigned int nCommunicatePort, const char* strOverlayID, unsigned int nPieceSize, int pamInterval, std::string pamsURL, int peerType, const char* overlayURL)
{

	ServerInfo_t *recordInfo = NULL, *peerInfo = NULL, *communicateInfo = NULL;

	PrepAgent_t * agent = NULL;

	agent = _newAgent(strOverlayID, strPAID, nPieceSize, nRecordPort, nPeerPort, nCommunicatePort, 0);

	if (agent == NULL)
	{
		return FAIL;
	}

	/*if (!HTTP_Startup())
	{
	return FAIL;
	}*/

	recordInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	if (recordInfo != NULL)
	{
		memset(recordInfo, 0, sizeof(ServerInfo_t));
		recordInfo->strKey = _strdup(strOverlayID);
		agent->recordHandle = PTHREAD_CREATE(RecordThread, recordInfo);
	}	

	peerInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	if (peerInfo != NULL)
	{
		memset(peerInfo, 0, sizeof(ServerInfo_t));
		peerInfo->strKey = _strdup(strOverlayID);

		agent->ServerHandle = PTHREAD_CREATE(ServerThread, peerInfo);
	}	

	communicateInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	if (communicateInfo != NULL)
	{
		memset(communicateInfo, 0, sizeof(ServerInfo_t));
		communicateInfo->strKey = _strdup(strOverlayID);

		agent->CommunicateHandle = PTHREAD_CREATE(CommunicateThread, communicateInfo);
	}	

	if (gSpeedHandle == NULL)
	{
		gSpeedHandle = PTHREAD_CREATE(SpeedThread, NULL);
	}

	if (pamInterval > 0)
	{
		PAMInfo_t *PAMInfo = NULL;
		PAMInfo = (PAMInfo_t *)malloc(sizeof(PAMInfo_t));
		if (PAMInfo != NULL)
		{
			memset(PAMInfo, 0, sizeof(PAMInfo_t));
			PAMInfo->strKey = _strdup(strOverlayID);
			PAMInfo->strPAMSURL = _strdup(pamsURL.c_str());

			agent->PAMReoprtHandle = PTHREAD_CREATE(PAMReportThread, PAMInfo);
			agent->nPAMInterval = pamInterval;
		}
	}

	agent->nAgentType = peerType;

	char strServerIP[32] = { 0, }, strServerPath[128] = { 0, }, *urlTmp;
	unsigned int nServerPort;

	urlTmp = _strdup(overlayURL);

	_getServerInfoInURL(urlTmp, strServerIP, &nServerPort, strServerPath);

	free(urlTmp);

	if (agent->nAgentType == PAMP_TYPE_CS)
	{
		PrepBuffer_getBufferByKey(agent->strOverlayID)->SP = 0;
	}
	else if (agent->nAgentType == PAMP_TYPE_SEEDER)
	{
		PrepBuffer_getBufferByKey(agent->strOverlayID)->SP = 0;

		ClientInfo_t *Info = (ClientInfo_t *)malloc(sizeof(ClientInfo_t));
		if (Info != NULL)
		{
			memset(Info, 0, sizeof(ClientInfo_t));
			Info->strKey = _strdup(strOverlayID);
			Info->nServerPort = nServerPort;
			Info->strOverlayID = _strdup(strOverlayID);
			Info->strServerIP = _strdup(strServerIP);
			Info->strServerPath = _strdup(strServerPath);

			_clientManager_Startup(Info);/*Info->ClientHandle = */
			agent->ClientInfo = Info;
		}
	}

	return SUCCESS;
}

int PrepAgent_RunPODOAgent(char* strPAID, unsigned int nPeerPort, char* strOverlayID, unsigned int nPieceSize, unsigned int nFileCount, FileInfo_t** fileInfos, int totalPieceCount, char* downDir, char* completeDir, unsigned int nVersion, unsigned int nIsServer)
{
	ServerInfo_t /**recordInfo = NULL,*/ *peerInfo = NULL;

	PrepAgent_t * agent = NULL;

	agent = _newAgentPODO(strOverlayID, strPAID, nPieceSize, nPeerPort, nFileCount, fileInfos, totalPieceCount, downDir, completeDir, nVersion, nIsServer);

	if (agent == NULL)
	{
		return FAIL;
	}

	/*if (!HTTP_Startup())
	{
	return FAIL;
	}*/

	/*recordInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	memset(recordInfo, 0, sizeof(ServerInfo_t));
	recordInfo->strKey = _strdup(strOverlayID);

	agent->recordHandle = PTHREAD_CREATE(RecordThread, recordInfo);*/

	peerInfo = (ServerInfo_t *)malloc(sizeof(ServerInfo_t));
	if (peerInfo != NULL)
	{
		memset(peerInfo, 0, sizeof(ServerInfo_t));
		peerInfo->strKey = _strdup(strOverlayID);

		agent->ServerHandle = PTHREAD_CREATE(ServerThread, peerInfo);
	}	

	if (gSpeedHandle == NULL)
	{
		gSpeedHandle = PTHREAD_CREATE(SpeedThread, NULL);
	}

	return SUCCESS;
}

int PrepAgent_UpdatePODOAgent(char* strOverlayID, unsigned int nFileCount, FileInfo_t** fileInfos, int totalPieceCount, unsigned int nVersion)
{
	PrepAgent_t * agent = NULL;

	agent = _getAgentByKey(strOverlayID);

	if (agent == NULL)
	{
		return FAIL;
	}

	if (!PODOBuffer_updateBuffer(strOverlayID, nFileCount, fileInfos, totalPieceCount, nVersion))
	{
		return FAIL;
	}

	return SUCCESS;
}

void PrepAgent_StopPrepAgent(const char* strOverlayID, int removeData)
{
	unsigned int i=0;
	//unsigned int j = 0;

	LogPrint(LOG_DEBUG, "PrepAgent_StopPrepAgent start!!\n");

	for(i=0; i<gnMaxAgentCount; i++)
	{
		if (gPrepAgentArray[i] != NULL)
		{
			if (!strcmp(gPrepAgentArray[i]->strOverlayID, strOverlayID))
			{
				gPrepAgentArray[i]->nClose = 1;

				if (gPrepAgentArray[i]->recordHandle != NULL)
				{
					shutdown(gPrepAgentArray[i]->recordSocket, 2);
					close(gPrepAgentArray[i]->recordSocket);
					while(gPrepAgentArray[i]->recordHandle != NULL) {
						SLEEP(100);
					}
				}
				LogPrint(LOG_DEBUG, "PrepAgent_StopPrepAgent - record end!!\n");

				if (gPrepAgentArray[i]->ServerHandle != NULL)
				{
					shutdown(gPrepAgentArray[i]->ServerSocket, 2);
					close(gPrepAgentArray[i]->ServerSocket);
					while(gPrepAgentArray[i]->ServerHandle != NULL) {
						SLEEP(100);
					}
				}
				LogPrint(LOG_DEBUG, "PrepAgent_StopPrepAgent - server end!!\n");

				if (gPrepAgentArray[i]->CommunicateHandle != NULL)
				{
					shutdown(gPrepAgentArray[i]->CommunicateSocket, 2);
					close(gPrepAgentArray[i]->CommunicateSocket);
					while (gPrepAgentArray[i]->CommunicateHandle != NULL) {
						SLEEP(100);
					}
				}

				if (gPrepAgentArray[i]->PAMReoprtHandle != NULL)
				{
					while (gPrepAgentArray[i]->PAMReoprtHandle != NULL)
					{
						SLEEP(100);
					}
				}

				if (gPrepAgentArray[i]->ClientInfo != NULL)
				{
					while(gPrepAgentArray[i]->ClientInfo != NULL) {
						SLEEP(100);

						if (gPrepAgentArray[i]->ClientInfo != NULL)
						{
							pthread_cond_signal(&gPrepAgentArray[i]->ClientInfo->ClientCond);
						}
					}
				}
				LogPrint(LOG_DEBUG, "PrepAgent_StopPrepAgent - client end!!\n");

				while (!gPrepAgentArray[i]->totalPeerMap.empty())
				{
					SLEEP(100);
				}
				
				LogPrint(LOG_DEBUG, "PrepAgent_StopPrepAgent - peer end!!\n");

				if (gPrepAgentArray[i]->PlayHandle != NULL)
				{
					if (gPrepAgentArray[i]->PlayServerSocket > 0)
					{
						shutdown(gPrepAgentArray[i]->PlayServerSocket, 2);
						close(gPrepAgentArray[i]->PlayServerSocket);
					}

					if (gPrepAgentArray[i]->PlaySocket > 0)
					{
						shutdown(gPrepAgentArray[i]->PlaySocket, 2);
						close(gPrepAgentArray[i]->PlaySocket);
					}
					
					while(gPrepAgentArray[i]->PlayHandle != NULL) {
						SLEEP(100);
					}
				}
				LogPrint(LOG_DEBUG, "PrepAgent_StopPrepAgent - play end!!\n");

				while (1)
				{
					gPrepAgentArray[i]->sendPartnerMutex.lock();
					int size = gPrepAgentArray[i]->sendPartnerMap.size();
					
					if (size <= 0)
					{
						gPrepAgentArray[i]->sendPartnerMutex.unlock();
						break;
					}

					PartnerData_t *partner = gPrepAgentArray[i]->sendPartnerMap.begin()->second;
					gPrepAgentArray[i]->sendPartnerMutex.unlock();

					shutdown(partner->socket, 2);
					close(partner->socket);
					while (size <= gPrepAgentArray[i]->sendPartnerMap.size())
					{
						SLEEP(100);
					}
				}

				while (1)
				{
					gPrepAgentArray[i]->recvPartnerMutex.lock();
					int size = gPrepAgentArray[i]->recvPartnerMap.size();

					if (size <= 0)
					{
						gPrepAgentArray[i]->recvPartnerMutex.unlock();
						break;
					}
					PartnerData_t *partner = gPrepAgentArray[i]->recvPartnerMap.begin()->second;
					gPrepAgentArray[i]->recvPartnerMutex.unlock();

					shutdown(partner->socket, 2);
					close(partner->socket);
					while (size <= gPrepAgentArray[i]->recvPartnerMap.size())
					{
						SLEEP(100);
					}
				}

				LogPrint(LOG_DEBUG, "PrepAgent_StopPrepAgent - partner end!!\n");

				prepBuffer_freeBufferByKey(gPrepAgentArray[i]->strOverlayID);
				PODOBuffer_freeBufferByKey(gPrepAgentArray[i]->strOverlayID, removeData);

				if (gPrepAgentArray[i]->strOverlayID != NULL && strlen_s(gPrepAgentArray[i]->strOverlayID))
				{
					free(gPrepAgentArray[i]->strOverlayID);
					gPrepAgentArray[i]->strOverlayID = NULL;
				}

				if (gPrepAgentArray[i]->strPAID != NULL && strlen_s(gPrepAgentArray[i]->strPAID))
				{
					free(gPrepAgentArray[i]->strPAID);
					gPrepAgentArray[i]->strPAID = NULL;
				}

				//free(gPrepAgentArray[i]);
				delete gPrepAgentArray[i];
				gPrepAgentArray[i] = NULL;

				gnCurrentAgentCount--;
			}
		}
	}

	LogPrint(LOG_DEBUG, "PrepAgent_StopPrepAgent - All end!!\n");
}

/*
double PrepAgent_GetSpeed(char* strOverlayID)
{
	int i = 0;
	double speed = 0;

	for(i=0; i<gnMaxAgentCount; i++)
	{
		if (gPrepAgentArray[i] != NULL)
		{
			if (!strcmp(gPrepAgentArray[i]->strOverlayID, strOverlayID))
			{
				gPrepAgentArray[i]->nSpeedCheck = 1;

				speed = gPrepAgentArray[i]->dSpeed;

				gPrepAgentArray[i]->dSpeed = 0;

				break;
			}
		}
	}

	return speed;
}

void PrepAgent_SetSpeedCheck(int chk)
{
	int i = 0;
	//double speed = 0;

	for(i=0; i<gnMaxAgentCount; i++)
	{
		if (gPrepAgentArray[i] != NULL)
		{
			gPrepAgentArray[i]->dSpeed = chk;
		}
	}
}*/

/*
1 = Started
2 = Checking
4 = Start after check
8 = Checked
16 = Error
32 = Paused
64 = Queued
128 = Loaded
For example, if a torrent job has a status of 201 = 128 + 64 + 8 + 1, then it is loaded, queued, checked, and started. A bitwise AND operator should be used to determine whether the given STATUS contains a particular status.
*/
FileInfo_t** PrepAgent_GetFileInfos(char* overlayID, int* cnt)
{
	PrepAgent_t * agent = _getAgentByKey(overlayID);

	*cnt = 0;

	if (agent != NULL)
	{
		if (agent->nIsPODO)
		{
			return PODOBuffer_GetFileInfos(overlayID, cnt);
		}
	}

	return NULL;
}

Property_t* PrepAgent_GetProperty(char* overlayID)
{
	int len = 0;
	char tmp[10] = { '\0' };
	Property_t *property = NULL;
	PrepAgent_t * agent = _getAgentByKey(overlayID);

	if (agent != NULL)
	{
		property = (Property_t*)malloc(sizeof(Property_t));
		if (property != NULL)
		{
			memset(property, 0, sizeof(Property_t));

			property->strOverlayID = _strdup(overlayID);
		}
		
		if (agent->ClientInfo != NULL)
		{
			len += strlen_s(agent->ClientInfo->strServerIP) + 1;
			//_itoa(agent->ClientInfo->nServerPort, tmp, 10);
			
			sprintf_s(tmp, "%d", agent->ClientInfo->nServerPort);

			len += strlen_s(tmp) + 1;
			len += strlen_s(agent->ClientInfo->strServerPath) + 1;

			property->strTracker = (char *)malloc(sizeof(char) * len);

			if (property->strTracker != NULL)
			{
				memset(property->strTracker, 0, sizeof(char) * len);

				sprintf_s(property->strTracker, len, "%s%s%s%s%s", agent->ClientInfo->strServerIP, ":", tmp, "/", agent->ClientInfo->strServerPath);
			}
		}
		else
		{
			property->strTracker = _strdup(" ");
		}

		property->nMaxSendPeerCount = agent->nMaxPeerCount;
		property->dUploadLimit = agent->dUploadBpsLimit;
		property->dDownloadLimit = agent->dDownloadBpsLimit;
	}

	return property;
}

Progress_t* PrepAgent_GetStatus(char* overlayID)
{
	int status = 0;
	Progress_t* progress = NULL;
	PrepAgent_t * agent = _getAgentByKey(overlayID);

	if (agent != NULL)
	{
		progress = (Progress_t*)malloc(sizeof(Progress_t));
		if (progress != NULL)
		{
			memset(progress, 0, sizeof(Progress_t));
		}		

		status += 1;
		status += 8;
		status += 64;

		if (agent->nPause > 0)
		{
			status += 32;
		}
		
		if (agent->nIsPODO > 0)
		{
			if (PODOBuffer_isPODOComplete(overlayID, 1) > 0)
			{
				status += 128;
			}
		}

		progress->nStatus = status;

		progress->nPeerCountInOverlayNetwork = agent->nPeerCountInOverlayNetwork;
		progress->nRecvPeerCount = agent->nCurRecvPeerCount;
		progress->nSendPeerCount = agent->nCurSendPeerCount;
		progress->dDownloadBytes = agent->dTotalDownloadBytes;
		progress->dUploadBytes = agent->dTotalUploadBytes;
		progress->dDownloadBps = agent->dDownloadBps;
		progress->dUploadBps = agent->dUploadBps;
		
		if (agent->nIsPODO)
		{
			PODOBuffer_t * buf = PODOBuffer_getPODOBufferByKey(overlayID);

			if (buf != NULL)
			{
				progress->dTotalBytes = buf->dTotalBytes;
				progress->lAddedTime = buf->lAddedTime;
				progress->lCompleteTime = buf->lCompleteTime;
			}
		}
		else
		{
			PrepBuffer_t * buf = PrepBuffer_getBufferByKey(overlayID);

			if (buf != NULL)
			{
				progress->lAddedTime = buf->lAddedTime;
				progress->lCompleteTime = buf->lCompleteTime;
			}
		}
	}

	return progress;
}

int PrepAgent_SetOverlayBandwidth(char* overlayID, double up, double down)
{
	int rslt = 0;
	PrepAgent_t * agent = _getAgentByKey(overlayID);

	if (agent != NULL)
	{
		if (up >= 0)
		{
			agent->dUploadBpsLimit = up;
		}

		if (down >= 0)
		{
			agent->dDownloadBpsLimit = down;
		}

		rslt = 1;
	}

	return rslt;
}

int PrepAgent_SetOverlayMaxPeerCount(char* overlayID, unsigned int count)
{
	int rslt = 0;
	PrepAgent_t * agent = _getAgentByKey(overlayID);

	if (agent != NULL)
	{
		if (agent->nMaxPeerCount != count)
		{
			agent->nPause = 1;

			while (!agent->totalPeerMap.empty())
			{
				SLEEP(100);
			}

			agent->nMaxPeerCount = count;

			agent->nPause = 0;
		}

		rslt = 1;
	}

	return rslt;
}

void PrepAgent_SetPlaySync(int dfrag, int dtime, int playsync)
{
	if (dfrag >= 0)
		gnDfrag = dfrag;

	gnDtime = dtime;
	gnPlaySync = playsync;
}

void *RecordThread(void *pInfo)
{
	int ret;
	char buf[65500] = { 0, };
	int timeout = 5; // 5초
	int lastDP = -1;

	struct sockaddr_in serveraddr;

	PrepAgent_t * agent = NULL;

	ServerInfo_t *Info = (ServerInfo_t *)pInfo;

	agent = _getAgentByKey(Info->strKey);

	pthread_cleanup_push(_cleanupRecordThread, Info);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL); 
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	Info->socket = socket(AF_INET, SOCK_DGRAM, 0);
	if (Info->socket < 0)
	{
		perror("socket error : ");
		pthread_exit(NULL);
	}

	agent->recordSocket = Info->socket;

	memset(&serveraddr, 0, sizeof(serveraddr));
	serveraddr.sin_family = AF_INET;
	serveraddr.sin_addr.s_addr = htonl(INADDR_ANY);
	serveraddr.sin_port = htons(agent->nRecordPort);

	ret = bind(Info->socket, (struct sockaddr *)&serveraddr, sizeof(serveraddr));
	
	if (ret == SOCKET_ERROR)
	{
		perror("bind error !!!: ");
		pthread_exit(NULL);
	}

	// time out 처리 하지 않고 계속 대기하려 했으나 recvfrom 에서 대기할 경우 pthread_cancel 호출해도 thread가 죽지 않는
	// 현상이 있어 time out 은 그대로 두고 대신 time out 이 걸려도 아무 작업 없이 다시 대기하도록 한다.
#ifdef WIN32
	if(setsockopt(Info->socket, SOL_SOCKET, SO_RCVTIMEO, (char*)&timeout, sizeof(timeout)) == SOCKET_ERROR)
#else
	struct timeval tv;
	tv.tv_sec = timeout;
	tv.tv_usec = 0;
	if (setsockopt(Info->socket, SOL_SOCKET, SO_RCVTIMEO, (char*)&tv, sizeof(struct timeval)) == SOCKET_ERROR)
#endif
	{
		LogPrint(LOG_CRITICAL, "setsockopt() error");
		pthread_exit(NULL);
	}

	while(1)
	{
		if(agent->nClose == 1) {
			break;
		}

		ret = recvfrom(Info->socket, buf, sizeof(buf), 0, NULL, NULL);

		if (ret > 0)
		{
			int tmpDP = 0;

			if(agent->nClose == 1) {
				break;
			}

			/////////////////////////////////////////////////////////////////////////////
			/*FILE *fp = fopen("1231231.mp4", "ab");

			if (fp == NULL)
			{
				LogPrint(LOG_CRITICAL, "111111Outfile open error!!\n");
			}

			int fr = fwrite(buf, 1, ret, fp);

			if (fr < 0)
			{
				LogPrint(LOG_CRITICAL, "111111Outfile write error\n");
			}

			fclose(fp);*/
			/////////////////////////////////////////////////////////////////////////

			prepBuffer_setRecordData(Info->strKey, buf, ret);
			
			tmpDP = prepBuffer_getCurrentDP(Info->strKey);
			if (lastDP != tmpDP)
			{
				LogPrint(LOG_DEBUG, "prepBuffer_getCurrentDP - %d\n", tmpDP);
				lastDP = tmpDP;

				if (lastDP > 0)
				{
					char* pieceData = (char *)calloc(1, agent->nPieceSize);

					if (prepBuffer_getPieceData(Info->strKey, lastDP - 1, pieceData) == SUCCESS) {
						char filename[20] = { 0, };
						sprintf(filename, "%d.piece", lastDP - 1);

						FILE *fp = fopen(filename, "w");

						if (fp == NULL)
						{
							LogPrint(LOG_CRITICAL, "111111Outfile open error!!\n");
						}
						else
						{
							int fr = fwrite(pieceData, 1, agent->nPieceSize, fp);

							if (fr < 0)
							{
								LogPrint(LOG_CRITICAL, "111111Outfile write error\n");
							}

							fclose(fp);
						}
					}

					free(pieceData);
				}

				//for (i=0; i<agent->nMaxPartnerCount; i++)
				{
					if(agent->nClose == 1) {
						break;
					}

					agent->recvPartnerMutex.lock();

					if (agent->recvPartnerMap.size() > 0)
					{
						for (PartnerMapIter it = agent->recvPartnerMap.begin(); it != agent->recvPartnerMap.end(); ++it)
						{
							NotifyData_t *data = it->second->notifyData;

							if (data == NULL)
							{
								data = (NotifyData_t *)malloc(sizeof(NotifyData_t));
								if (data != NULL)
								{
									memset(data, 0, sizeof(NotifyData_t));
								}

								it->second->notifyData = data;
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
								}
								next->next = data;
							}

							data->piece_index = lastDP - 1;
						}
					}
					agent->recvPartnerMutex.unlock();
				}
			}
		}
		else
		{
			//LogPrint(LOG_DEBUG, "record recv < 0\n");
			//LogPrint(LOG_DEBUG, "time out!!\n");
			//pthread_exit(NULL);  time out이 발생해도 thread를 죽이지 않고 다시 대기한다.
		}
		//add_data.sum = add_data.a + add_data.b;
		//sendto(sockfd, (char *)&add_data, sizeof(add_data), 0, (struct sockaddr *)&clientaddr, clilen);
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);

	if (Info != NULL)
	{
		close(Info->socket);
	}

	return NULL;
}

int isEqualsOverlayItem(PrepAgent_t * agent, OverlayItem_t * overlayItem) 
{
	if (agent->nAgentType == PAMP_TYPE_SEEDER)
	{
		agent->recvPartnerMutex.lock();
		for (PartnerMapIter it = agent->recvPartnerMap.begin(); it != agent->recvPartnerMap.end(); ++it)
		{
			if (!strcmp(it->second->peerData->pa_id, overlayItem->strPAID))
			{
				agent->recvPartnerMutex.unlock();
				return TRUE;
			}
		}
		agent->recvPartnerMutex.unlock();
	}
	else
	{
		agent->sendPartnerMutex.lock();
		for (PartnerMapIter it = agent->sendPartnerMap.begin(); it != agent->sendPartnerMap.end(); ++it)
		{
			if (!strcmp(it->second->peerData->pa_id, overlayItem->strPAID))
			{
				agent->sendPartnerMutex.unlock();
				return TRUE;
			}
		}
		agent->sendPartnerMutex.unlock();
	}

	agent->totalPeerMutex.lock();
	for (PeerMapIter it = agent->totalPeerMap.begin(); it != agent->totalPeerMap.end(); ++it)
	{
		if (it->second->prepMode == PREP_CLIENT_MODE || agent->nAgentType == PAMP_TYPE_SEEDER)
		{
			if (!strcmp(it->second->pa_id, overlayItem->strPAID))
			{
				agent->totalPeerMutex.unlock();
				return TRUE;
			}
		}
	}
	agent->totalPeerMutex.unlock();

	return FALSE;
}

void *SendFilePiece(int sockfd, int udp)
{
	unsigned long sent_len;
	//char ch;
	int ret;
	unsigned long fragment_index = 0;
	unsigned int fragment_size = 128*1024;
	FILE *fp;
	//char *rslt;

	struct sockaddr_in player_addr;
	player_addr.sin_family = AF_INET;
	player_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
	player_addr.sin_port =  htons(1001);

	fp=fopen((char *)"C:\\Users\\Jay\\Desktop\\123.mp4", "rb");
	if(fp==NULL) 
	{
		LogPrint(LOG_CRITICAL, "file open failure\n");
		return NULL;
	}

	fseek(fp, (fragment_index * fragment_size), SEEK_SET);

	sent_len=0;
	while(!feof(fp))
	{
		int size;
		char tmpCh[1392] = { 0, };
		//char sendch[1392];

		size=fread(tmpCh, 1, 1392, fp);
		//memcpy(sendch, tmpCh, size);
		//rslt = (char*)malloc(sizeof(char) * size);
		//memcpy(rslt, tmpCh, size);

		if(udp == 1) 
		{
			ret=sendto(sockfd, tmpCh, size,0,(struct sockaddr*)&player_addr, sizeof(player_addr));
			SLEEP(5);
		} 
		else 
		{
			ret=send(sockfd, tmpCh, size, 0);
		}

		//free(rslt);

		if(ret<=0)
		{
			break;
		}

		if(udp == 1) 
		{
			if ((sent_len % 1392) == 0) SLEEP(5);
		}

		sent_len+=size;

		LogPrint(LOG_DEBUG, "%d byte has been sent\n", sent_len);
	}

	LogPrint(LOG_DEBUG, "%d byte has been sent\n", sent_len);

	fclose(fp);	

	return NULL;
}

void *SpeedThread(void *pInfo)
{
	int i = 0, cnt = 0;
		
	LogPrint(LOG_DEBUG, "Start speed thread.\n");

	pthread_cleanup_push(_cleanupSpeedThread, NULL);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	while (1) {
		SLEEP(1000);

		if (gStopPrepAgent)
		{
			break;
		}

		cnt = 0;
		
		gSecDownloadBytes = 0;
		gSecUploadBytes = 0;

		gDownloadBps = 0;
		gUploadBps = 0;

		for (i = 0; i < gnMaxAgentCount; i++)
		{
			if (gPrepAgentArray[i] != NULL && !gPrepAgentArray[i]->nClose)
			{
				cnt++;
				gPrepAgentArray[i]->dDownloadBps = gPrepAgentArray[i]->dSecDownloadBytes;
				gPrepAgentArray[i]->dSecDownloadBytes = 0;
				gSecDownloadBytes += gPrepAgentArray[i]->dDownloadBps;
				gDownloadBytes += gPrepAgentArray[i]->dDownloadBps;

				gPrepAgentArray[i]->dUploadBps = gPrepAgentArray[i]->dSecUploadBytes;
				gPrepAgentArray[i]->dSecUploadBytes = 0;
				gSecUploadBytes += gPrepAgentArray[i]->dUploadBps;
				gUploadBytes += gPrepAgentArray[i]->dUploadBps;
			}
		}

		gDownloadBps = gSecDownloadBytes;
		gUploadBps = gSecDownloadBytes;

		if (cnt <= 0) break;
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);

	return NULL;
}


void *PlayThread(void *pInfo)
{
	int udp = 0;
	int file = 0;
	//int nBufferCheck = 1;
	struct sockaddr_in server_addr, player_addr;
	SOCKET serverfd = -1;
	int size;
	PrepAgent_t *agent;
	ClientInfo_t *Info = (ClientInfo_t *)pInfo;
	ClientInfo_t * playInfo = (ClientInfo_t *)malloc(sizeof(ClientInfo_t));

	LogPrint(LOG_DEBUG, "Server: Start play thread.\n");

	if (playInfo == NULL)
	{
		perror("playthread error");
		return 0;
	}

	memset(playInfo, 0, sizeof(ClientInfo_t));
	playInfo->strKey = _strdup(Info->strKey);

	agent = _getAgentByKey(playInfo->strKey);

	pthread_cleanup_push(_cleanupPlayThread, playInfo);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL); 
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	while(1) {
		if(agent->nClose == 1) {
			break;
		}

		//UDP
		if(udp == 1) 
		{
			playInfo->socket = socket(AF_INET, SOCK_DGRAM, 0);
			player_addr.sin_family = AF_INET;
			player_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
			player_addr.sin_port =  htons(agent->nRecordPort);
		}
		else
		{
			//TCP
			// 		serverfd = socket(PF_INET, SOCK_STREAM, 0);
			// 		memset((char *)&server_addr, 0, sizeof(server_addr));  
			// 		server_addr.sin_family = PF_INET;
			// 		server_addr.sin_addr.s_addr = htons(INADDR_ANY);//inet_addr("127.0.0.1");
			// 		server_addr.sin_port =  htons(agent->nRecordPort);
			// 		bind(serverfd,(struct sockaddr *)&server_addr,sizeof(server_addr));
			// 		listen(serverfd, 1);
			// 		size = sizeof(player_addr);
			// 		playInfo->socket = accept(serverfd, (struct sockaddr *)&player_addr, &size);

			int	nfds;			/* 최대 소켓번호 +1 */
			fd_set read_fds;	/* 읽기를 감지할 소켓번호 구조체 */
			struct timeval timeout;
			timeout.tv_sec = 10;
			timeout.tv_usec = 0;

			/* 초기소켓 생성 */
			if((serverfd = socket(PF_INET, SOCK_STREAM, 0)) < 0)  {
				LogPrint(LOG_CRITICAL, "Server: Can't open stream socket.");
				pthread_exit(NULL);
			}

			agent->PlayServerSocket = serverfd;

			/* server_addr 구조체의 내용 세팅 */
			memset((char *)&server_addr, 0, sizeof(server_addr));  
			server_addr.sin_family = AF_INET;              
			server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
			//server_addr.sin_port = htons(atoi(argv[1]));     
			server_addr.sin_port = htons(agent->nRecordPort);

			LogPrint(LOG_DEBUG, "Server: play with tcp %d\n", agent->nRecordPort);

			if (bind(serverfd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
				LogPrint(LOG_CRITICAL, "Server: Can't bind local address.\n");
				pthread_exit(NULL);
			}

			/* 클라이언트로부터 연결요청을 기다림 */
			listen(serverfd, 5);
			LogPrint(LOG_DEBUG, "listen!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");

			nfds = serverfd + 1;		/* 최대 소켓번호 +1 */
			FD_ZERO(&read_fds);

			while(1) {
				if(agent->nClose == 1) {
					break;
				}

				/* 읽기 변화를 감지할 소켓번호를 fd_set 구조체에 지정 */
				FD_SET(serverfd, &read_fds);

				/*--------------------------------------- select() 호출 ----------------------------------------- */
				if (select(nfds, &read_fds, (fd_set *)0, (fd_set *)0,(struct timeval *)0) < 0) {
					LogPrint(LOG_CRITICAL, "select error\n");
					pthread_exit(NULL);
				}

				/*------------------------------ 클라이언트 연결요청 처리 ------------------------------- */
				if(FD_ISSET(serverfd, &read_fds)) {
					//int ttt = 1000;
					size = sizeof(player_addr);
					
#ifdef WIN32
					playInfo->socket = accept(serverfd, (struct sockaddr *)&player_addr, &size);
#else
					playInfo->socket = accept(serverfd, (struct sockaddr *)&player_addr, (socklen_t *)&size);
#endif
					LogPrint(LOG_DEBUG, "accept!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
					//setsockopt(playInfo->socket, SOL_SOCKET, SO_RCVTIMEO, (char*)&ttt, sizeof(ttt));

					close(serverfd);
					shutdown(serverfd, 0);

					break;
				}
			}
		}

		agent->PlaySocket = playInfo->socket;

		{
			// LINGER 구조체의 값 설정  
			struct linger  ling = {0,};  
			ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
			ling.l_linger = 0;  // LINGER Timeout 설정  

			// LINGER 옵션을 Socket에 적용  
			setsockopt(playInfo->socket, SOL_SOCKET, SO_LINGER, (char*)&ling, sizeof(ling));
		}

		int dtime = gnDtime;
		int dfrag = gnDfrag;
		//int playSyncTime = gnPlaySync > 0 ? dtime : 0;


		if(file == 1) 
		{
			SendFilePiece(playInfo->socket, udp);
		}
		else
		{
			unsigned int skipCount = 0;

			while(1) 
			{
				char * pieceData = NULL;

				if (dfrag > 0)
				{
					LogPrint(LOG_WARNING, "CONF_DFRAG!! %d\n", dfrag);
					while (dfrag > 0)
					{
						if (agent->nClose == 1) {
							break;
						}

						int frag = prepBuffer_getCurrentDP(playInfo->strKey) - prepBuffer_getCurrentSP(playInfo->strKey);

						LogPrint(LOG_WARNING, "Current frag!! %d\n", frag);

						if (frag >= dfrag)
						{
							LogPrint(LOG_WARNING, "frag OK!!\n");
							dfrag = 0;
						}
						else
						{
							LogPrint(LOG_WARNING, "frag SLEEP 1000!!\n");
							SLEEP(1000);
						}
					}
				}
				/*
				if (playSyncTime > 0)
				{
					LogPrint(LOG_WARNING, "CONF_PLAYSYNC!! %d\n", playSyncTime);
					double sync = GetNTPTimestamp();
					LogPrint(LOG_WARNING, "Cur time !! %.0lf\n", sync);
					sync -= (playSyncTime / 1000 / 2);
					LogPrint(LOG_WARNING, "Cur time2 !! %.0lf\n", sync);

					int tmppp = -1;

					int lastIndex = 0;

					do 
					{
						if (agent->nClose == 1) {
							break;
						}

						tmppp = prepBuffer_getPieceIndex4Timestamp(playInfo->strKey, sync, lastIndex);

						if (tmppp < 0)
						{
							prepBuffer_setCurrentPP(playInfo->strKey, prepBuffer_getCurrentDP(playInfo->strKey) - 1);
							SLEEP(1000);
						}
					} while (tmppp < 0);

					playSyncTime = 0;
					prepBuffer_setCurrentPP(playInfo->strKey, tmppp);
				}

				if (dtime > 0)
				{
					LogPrint(LOG_WARNING, "CONF_DTIME!! SLEEP %d\n", dtime);
					SLEEP(dtime);
					dtime = 0;
				}*/

				if(agent->nClose == 1) {
					break;
				}
				/*
				if(nBufferCheck == 1 && !prepBuffer_isPlayable(playInfo->strKey))  
				{
				sleep(10);
				continue;
				}*/

				pieceData = prepBuffer_getPlayData(playInfo->strKey, skipCount >= gnMaxSkipCount && agent->nCurSendPeerCount + agent->sendPartnerMap.size() > 0);
				//nBufferCheck = pieceData == NULL || !strcmp("", pieceData);
				if(pieceData == NULL /*|| !strcmp("", pieceData)*/) 
				{
					skipCount++;

					LogPrint(LOG_DEBUG, "pieceData == NULL : %d\n", skipCount);
					
					SLEEP(2000);
					continue;
				}
				else
				{
					if (GetSimulationLogPrint() > 0)
					{
						int pp = prepBuffer_getCurrentPP(playInfo->strKey);
						LogPrint(LOG_SIMULATION, "PlayPiece\t\t%d\t%s\t\t%s\n", pp, GetTimeString(prepBuffer_getPieceDataTimestamp(playInfo->strKey, pp) / 1000), GetTimeString(0));
					}

					int ret;

					unsigned long sent_len = 0;
					
					int failedSend = 0;

					skipCount = 0;

					while(sent_len < agent->nPieceSize)
					{
						//int playSize = 262144+1;
						//int playSize = 2048 * 1024;
						int playSize = agent->nPieceSize;
						int remainder = (agent->nPieceSize - sent_len) % playSize;

						if (remainder > 0)
						{
							playSize = remainder;
						}

						if(udp == 1) 
						{
							//udp
							ret=sendto(playInfo->socket, pieceData + sent_len, playSize,0,(struct sockaddr*)&player_addr, sizeof(player_addr));
						}
						else
						{
							//tcp
							LogPrint(LOG_DEBUG, "send start!!!\n");
							ret=send(playInfo->socket, pieceData + sent_len, playSize,0);
							LogPrint(LOG_DEBUG, "send end!!!\n");
						}

						if(ret<=0)
						{
							failedSend = 1;
							LogPrint(LOG_CRITICAL, "Failed to send , ret:%d\n", ret);
							break;
						}
						else
						{
							//DebugPrintCritical2("send : ret:%d\n", ret);
						}


						if(udp == 1) 
						{
							if ((sent_len % 1392) == 0) SLEEP(6);
						}

						sent_len+=ret;

						/*char * ggg = new char[10];
						sprintf(ggg, "%d", ret);
						perror(ggg);*/
					}

					free(pieceData);

					if (failedSend)
					{
						LogPrint(LOG_CRITICAL, "PlayThread Send fail!! restart sock bind.");
						break;
					}
				} 
			}
		}
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);

	return NULL;
}

void *VirtualPlayThread(void *pInfo)
{
	PrepAgent_t *agent;
	ClientInfo_t *Info = (ClientInfo_t *)pInfo;
	ClientInfo_t * playInfo = (ClientInfo_t *)malloc(sizeof(ClientInfo_t));

	LogPrint(LOG_DEBUG, "Server: Start virtual play thread.\n");

	if (playInfo == NULL)
	{
		LogPrint(LOG_CRITICAL, "virtualplaythread error");
		return 0;
	}

	memset(playInfo, 0, sizeof(ClientInfo_t));
	playInfo->strKey = _strdup(Info->strKey);

	agent = _getAgentByKey(playInfo->strKey);

	pthread_cleanup_push(_cleanupVirtualPlayThread, playInfo);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	unsigned int skipCount = 0;

	while (1)
	{
		SLEEP(1000);

		char * pieceData = NULL;

		if (agent->nClose == 1) {
			break;
		}
		
		pieceData = prepBuffer_getPlayData(playInfo->strKey, skipCount >= gnMaxSkipCount && agent->nCurSendPeerCount + agent->sendPartnerMap.size() > 0);
		
		if (pieceData == NULL /*|| !strcmp("", pieceData)*/)
		{
			skipCount++;

			LogPrint(LOG_DEBUG, "pieceData == NULL : %d\n", skipCount);

			continue;
		}
		else
		{
			skipCount = 0;

			int pp = prepBuffer_getCurrentPP(playInfo->strKey);

			char filename[20] = { 0, };
			sprintf(filename, "%d.piece", pp - 1);

			FILE *fp = fopen(filename, "w");

			if (fp == NULL)
			{
				LogPrint(LOG_CRITICAL, "111111Outfile open error!!\n");
			}
			else
			{
				int fr = fwrite(pieceData, 1, agent->nPieceSize, fp);

				if (fr < 0)
				{
					LogPrint(LOG_CRITICAL, "111111Outfile write error\n");
				}

				fclose(fp);
			}

			free(pieceData);
			pieceData = NULL;
		}
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);

	return NULL;
}

void *ClientThread(void *pInfo)
{
	int peerCount=0;
	ClientInfo_t *Info = (ClientInfo_t *)pInfo;
	//	char * urlTmp;
	int cnt = 0, i=0;
	PrepAgent_t * agent = NULL;
	OverlayItem_t ** item;
	OverlayItem_t * overlayItem;
	int oldIndex;

	pthread_cleanup_push(_cleanupClientThread, Info);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL); 
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	agent = _getAgentByKey(Info->strKey);

	while(1) {

		pthread_mutex_lock(&Info->ClientMutex);

		pthread_cond_wait(&Info->ClientCond,&Info->ClientMutex);

		LogPrint(LOG_DEBUG, "fire event %d.\n", peerCount++);

		pthread_mutex_unlock(&Info->ClientMutex);

		if(agent->nClose == 1) {
			break;
		}

		if (agent->nPause == 1) {
			_fireNextEvent(Info, 5);
			LogPrint(LOG_INFO, "일시정지 중입니다. 5초후 재검색을 합니다.\n");
			continue;
		}

		if (agent->nIsPODO)
		{
			item = overlayAction_RetrievePODOOverlayNetwork(Info->strOverlayID, Info->strServerIP, Info->nServerPort, Info->strServerPath, &cnt, agent->strPAID);
		}
		else
		{
			item = overlayAction_RetrieveOverlayNetwork(Info->strOverlayID, Info->strServerIP, Info->nServerPort, Info->strServerPath, &cnt, agent->strPAID);
		}
		
		if (item == NULL || cnt <= 0)
		{
			PrepAgent_FreeOverlayItem(item, cnt);
			LogPrint(LOG_INFO, "overlay 목록이 없습니다. 5초후 재검색을 합니다.\n");
			_fireNextEvent(Info, 5);
			continue;
		}

		agent->nPeerCountInOverlayNetwork = cnt;
		oldIndex = agent->nCurSendPeerCount;
		for (i=0; i<cnt; i++)
		{
			if(agent->nClose == 1) {
				break;
			}

			if (agent->nPause == 1) {
				break;
			}

			overlayItem = item[i];

			if (!strcmp(agent->strPAID, overlayItem->strPAID))
			{
				LogPrint(LOG_DEBUG, "나의 목록이므로 다음 연결을 처리합니다.\n");
				continue;
			}
			else if (agent->nMaxPeerCount < agent->nCurSendPeerCount + 1 && agent->nAgentType != PAMP_TYPE_SEEDER) {
				LogPrint(LOG_DEBUG, "Server %u개에 연결된 상태입니다. 연결제한.\n", agent->nCurSendPeerCount);
				break;
			}
			else if (agent->nMaxPeerCount < agent->nCurRecvPeerCount + 1 && agent->nAgentType == PAMP_TYPE_SEEDER) {
				LogPrint(LOG_DEBUG, "Server %u개에 연결된 상태입니다. 연결제한.\n", agent->nCurRecvPeerCount);
				break;
			}
			else if(isEqualsOverlayItem(agent, overlayItem)) {
				LogPrint(LOG_DEBUG, "이미 연결되어 있는 Server 목록이므로 다음 연결을 처리합니다.\n");
				continue;
			} else {
				PeerInfo_t * peerInfo;
				int verchk = 0;
				int socketfd = -1;
				
				if (agent->nIsPODO)
				{
					verchk = PODOBuffer_isValidVersion(agent->strOverlayID, overlayItem->nActiveTime);

					if (verchk == 0) // 나보다 버젼이 낮아
					{
						continue;
					}
					else if (verchk == -1) // 나보다 버젼이 높아
					{
						//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_VERSION, agent->strOverlayID, NULL, NULL, 0, overlayItem->nActiveTime);
						continue;
					}
				}
				/*
				socketfd = TCP_Connect(overlayItem->strAgentIP, overlayItem->nAgentPort);
				if(socketfd < 0) {
					LogPrint(LOG_DEBUG, "PREP_EVENT_CONNECT_FAIL\n");
					//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_CONNECT_FAIL, Info->strKey, agent->strPAID, overlayItem->strPAID, 0, 0);
					LogPrint(LOG_DEBUG, "PREP_EVENT_CONNECT_FAIL - END\n");
					continue;
				}

				{
#ifdef WIN32
					int ntimeout = 2000;
					// LINGER 구조체의 값 설정  
					LINGER  ling = { 0, };
					ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
					ling.l_linger = 0;  // LINGER Timeout 설정  

					// LINGER 옵션을 Socket에 적용  
					setsockopt(socketfd, SOL_SOCKET, SO_LINGER, (char*)&ling, sizeof(ling));
					setsockopt(socketfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&ntimeout, sizeof(ntimeout));
#else
					struct linger ling = { 0, };
					ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
					ling.l_linger = 0;  // LINGER Timeout 설정
					int sz = sizeof(ling);

					setsockopt(socketfd, SOL_SOCKET, SO_LINGER, &ling, (socklen_t)sz);

					struct timeval tv;
					tv.tv_sec = 2;
					tv.tv_usec = 0;
					setsockopt(socketfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&tv, sizeof(struct timeval));
#endif
				}

				LogPrint(LOG_DEBUG, "agentIP: %s에 접속하였습니다. socket: %d\n", overlayItem->strAgentIP, socketfd);*/

				peerInfo = (PeerInfo_t *)malloc(sizeof(PeerInfo_t));

				if (peerInfo == NULL)
				{
					perror("peerinfo alloc error");
					continue;
				}

				memset(peerInfo, 0, sizeof(PeerInfo_t));
				peerInfo->nDownSetPiece = -1;
				peerInfo->callback = _clientPeerStart;

				LogPrint(LOG_DEBUG, "1111111111111111111111\n");

				peerInfo->socket = socketfd;
				peerInfo->strKey = _strdup(Info->strKey);
				peerInfo->nPeerId = agent->nPeerIdNext++;
				peerInfo->nPartnerId = -1;

				peerInfo->agent = agent;
				peerInfo->parentClient = Info;

				LogPrint(LOG_DEBUG, "22222222222222222222222222\n");

				PeerData_t *peer = (PeerData_t *)malloc(sizeof(PeerData_t));
				if (peer == NULL)
				{
					free(peerInfo);
					perror("peer alloc error");
					continue;
				}

				memset(peer, 0, sizeof(PeerData_t));
				sprintf_s(peer->pa_id, overlayItem->strPAID);
				sprintf_s(peer->ip, overlayItem->strAgentIP);
				peer->port = overlayItem->nAgentPort;
				peer->nBYE = 0;
				peer->nRefresh = 0;

				LogPrint(LOG_DEBUG, "33333333333333333333333333\n");

				if (agent->nAgentType == PAMP_TYPE_SEEDER)
				{
					peerInfo->prepMode = PREP_SERVER_MODE;
					peer->prepMode = PREP_SERVER_MODE;
					agent->nCurRecvPeerCount++;
				}
				else
				{
					peerInfo->prepMode = PREP_CLIENT_MODE;
					peer->prepMode = PREP_CLIENT_MODE;
					agent->nCurSendPeerCount++;
				}
				
				agent->totalPeerMutex.lock();
				PeerMapIter it = agent->totalPeerMap.find(peerInfo->nPeerId);
				if (it != agent->totalPeerMap.end())
				{
					it->second->nBYE = 1;
					agent->totalPeerMap.erase(it);
				}

				agent->totalPeerMap.insert(std::pair<double, PeerData_t*>(peerInfo->nPeerId, peer));
				agent->totalPeerMutex.unlock();

				peerInfo->ip = _strdup(overlayItem->strAgentIP);
				peerInfo->port = overlayItem->nAgentPort;
				peerInfo->id = _strdup(overlayItem->strPAID);
				peer->peerHandle = PTHREAD_CREATE(TotalPeerThread, peerInfo);
				LogPrint(LOG_DEBUG, "socket: %d -> TotalPeerThread 생성 완료\n", socketfd);
				LogPrint(LOG_DEBUG, "nCurRecvPeerCount %u\n", agent->nCurRecvPeerCount);
				LogPrint(LOG_DEBUG, "nCurSendPeerCount %u\n", agent->nCurSendPeerCount);

				SLEEP(1000);
			}
		}

		PrepAgent_FreeOverlayItem(item, cnt);

		if(agent->nClose == 1) {
			break;
		}

		if(oldIndex == agent->nCurSendPeerCount) {
			LogPrint(LOG_DEBUG, "Server %d개에 연결된 상태입니다. 5초후 재시도 요청을 진행합니다.\n", agent->nCurSendPeerCount);
			_fireNextEvent(Info, 5);
		} else if(agent->nCurSendPeerCount < agent->nMaxPeerCount) {
			LogPrint(LOG_DEBUG, "1초후 다음 연결을 진행합니다. (현재 %d / 최대 %d)\n", agent->nCurSendPeerCount, agent->nMaxPeerCount);
			_fireNextEvent(Info, 1);
		}
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);

	return NULL;
}

void *ServerThread(void *pInfo)
{
	ServerInfo_t *Info = (ServerInfo_t *)pInfo;

	int	nfds;			/* 최대 소켓번호 +1 */
	fd_set read_fds;	/* 읽기를 감지할 소켓번호 구조체 */
	struct sockaddr_in 	client_addr, server_addr;

	int client_fd = -1, clilen = 0;

	PrepAgent_t * agent = NULL;
	int nConnectedCount = 0;

	pthread_cleanup_push(_cleanupServerThread, Info);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL); 
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	agent = _getAgentByKey(Info->strKey);

	/* 초기소켓 생성 */
	if((Info->socket = socket(PF_INET, SOCK_STREAM, 0)) < 0)  {
		LogPrint(LOG_CRITICAL, "Server: Can't open stream socket.");
		pthread_exit(NULL);
	}

	agent->ServerSocket = Info->socket;

	/* server_addr 구조체의 내용 세팅 */
	memset((char *)&server_addr, 0, sizeof(server_addr));  
	server_addr.sin_family = AF_INET;              
	server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
	//server_addr.sin_port = htons(atoi(argv[1]));     
	server_addr.sin_port = htons(agent->nPeerPort);

	if (bind(Info->socket,(struct sockaddr *)&server_addr,sizeof(server_addr)) < 0) {
		LogPrint(LOG_CRITICAL, "Server: Can't bind local address.\n");
		pthread_exit(NULL);
	}

	//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_START, Info->strKey, agent->strPAID, NULL, 0, 0);

	/* 클라이언트로부터 연결요청을 기다림 */
	listen(Info->socket, 5);

	nfds = Info->socket + 1;		/* 최대 소켓번호 +1 */
	FD_ZERO(&read_fds);

	while(1) {
		if(agent->nClose == 1) {
			break;
		}

		/* 읽기 변화를 감지할 소켓번호를 fd_set 구조체에 지정 */
		FD_SET(Info->socket, &read_fds);

		/*--------------------------------------- select() 호출 ----------------------------------------- */
		if (select(nfds, &read_fds, (fd_set *)0, (fd_set *)0,(struct timeval *)0) < 0) {
			LogPrint(LOG_CRITICAL, "select error\n");
			pthread_exit(NULL);
		}

		/*------------------------------ 클라이언트 연결요청 처리 ------------------------------- */
		if(FD_ISSET(Info->socket, &read_fds)) {
			clilen = sizeof(client_addr);
#ifdef WIN32
			client_fd = accept(Info->socket, (struct sockaddr *)&client_addr, &clilen);
#else
			client_fd = accept(Info->socket, (struct sockaddr *)&client_addr, (socklen_t *)&clilen);
#endif
			LogPrint(LOG_DEBUG, "%d번째 접속자\n", ++nConnectedCount);

			if(agent->nClose == 1) {
				break;
			}

			if(client_fd != -1)
			{
				{
#ifdef WIN32
					int ntimeout = 2000;
					// LINGER 구조체의 값 설정  
					LINGER  ling = {0,};  
					ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
					ling.l_linger = 0;  // LINGER Timeout 설정  

					// LINGER 옵션을 Socket에 적용  
					setsockopt(client_fd, SOL_SOCKET, SO_LINGER, (char*)&ling, sizeof(ling));
					setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, (char*)&ntimeout, sizeof(ntimeout));
#else
					struct linger ling = {0,};
					ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
					ling.l_linger = 0;  // LINGER Timeout 설정
					int sz = sizeof(ling);

					setsockopt(client_fd, SOL_SOCKET, SO_LINGER, &ling, (socklen_t)sz);

					struct timeval tv;
					tv.tv_sec = 2;
					tv.tv_usec = 0;
					setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, (char*)&tv, sizeof(struct timeval));
#endif
				}

				if (agent->nMaxPeerCount < agent->nCurRecvPeerCount + 1)
				{
					//send(client_fd, &PrepHeaderSend, sizeof(PrepProtoHeader_t), 0);
					//send(client_fd, start, strlen(start), 0);
					LogPrint(LOG_DEBUG, "참가자 초과로 현재 참가자를 종료 처리합니다. 참가자 %u명이 접속된 상태입니다.\n", agent->nCurRecvPeerCount);
					/* 종료시킴 */
					shutdown(client_fd, 2);
					close(client_fd);
				}
				else
				{
					PeerInfo_t * peerInfo = (PeerInfo_t *)malloc(sizeof(PeerInfo_t));
					if (peerInfo == NULL)
					{
						perror("peerinfo alloc error");
						continue;
					}
					memset(peerInfo, 0, sizeof(PeerInfo_t));
					peerInfo->prepMode = PREP_SERVER_MODE;
					peerInfo->socket = client_fd;
					peerInfo->strKey = _strdup(Info->strKey);
					peerInfo->nPeerId = agent->nPeerIdNext++;
					peerInfo->nPartnerId = -1;
					peerInfo->nDownSetPiece = -1;

					peerInfo->agent = agent;

					PeerData_t *peer = (PeerData_t *)malloc(sizeof(PeerData_t));
					if (peer == NULL)
					{
						free(peerInfo);
						perror("peer alloc error");
						continue;
					}
					memset(peer, 0, sizeof(PeerData_t));
					peer->prepMode = PREP_SERVER_MODE;
					peer->nBYE = 0;
					peer->nRefresh = 0;
					
					agent->totalPeerMutex.lock();
					PeerMapIter it = agent->totalPeerMap.find(peerInfo->nPeerId);
					if (it != agent->totalPeerMap.end())
					{
						it->second->nBYE = 1;
						agent->totalPeerMap.erase(it);
					}

					agent->totalPeerMap.insert(std::pair<double, PeerData_t*>(peerInfo->nPeerId, peer));
					agent->totalPeerMutex.unlock();

					agent->nCurRecvPeerCount++;
					peer->peerHandle = PTHREAD_CREATE(TotalPeerThread, peerInfo);
					LogPrint(LOG_DEBUG, "Create ServerPeerThread.\n");
					LogPrint(LOG_DEBUG, "nCurRecvPeerCount : %u\n", agent->nCurRecvPeerCount);
				}
			}
		}

		LogPrint(LOG_INFO, "Client 접속 상태: 현재 %d / 최대 %d\n", agent->nCurRecvPeerCount, agent->nMaxPeerCount);
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);
	
	close(client_fd);

	return NULL;
}

#define  COMMUNICATE_GET 1
#define  COMMUNICATE_SET 2

#define  COMMUNICATE_MAX_UPLOAD 1
#define  COMMUNICATE_MAX_DOWNLOAD 2
#define  COMMUNICATE_CUR_UPLOAD 3
#define  COMMUNICATE_CUR_DOWNLOAD 4
#define  COMMUNICATE_MAX_PEER 5
#define  COMMUNICATE_CUR_SENDPEER 6
#define  COMMUNICATE_CUR_SENDPEERLIST 7
#define  COMMUNICATE_CUR_RECVPEER 8
#define  COMMUNICATE_CUR_RECVPEERLIST 9
#define  COMMUNICATE_MAX_PARTNER 10
#define  COMMUNICATE_CUR_SENDPARTNER 11
#define  COMMUNICATE_CUR_SENDPARTNERLIST 12
#define  COMMUNICATE_CUR_RECVPARTNER 13
#define  COMMUNICATE_CUR_RECVPARTNERLIST 14
#define  COMMUNICATE_CUR_SP 15
#define  COMMUNICATE_CUR_PP 16
#define  COMMUNICATE_CUR_CP 17
#define  COMMUNICATE_CUR_CS 18
#define  COMMUNICATE_CUR_DP 19
#define  COMMUNICATE_CUR_BUFFER_STATUS 20
#define  COMMUNICATE_LOG_PRINT_LEVEL 21
#define  COMMUNICATE_PLAYSYNC 22
#define  COMMUNICATE_CUR_DOWNUP 23
#define  COMMUNICATE_CUR_PEERS 24

void *CommunicateThread(void *pInfo)
{
	ServerInfo_t *Info = (ServerInfo_t *)pInfo;

	int	nfds;			/* 최대 소켓번호 +1 */
	fd_set read_fds;	/* 읽기를 감지할 소켓번호 구조체 */
	struct sockaddr_in 	client_addr, server_addr;

	int client_fd = -1, clilen = 0;

	PrepAgent_t * agent = NULL;
	//int nConnectedCount = 0;

	pthread_cleanup_push(_cleanupCommunicateThread, Info);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	agent = _getAgentByKey(Info->strKey);

	/* 초기소켓 생성 */
	if ((Info->socket = socket(PF_INET, SOCK_STREAM, 0)) < 0)  {
		LogPrint(LOG_CRITICAL, "Server: Can't open stream socket.");
		pthread_exit(NULL);
	}

	agent->CommunicateSocket = Info->socket;

	/* server_addr 구조체의 내용 세팅 */
	memset((char *)&server_addr, 0, sizeof(server_addr));
	server_addr.sin_family = AF_INET;
	server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
	//server_addr.sin_port = htons(atoi(argv[1]));     
	server_addr.sin_port = htons(agent->nCommunicatePort);

	if (bind(Info->socket, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
		LogPrint(LOG_CRITICAL, "Server: Can't bind local address.\n");
		pthread_exit(NULL);
	}
	
	/* 클라이언트로부터 연결요청을 기다림 */
	listen(Info->socket, 5);

	nfds = Info->socket + 1;		/* 최대 소켓번호 +1 */
	FD_ZERO(&read_fds);

	while (1) {
		if (agent->nClose == 1) {
			break;
		}

		/* 읽기 변화를 감지할 소켓번호를 fd_set 구조체에 지정 */
		FD_SET(Info->socket, &read_fds);

		/*--------------------------------------- select() 호출 ----------------------------------------- */
		if (select(nfds, &read_fds, (fd_set *)0, (fd_set *)0, (struct timeval *)0) < 0) {
			LogPrint(LOG_CRITICAL, "select error\n");
			pthread_exit(NULL);
		}

		/*------------------------------ 클라이언트 연결요청 처리 ------------------------------- */
		if (FD_ISSET(Info->socket, &read_fds)) {
			clilen = sizeof(client_addr);
#ifdef WIN32
			client_fd = accept(Info->socket, (struct sockaddr *)&client_addr, &clilen);
#else
			client_fd = accept(Info->socket, (struct sockaddr *)&client_addr, (socklen_t *)&clilen);
#endif
			LogPrint(LOG_DEBUG, "Communicate 접속\n");

			if (agent->nClose == 1) {
				break;
			}

			if (client_fd != -1)
			{
				{
#ifdef WIN32
					int ntimeout = 2000;
					// LINGER 구조체의 값 설정  
					LINGER  ling = { 0, };
					ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
					ling.l_linger = 0;  // LINGER Timeout 설정  

					// LINGER 옵션을 Socket에 적용  
					setsockopt(client_fd, SOL_SOCKET, SO_LINGER, (char*)&ling, sizeof(ling));
					setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, (char*)&ntimeout, sizeof(ntimeout));
#else
					struct linger ling = { 0, };
					ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
					ling.l_linger = 0;  // LINGER Timeout 설정
					int sz = sizeof(ling);

					setsockopt(client_fd, SOL_SOCKET, SO_LINGER, &ling, (socklen_t)sz);

					struct timeval tv;
					tv.tv_sec = 2;
					tv.tv_usec = 0;
					setsockopt(client_fd, SOL_SOCKET, SO_RCVTIMEO, (char*)&tv, sizeof(struct timeval));
#endif
				}

				int nfds;
				fd_set read_fds;
				int ret;
				
				struct timeval timeout;
				
				nfds = client_fd + 1;
				FD_ZERO(&read_fds);

				double sync = -1;
				int lastidx = 0;

				while (1) {
					if (agent->nClose == 1) {
						break;
					}

					FD_SET(client_fd, &read_fds);
					timeout.tv_sec = 2;
					timeout.tv_usec = 0;
					ret = select(nfds, &read_fds, (fd_set *)0, (fd_set *)0, &timeout);
					if (ret < 0) {
						LogPrint(LOG_CRITICAL, "Communicate socket : %d error\n", client_fd);
						perror("Communicate select()");
						break;
					}

					if (agent->nClose == 1) {
						break;
					}

					if (ret == 0)
					{
						continue;
					}

					if (FD_ISSET(client_fd, &read_fds))
					{
						int size = 0;
						char hbuf[2] = { 0, };
						size = recv(client_fd, hbuf, 2, 0);

						if (size <= 0 || hbuf[0] <= 0)
						{
							LogPrint(LOG_CRITICAL, "Communicate recv error!! socket : %d\n", client_fd);
							perror("Communicate recv()");
							break;
						}

						if (hbuf[0] == COMMUNICATE_GET)
						{
							int val = -1;

							if (hbuf[1] == COMMUNICATE_MAX_UPLOAD)
							{
								val = (int)agent->dUploadBpsLimit;
							}
							else if (hbuf[1] == COMMUNICATE_MAX_DOWNLOAD)
							{
								val = (int)agent->dDownloadBpsLimit;
							}
							else if (hbuf[1] == COMMUNICATE_MAX_PEER)
							{
								val = agent->nMaxPeerCount;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_UPLOAD)
							{
								val = (int)agent->dUploadBps;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_DOWNLOAD)
							{
								val = (int)agent->dDownloadBps;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_DOWNUP)
							{
								val = -1;

								char *buf = new char[1 + 4 + 4];
								buf[0] = hbuf[1];

								int down = (int)agent->dDownloadBps;
								int up = (int)agent->dUploadBps;

								down = htonl(down);
								up = htonl(up);

								memcpy(buf + 1, &down, 4);
								memcpy(buf + 1 + 4, &up, 4);
								SLEEP(10);
								send(client_fd, buf, 1 + 4 + 4, 0);

								delete[] buf;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_SENDPEER)
							{
								val = agent->nCurSendPeerCount;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_SENDPEERLIST)
							{
								val = -1;

								bsonobjbuilder arr;
								agent->totalPeerMutex.lock();
								for (PeerMapIter it = agent->totalPeerMap.begin(); it != agent->totalPeerMap.end(); ++it)
								{
									if (it->second->prepMode == PREP_CLIENT_MODE)
									{
										bsonobjbuilder peer;
										peer.append("id", it->second->pa_id);

										arr.append("", peer.obj());
									}
								}
								agent->totalPeerMutex.unlock();
								bsonobjbuilder total;
								total.appendArray("peers", arr.obj());

								char *buf = new char[total.obj().objsize() + 1];
								buf[0] = hbuf[1];
								memcpy(buf + 1, total.obj().objdata(), total.obj().objsize());

								//send(client_fd, total.obj().objdata(), total.obj().objsize(), 0);
								send(client_fd, buf, total.obj().objsize() + 1, 0);

								delete[] buf;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_RECVPEER)
							{
								val = agent->nCurRecvPeerCount;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_RECVPEERLIST)
							{
								val = -1;

								bsonobjbuilder arr;

								agent->totalPeerMutex.lock();
								for (PeerMapIter it = agent->totalPeerMap.begin(); it != agent->totalPeerMap.end(); ++it)
								{
									if (it->second->prepMode == PREP_SERVER_MODE)
									{
										bsonobjbuilder peer;
										peer.append("id", it->second->pa_id);

										arr.append("", peer.obj());
									}
								}
								agent->totalPeerMutex.unlock();

								/*bsonobjbuilder total;
								total.appendArray("peers", arr.obj());

								send(client_fd, total.obj().objdata(), total.obj().objsize(), 0);*/

								bsonobjbuilder total;
								total.appendArray("peers", arr.obj());

								char *buf = new char[total.obj().objsize() + 1];
								buf[0] = hbuf[1];
								memcpy(buf + 1, total.obj().objdata(), total.obj().objsize());

								//send(client_fd, total.obj().objdata(), total.obj().objsize(), 0);
								send(client_fd, buf, total.obj().objsize() + 1, 0);

								delete[] buf;
							}
							else if (hbuf[1] == COMMUNICATE_MAX_PARTNER)
							{
								val = agent->nMaxPartnerCount;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_SENDPARTNER)
							{
								val = (int)agent->sendPartnerMap.size();
							}
							else if (hbuf[1] == COMMUNICATE_CUR_SENDPARTNERLIST)
							{
								val = -1;

								bsonobjbuilder arr;

								agent->sendPartnerMutex.lock();
								for (PartnerMapIter it = agent->sendPartnerMap.begin(); it != agent->sendPartnerMap.end(); ++it)
								{
									bsonobjbuilder peer;
									peer.append("id", it->second->peerData->pa_id);

									arr.append("", peer.obj());
								}
								agent->sendPartnerMutex.unlock();

								/*bsonobjbuilder total;
								total.appendArray("peers", arr.obj());

								send(client_fd, total.obj().objdata(), total.obj().objsize(), 0);*/

								bsonobjbuilder total;
								total.appendArray("peers", arr.obj());

								char *buf = new char[total.obj().objsize() + 1];
								buf[0] = hbuf[1];
								memcpy(buf + 1, total.obj().objdata(), total.obj().objsize());

								//send(client_fd, total.obj().objdata(), total.obj().objsize(), 0);
								send(client_fd, buf, total.obj().objsize() + 1, 0);

								delete[] buf;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_RECVPARTNER)
							{
								val = agent->recvPartnerMap.size();
							}
							else if (hbuf[1] == COMMUNICATE_CUR_RECVPARTNERLIST)
							{
								val = -1;

								bsonobjbuilder arr;

								agent->recvPartnerMutex.lock();
								for (PartnerMapIter it = agent->recvPartnerMap.begin(); it != agent->recvPartnerMap.end(); ++it)
								{
									bsonobjbuilder peer;
									peer.append("id", it->second->peerData->pa_id);

									arr.append("", peer.obj());
								}
								agent->recvPartnerMutex.unlock();

								/*bsonobjbuilder total;
								total.appendArray("peers", arr.obj());

								send(client_fd, total.obj().objdata(), total.obj().objsize(), 0);*/

								bsonobjbuilder total;
								total.appendArray("peers", arr.obj());

								char *buf = new char[total.obj().objsize() + 1];
								buf[0] = hbuf[1];
								memcpy(buf + 1, total.obj().objdata(), total.obj().objsize());

								//send(client_fd, total.obj().objdata(), total.obj().objsize(), 0);
								send(client_fd, buf, total.obj().objsize() + 1, 0);

								delete[] buf;
							}
							else if (hbuf[1] == COMMUNICATE_CUR_PP)
							{
								val = prepBuffer_getCurrentPP(agent->strOverlayID);
							}
							else if (hbuf[1] == COMMUNICATE_CUR_DP)
							{
								val = prepBuffer_getCurrentDP(agent->strOverlayID);
							}
							else if (hbuf[1] == COMMUNICATE_CUR_CP)
							{
								val = prepBuffer_getCurrentCP(agent->strOverlayID);
							}
							else if (hbuf[1] == COMMUNICATE_CUR_CS)
							{
								val = prepBuffer_getCurrentCS(agent->strOverlayID);
							}
							else if (hbuf[1] == COMMUNICATE_CUR_SP)
							{
								val = prepBuffer_getCurrentSP(agent->strOverlayID);
							}
							else if (hbuf[1] == COMMUNICATE_CUR_BUFFER_STATUS)
							{
								int pp = 0, sp = 0, cp = 0, dp = 0, cs = 0;
								prepBuffer_getCurrentBufferStatus(agent->strOverlayID, sp, pp, cp, cs, dp);

								val = -1;

								bsonobjbuilder bson;

								bson.append("sp", sp);
								bson.append("pp", pp);
								bson.append("cp", cp);
								bson.append("cs", cs);
								bson.append("dp", dp);

								char *buf = new char[bson.obj().objsize() + 1];
								buf[0] = hbuf[1];
								memcpy(buf + 1, bson.obj().objdata(), bson.obj().objsize());

								//send(client_fd, bson.obj().objdata(), bson.obj().objsize(), 0);
								SLEEP(10);
								send(client_fd, buf, bson.obj().objsize() + 1, 0);

								delete[] buf;
							}
							else if (hbuf[1] == COMMUNICATE_LOG_PRINT_LEVEL)
							{
								val = GetLogLevel();
							}
							else if (hbuf[1] == COMMUNICATE_PLAYSYNC)
							{
								if (sync < 0)
								{
									if (prepBuffer_getCurrentCS(agent->strOverlayID) > 10)
									{
										sync = 1;
										val = 1;
									}
									else
									{
										val = 0;
									}
								}
								else
								{
									val = 1;
								}
							}
							else if (hbuf[1] == COMMUNICATE_CUR_PEERS)
							{
								val = -1;

								bsonobjbuilder from;
								bsonobjbuilder to;

								agent->totalPeerMutex.lock();
								agent->sendPartnerMutex.lock();
								agent->recvPartnerMutex.lock();

								for (PeerMapIter it = agent->totalPeerMap.begin(); it != agent->totalPeerMap.end(); ++it)
								{
									if (it->second->prepMode == PREP_CLIENT_MODE)
									{
										bsonobjbuilder peer;
										peer.append("id", it->second->pa_id);

										from.append("", peer.obj());
									}
									else
									{
										bsonobjbuilder peer;
										peer.append("id", it->second->pa_id);

										to.append("", peer.obj());
									}
								}
								agent->totalPeerMutex.unlock();

								bsonobjbuilder total;
								total.appendArray("from", from.obj());
								total.appendArray("to", to.obj());

								bsonobjbuilder fromp;


								for (PartnerMapIter it = agent->sendPartnerMap.begin(); it != agent->sendPartnerMap.end(); ++it)
								{
									bsonobjbuilder peer;
									peer.append("id", it->second->peerData->pa_id);

									fromp.append("", peer.obj());
								}
								agent->sendPartnerMutex.unlock();

								total.appendArray("fromp", fromp.obj());

								bsonobjbuilder top;


								for (PartnerMapIter it = agent->recvPartnerMap.begin(); it != agent->recvPartnerMap.end(); ++it)
								{
									bsonobjbuilder peer;
									peer.append("id", it->second->peerData->pa_id);

									top.append("", peer.obj());
								}
								agent->recvPartnerMutex.unlock();

								total.appendArray("top", top.obj());

								char *buf = new char[total.obj().objsize() + 1];
								buf[0] = hbuf[1];
								memcpy(buf + 1, total.obj().objdata(), total.obj().objsize());
								SLEEP(10);
								//send(client_fd, total.obj().objdata(), total.obj().objsize(), 0);
								send(client_fd, buf, total.obj().objsize() + 1, 0);

								delete[] buf;
							}

							if (val >= 0)
							{
								val = htonl(val);
								//send(client_fd, (char*)&val, 4, 0);
								char* buf = new char[5];
								buf[0] = hbuf[1];
								memcpy(buf + 1, &val, 4);
								send(client_fd, buf, 5, 0);

								delete[] buf;
							}
						}
						else if (hbuf[0] == COMMUNICATE_SET)
						{
							int val = 0;

							size = (int)recv(client_fd, (char*)&val, 4, 0);

							if (size <= 0)
							{
								perror("Communicate recv()");
								break;
							}

							val = ntohl(val);

							if (hbuf[1] == COMMUNICATE_MAX_UPLOAD)
							{
								agent->dUploadBpsLimit = val;
							}
							else if (hbuf[1] == COMMUNICATE_MAX_DOWNLOAD)
							{
								agent->dDownloadBpsLimit = val;
							}
							else if (hbuf[1] == COMMUNICATE_MAX_PEER)
							{
								agent->nMaxPeerCount = val;
							}
							else if (hbuf[1] == COMMUNICATE_LOG_PRINT_LEVEL)
							{
								LogPrint(LOG_CRITICAL, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
								LogPrint(LOG_CRITICAL, "Log Level 변경! %d --> %d\n", GetLogLevel(), val);
								LogPrint(LOG_CRITICAL, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
								SetLogLevel(val);
							}
						}
					}
				}
			}
		}
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);

	close(client_fd);

	return NULL;
}

std::string AddDoubleQuote(std::string val);
/*{
	return "\"" + val + "\"";
}*/

void *PAMReportThread(void *pInfo)
{
	PAMInfo_t *Info = (PAMInfo_t *)pInfo;

	std::string url = Info->strPAMSURL;
	free(Info->strPAMSURL);
	Info->strPAMSURL = NULL;

	pthread_cleanup_push(_cleanupPAMReportThread, Info);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	PrepAgent_t * agent = _getAgentByKey(Info->strKey);

	bsonobjbuilder peerbson;
	peerbson.append(AddDoubleQuote(JSON_KEY_PAMP_PEER_ID), agent->strPAID);
	if (agent->nAgentType == PAMP_TYPE_PEER || agent->nAgentType == PAMP_TYPE_SEEDER)
	{
		peerbson.append(AddDoubleQuote(JSON_KEY_TYPE), PAMP_TYPE_PEER_STR);
	}
	else if (agent->nAgentType == PAMP_TYPE_CS)
	{
		peerbson.append(AddDoubleQuote(JSON_KEY_TYPE), PAMP_TYPE_CS_STR);
	}
	else if (agent->nAgentType == PAMP_TYPE_RS)
	{
		peerbson.append(AddDoubleQuote(JSON_KEY_TYPE), PAMP_TYPE_RS_STR);
	}

	bsonobjbuilder regbson;
	regbson.append(AddDoubleQuote(JSON_KEY_PEER_INFOMATION), peerbson.obj());

	int resCode = 0;

	
	url.append("/peer");

	std::string rslt = HttpREST::Post(url, regbson.obj().toString(), &resCode);
	if (resCode == HTTP_SUCCESS)
	{
		bsonobjbuilder b;
		std::stringstream st(rslt);
		bsonobj rsltjson = fromjson(st, b);

		if (rsltjson.hasElement(JSON_KEY_PAMP_PAM_CONF))
		{
			bsonobj pamobj = rsltjson[JSON_KEY_PAMP_PAM_CONF].object();
			bool pamena = pamobj[JSON_KEY_PAMP_PAM_ENABLED].Bool();

			if (pamena)
			{
				Info->strPAMSURL = _strdup(pamobj[JSON_KEY_PAMP_PAMS_URL].String().c_str());
				Info->nInterval = pamobj[JSON_KEY_PAMP_PAM_INTERVAL].Int();
				agent->nPAMInterval = Info->nInterval;
			}
			else
			{
				Info->nInterval = 0;
				agent->nPAMInterval = 0;
			}
		}
	}

	while (Info->nInterval > 0)
	{
		for (int i = 0; i < Info->nInterval; i++)
		{
			if (agent->nClose == 1) {
				break;
			}

			SLEEP(1000);
		}

		if (agent->nClose == 1) {
			break;
		}

		bsonobjbuilder dsr;
		dsr.append(AddDoubleQuote(JSON_KEY_OVERLAY_EVENT), PAMP_OVERLAY_EVENT_STARTED);
		char tmp[15] = {0,};

		sprintf_s(tmp, "%.0lf", agent->dTotalUploadBytes / 1024);

		dsr.append(AddDoubleQuote(JSON_KEY_UPLOADED), tmp);

		sprintf_s(tmp, "%.0lf", agent->dTotalDownloadBytes / 1024);

		dsr.append(AddDoubleQuote(JSON_KEY_DOWNLOADED), tmp);
		dsr.append(AddDoubleQuote(JSON_KEY_LEFT), "0");
		dsr.append(AddDoubleQuote(JSON_KEY_NUM_UPLOAD_CONNECTION), agent->nCurRecvPeerCount);
		dsr.append(AddDoubleQuote(JSON_KEY_NUM_DOWNLOAD_CONNECTION), agent->nCurSendPeerCount);

		agent->pieceEventMutex.lock();
		bsonobjbuilder pebs;
		while (!agent->pieceEventList.empty())
		{
			PieceEvent_t *pe = agent->pieceEventList.front();

			bsonobjbuilder peb;
			peb.append(AddDoubleQuote(JSON_KEY_PIECE_EVENT_TYPE), pe->type == PAMP_OVERLAY_EVENT_UPLOADED ? PAMP_OVERLAY_EVENT_UPLOADED_STR : PAMP_OVERLAY_EVENT_DOWNLOADED_STR);
			char tmp[10];

			sprintf_s(tmp, "%d", pe->id);

			peb.append(AddDoubleQuote(JSON_KEY_PIECE_ID), tmp);
			peb.append(AddDoubleQuote(JSON_KEY_PIECE_INTEGRITY), pe->integrity);
			peb.append(AddDoubleQuote(JSON_KEY_TO), pe->to);
			peb.append(AddDoubleQuote(JSON_KEY_FROM), pe->from);
			
			pebs.append(AddDoubleQuote(""), peb.obj());
			
			agent->pieceEventList.pop_front();
			delete pe;
		}
		agent->pieceEventMutex.unlock();

		dsr.appendArray(AddDoubleQuote(JSON_KEY_PIECE_EVENT), pebs.obj());

		bsonobjbuilder ssr;
		ssr.append(AddDoubleQuote(JSON_KEY_MAX_UP_BW), (int)(agent->dUploadBpsLimit / 1024));
		ssr.append(AddDoubleQuote(JSON_KEY_MAX_DN_BW), (int)(agent->dDownloadBpsLimit / 1024));
		ssr.append(AddDoubleQuote(JSON_KEY_MAX_UP_BW_PER_NET), (int)(agent->dAllUploadBpsLimit / 1024));
		ssr.append(AddDoubleQuote(JSON_KEY_MAX_DN_BW_PER_NET), (int)(agent->dAllDownloadBpsLimit / 1024));
		ssr.append(AddDoubleQuote(JSON_KEY_MAX_NUM_CONN_FOR_UP), agent->nMaxPeerCount);
		ssr.append(AddDoubleQuote(JSON_KEY_MAX_NUM_CONN_FOR_UP_PER_NET), 0);
		ssr.append(AddDoubleQuote(JSON_KEY_MAX_NUM_ACTIVE_NET), /*agent->nPeerCountInOverlayNetwork*/0);

		bsonobjbuilder psr;
		psr.append(AddDoubleQuote(JSON_KEY_DYNAMIC_STATUS_REPORT), dsr.obj());
		psr.append(AddDoubleQuote(JSON_KEY_STATIC_STATUS_REPORT), ssr.obj());

		bsonobjbuilder all;
		all.append(AddDoubleQuote(JSON_KEY_PEER_STATUS_REPORT), psr.obj());

		std::string rslt = HttpREST::Put(Info->strPAMSURL, all.obj().toString(), &resCode);
		if (resCode != HTTP_SUCCESS)
		{
			std::stringstream err;
			err << "PAM Report error : ";
			err << resCode;
			perror(err.str().c_str());
		}
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);

	return NULL;
}

void *TotalPeerThread(void *pInfo)
{
#ifndef WIN32
	signal(SIGPIPE, SIG_IGN);
#endif
	PeerInfo_t *Info = (PeerInfo_t *)pInfo;

	pthread_cleanup_push(_cleanupTotalPeerThread, pInfo);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	if (Info->ip !=  NULL && strlen_s(Info->ip) > 0)
	{
		int socketfd = -1;

		socketfd = TCP_Connect(Info->ip, Info->port);
		if (socketfd < 0)
		{
			LogPrint(LOG_DEBUG, "PREP_EVENT_CONNECT_FAIL\n");
			//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_CONNECT_FAIL, Info->strKey, agent->strPAID, overlayItem->strPAID, 0, 0);
			LogPrint(LOG_DEBUG, "PREP_EVENT_CONNECT_FAIL - END\n");
		}
		else
		{
#ifdef WIN32
			int ntimeout = 2000;
			// LINGER 구조체의 값 설정  
			LINGER  ling = { 0, };
			ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
			ling.l_linger = 0;  // LINGER Timeout 설정  

			// LINGER 옵션을 Socket에 적용  
			setsockopt(socketfd, SOL_SOCKET, SO_LINGER, (char*)&ling, sizeof(ling));
			setsockopt(socketfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&ntimeout, sizeof(ntimeout));
#else
			struct linger ling = { 0, };
			ling.l_onoff = 1;   // LINGER 옵션 사용 여부  
			ling.l_linger = 0;  // LINGER Timeout 설정
			int sz = sizeof(ling);

			setsockopt(socketfd, SOL_SOCKET, SO_LINGER, &ling, (socklen_t)sz);

			struct timeval tv;
			tv.tv_sec = 2;
			tv.tv_usec = 0;
			setsockopt(socketfd, SOL_SOCKET, SO_RCVTIMEO, (char*)&tv, sizeof(struct timeval));
#endif
			LogPrint(LOG_DEBUG, "agentIP: %s에 접속하였습니다. socket: %d\n", Info->ip, socketfd);

			Info->socket = socketfd;

			ProcessPeer(pInfo, 1);

			LogPrint(LOG_DEBUG, "ProcessPeer END");
		}
	}
	else
	{
		ProcessPeer(pInfo, 1);

		LogPrint(LOG_DEBUG, "ProcessPeer END");
	}

	pthread_exit(NULL);

	LogPrint(LOG_DEBUG, "pthread_exit(NULL)");

	pthread_cleanup_pop(0);

	LogPrint(LOG_DEBUG, "pthread_cleanup_pop");

	return NULL;
}

#include "bson/bsonobjbuilder.h"
#include "bson/json.h"
#include "Protocol/JsonKey.h"
using namespace _bson;

void ProcessPeer(void *pInfo, int nTimeout) 
{
	PeerInfo_t *Info = (PeerInfo_t *)pInfo;
	int nfds; 
	fd_set read_fds;
	int ret;
	int nEndOfProcess = 1;

	//int timeOutCheck = 0;

	struct timeval timeout;
	timeout.tv_sec = nTimeout;
	timeout.tv_usec = 0;

	if(Info->callback != NULL) {
		Info->callback(pInfo);
	}

	nfds = Info->socket + 1; 
	FD_ZERO(&read_fds);
	while(1) { 

		LogPrint(LOG_DEBUG, "ProcessPeer sock:%d, partnerid : %d, peerid : %d\n", Info->socket, Info->nPartnerId, Info->nPeerId);

		if(Info->agent->nClose == 1) {
			sendBYE(Info);
			break;
		}

		if (Info->agent->nPause)
		{
			sendBYE(Info);
			break;
		}

		if (Info->nPartnerId >= 0)
		{
			if (Info->prepMode == PREP_SERVER_MODE)
			{
				PartnerMapIter it = Info->agent->recvPartnerMap.find(Info->nPartnerId);

				if (it != Info->agent->recvPartnerMap.end())
				{
					if (it->second->nBYE)
					{
						break;
					}
					else if (it->second->notifyData != NULL)
					{
						NotifyData_t * data = it->second->notifyData;

						it->second->notifyData = data->next;

						int ret = sendNOTIFY(Info, Info->socket, data->piece_index);

						LogPrint(LOG_DEBUG, "sendNOTIFY : %u\n", data->piece_index);

						free(data);

						if (ret <= 0)
						{
							break;
						}
					}
				}
			}
			else if (Info->prepMode == PREP_CLIENT_MODE)
			{
				PartnerMapIter it = Info->agent->sendPartnerMap.find(Info->nPartnerId);

				if (it != Info->agent->sendPartnerMap.end())
				{
					if (Info->agent->sendPartnerMap[Info->nPartnerId]->nBYE)
					{
						break;
					}
					
					if (Info->agent->nPartnerTimeout > 0)
					{
						if (Info->agent->sendPartnerMap[Info->nPartnerId]->notifyTime + Info->agent->nPartnerTimeout < GetNTPTimestamp())
						{
							LogPrint(LOG_CRITICAL, "!!!!!!!! 파트너 타임아웃으로 파트너 삭제 !!!!!!!!!!\n");

							Info->agent->sendPartnerMap[Info->nPartnerId]->nBYE = 1;
							break;
						}
					}
				}
			}
		}

		/* -------------------------------------- selelct() 호출 ------------------------*/
		FD_SET(Info->socket, &read_fds);
		timeout.tv_sec = nTimeout;
		ret = select(nfds, &read_fds, (fd_set *)0, (fd_set *)0, &timeout);
		if(ret < 0) { 
			LogPrint(LOG_CRITICAL, "socket : %d error\n", Info->socket);
			perror("select()");
			break;
		}

		if(Info->agent->nClose == 1) {
			sendBYE(Info);
			break;
		}

		if (Info->agent->nPause)
		{
			sendBYE(Info);
			break;
		}

		if (Info->nPartnerId < 0 && Info->nPeerId >= 0)
		{
			PeerMapIter it = Info->agent->totalPeerMap.find(Info->nPeerId);

			if (it != Info->agent->totalPeerMap.end())
			{
				if (it->second->nRefresh)
				{
					it->second->nRefresh = 0;
					sendREFRESH(Info, prepBuffer_getCurrentDP(Info->strKey));
				}
				else if (it->second->nBYE)
				{
					sendBYE(Info);
					break;
				}

			}
			else break;
		}

		if(ret == 0)
		{
			/*timeOutCheck++;

			if (timeOutCheck > 5)
			{
				LogPrint(LOG_DEBUG, "\n!!!! Timeout !!!!! partnerid : %d, peerid : %d\n", Info->nPartnerId, Info->nPeerId);
				break;
			}


			LogPrint(LOG_DEBUG, "\n!!!! Timeout check %d !!!!! partnerid : %d, peerid : %d\n", timeOutCheck, Info->nPartnerId, Info->nPeerId);
			*/
			continue;
		}

		//timeOutCheck = 0;

		/*------------------------- 서버로부터 수신한 메시지 처리 -------------------------*/ 
		if (FD_ISSET(Info->socket, &read_fds)) { 
			int size = 0, len = 0;
			size = recv(Info->socket, (char*)&len, 4, 0);

			//len = align2LittleEndianI(len);

			if (size <= 0 || len <= 0)
			{
				LogPrint(LOG_DEBUG, "processpeer recv error!!111 socket : %d\n", Info->socket);
				//perror("recv()");
				break;
			}

			char* buf = new char[len];
			memset(buf, 0, len);
			cpymem(buf, &len, 4);
			
			int rec = 4;
			while (rec < len)
			{
				while (!Info->agent->nClose && Info->agent->dDownloadBpsLimit > 0 && Info->agent->dSecDownloadBytes >= Info->agent->dDownloadBpsLimit)
				{
					SLEEP(100);
				}

				size = recv(Info->socket, buf + rec, len - rec, 0);
				LogPrint(LOG_DEBUG, "recv size %d,  socket : %d\n", size, Info->socket);
				if (size <= 0)
				{
					break;
				}

				rec += size;

				Info->agent->dTotalDownloadBytes += size;
				Info->agent->dSecDownloadBytes += size;
			}

			if (rec != len )
			{
				LogPrint(LOG_DEBUG, "processpeer recv error!!222 socket : %d\n", Info->socket);
				//perror("recv()");
				sendBYE(Info);
				break;
			}

			bsonobj bson(buf);

			std::string msgtype = bson[JSON_KEY_METHOD].String();

			if (msgtype == PP_METHOD_PELLO)
			{
				nEndOfProcess = recvPELLO(Info, bson);
			}
			else if (msgtype == PP_METHOD_HELLO)
			{
				nEndOfProcess = recvHELLO(Info, bson);
			}
			else if (msgtype == PP_METHOD_REFRESH)
			{
				nEndOfProcess = recvREFRESH(Info, bson);
			}
			else if (msgtype == PP_METHOD_BUFFERMAP)
			{
				nEndOfProcess = recvBUFFERMAP(Info, bson);
			}
			else if (msgtype == PP_METHOD_GET)
			{
				nEndOfProcess = recvGET(Info, bson);
			}
			else if (msgtype == PP_METHOD_BUSY)
			{
				nEndOfProcess = recvBUSY(Info, bson);
			}
			else if (msgtype == PP_METHOD_DATA)
			{
				nEndOfProcess = recvDATA(Info, bson);
			}
			else if (msgtype == PP_METHOD_CANCEL)
			{
				nEndOfProcess = recvDATACANCEL(Info, bson);
			}
			else if (msgtype == PP_METHOD_PARTNER_REQUEST)
			{
				if (recvPARTNER(Info, bson) == 1) {
					Info->agent->totalPeerMutex.lock();
					Info->agent->totalPeerMap.erase(Info->nPeerId);
					Info->agent->totalPeerMutex.unlock();
					/*Info->agent->recvPeerData[Info->nPeerIndex] = NULL;*/
					Info->agent->nCurRecvPeerCount--;
					LogPrint(LOG_DEBUG, "nCurRecvPeerCount: %u\n", Info->agent->nCurRecvPeerCount);

					_fireNextEvent(Info->parentClient, 0);
				}
				//break;
			}
			else if (msgtype == PP_METHOD_PARTNER_RESPONSE)
			{
				int result = recvRESULT(Info, bson);
				if (result == 1) {

// 					if (Info->prepMode == PREP_SERVER_MODE)
// 					{
// 						Info->agent->recvPeerData[Info->nPeerIndex] = NULL;
// 						Info->agent->nCurRecvPeerCount--;
// 					}
// 					else
					{
						Info->agent->totalPeerMutex.lock();
						Info->agent->totalPeerMap.erase(Info->nPeerId);
						//Info->agent->sendPeerData[Info->nPeerIndex] = NULL;
						Info->agent->totalPeerMutex.unlock();
						Info->agent->nCurSendPeerCount--;
					}

					//Info->agent->nCurSendPartnerCount++;
					LogPrint(LOG_DEBUG, "nCurrentPeerCount: %u\n", Info->agent->nCurSendPeerCount);
					LogPrint(LOG_DEBUG, "nCurSendPartnerCount: %u\n", Info->agent->sendPartnerMap.size());
					LogPrint(LOG_DEBUG, "nPartnerId: %d\n", Info->nPartnerId);

					_fireNextEvent(Info->parentClient, 0);
				}
				else {
					nEndOfProcess = 0;
				}
			}
			else if (msgtype == PP_METHOD_NOTIFY)
			{
				nEndOfProcess = recvNOTIFY(Info, bson);
			}
			else if (msgtype == PP_METHOD_BYE)
			{
				nEndOfProcess = recvBYE(Info, bson);
			}
			else
			{
				LogPrint(LOG_CRITICAL, " I don't know : %s\n", msgtype.c_str());
			}

			delete[] buf;

			if (nEndOfProcess < 1) {
				if (nEndOfProcess > -2)
				{
					sendBYE(Info);
				}
				LogPrint(LOG_DEBUG, "EndOfProcess partnerid : %d, peerid : %d\n", Info->nPartnerId, Info->nPeerId);
				break;
			}
		}

		LogPrint(LOG_DEBUG, "ProcessPeer while partnerid : %d, peerid : %d\n", Info->nPartnerId, Info->nPeerId);
	}
}

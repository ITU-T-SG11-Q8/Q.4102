#include <string.h>
#include "overlayAction.h"

#include "bson/bsonobjbuilder.h"
#include "bson/json.h"
#include "bson/bsonobjiterator.h"
#include "HttpREST.h"
#include "Protocol/JsonKey.h"
#include "Protocol/Peer.h"
#include <list>
#include "Util.h"

using namespace std;
using namespace _bson;

int _strCropperByStr(char* inputString, char* outputString, char* prefix, char* postfix, int outputlen)
{
	char* f_idx;
	char* b_idx;
	int len;

	if (outputlen < 1 || strlen_s(inputString) == 0)
	{
		return -1;
	}

	memset(outputString, 0x00, outputlen);

	if ((f_idx = (char *)strstr(inputString, prefix)) == NULL)
	{
		return 0;
	}

	if (strcmp(prefix, "") == 0)
	{
		f_idx = inputString; /* Prefix가 ""이라면 문자열의 시작부터 */
	}
	else
	{
		f_idx = f_idx + strlen_s(prefix); /* Prefix가 문자열일경우 Prefix가 끝나는 곳부터 */
	}

	if ((b_idx = (char *)strstr(f_idx, postfix)) == NULL)
	{
		return 0;
	}

	if (strcmp(postfix, "") == 0)
	{
		b_idx = inputString + strlen_s(inputString); /* Postfix가 ""이라면 문자열의 끝까지 */
	}

	len = b_idx - f_idx;

	if (len > outputlen - 1)
	{
		return -1;
	}

	strncpy(outputString, f_idx, len);

	return len;
}
/*
int overlayAction_CreateOverlayNetwork(const char* strPAID, char* strOsIP, unsigned int nOsPort, char* strOsPath, const char* strOverlayID, char* strAgentIP, unsigned int nAgentPort, unsigned int nMaxServerConn)
{
	int ret;
	char strQuery[1024] = XML_HEAD;

	// prep-overlay Start
	{
		char tmp[256];
		sprintf(tmp, "<prep-overlay id='%s'>\r\n", strOverlayID);
		strcat(strQuery, tmp);
	}

	// prep-node Info Start
	{
		char tmp[256];
		sprintf(tmp, "<prep-node id='%s'>\r\n", strPAID);
		strcat(strQuery, tmp);
	}

	// node-network-info 
	{
		char tmp[256];
		sprintf(tmp, "<node-network-info ip='%s' port='%d' maxServerConn='%d' curServerConn='0'/>\r\n", strAgentIP, nAgentPort, nMaxServerConn);
		strcat(strQuery, tmp);
	}

	// prep-node Info End
	{
		char tmp[256];
		sprintf(tmp, "</prep-node>\r\n");
		strcat(strQuery, tmp);
	}

	// prep-overlay End
	{
		char tmp[256];
		sprintf(tmp, "</prep-overlay>\r\n");
		strcat(strQuery, tmp);
	}

	// tail
	{
		char tmp[256];
		sprintf(tmp, XML_TAIL);
		strcat(strQuery, tmp);
	}

	//  test-jay
	//puts("---<< Query String >>--");
	//puts(strQuery);

	//HTTP_Startup();

	ret=HTTP_TrackerPUT(strOsIP, nOsPort, strOsPath, strQuery, strlen(strQuery));

	//HTTP_Cleanup();

	return ret;
}

int overlayAction_DeleteOverlayNetwork(char* strPAID, char* strOsIP, unsigned int nOsPort, char* strOsPath, char* strOverlayID, char* strAgentIP, unsigned int nAgentPort)
{
	int ret;
	char strQuery[1024] = XML_HEAD;

	// prep-overlay Start
	{
		char tmp[256];
		sprintf(tmp, "<prep-overlay id='%s'>\r\n", strOverlayID);
		strcat(strQuery, tmp);
	}

	// prep-node Info Start
	{
		char tmp[256];
		sprintf(tmp, "<prep-node id='%s'>\r\n", strPAID);
		strcat(strQuery, tmp);
	}

	// node-network-info 
	if (strlen(strAgentIP) && nAgentPort > 0)
	{
		char tmp[256];
		sprintf(tmp, "<node-network-info ip='%s' port='%d'/>\r\n", strAgentIP, nAgentPort);
		strcat(strQuery, tmp);
	}

	// prep-node Info End
	{
		char tmp[256];
		sprintf(tmp, "</prep-node>\r\n");
		strcat(strQuery, tmp);
	}

	// prep-overlay End
	{
		char tmp[256];
		sprintf(tmp, "</prep-overlay>\r\n");
		strcat(strQuery, tmp);
	}

	// tail
	{
		char tmp[256];
		sprintf(tmp, XML_TAIL);
		strcat(strQuery, tmp);
	}

	//  test-jay
	//puts("---<< Query String >>--");
	//puts(strQuery);

	//HTTP_Startup();

	ret=HTTP_TrackerDELETE(strOsIP, nOsPort, strOsPath, strQuery, strlen(strQuery));

	//HTTP_Cleanup();

	return ret;
}*/

OverlayItem_t ** overlayAction_RetrieveOverlayNetwork(char* strOverlayID, char* strOsIP, unsigned int nOsPort, char* strOsPath, int* nCount, char* strMyPAID)
{
	string url = "http://";
	url.append(strOsIP);
	url.append(":");
	url.append(to_string(nOsPort));
	url.append(strOsPath);
	url.append("/");
	url.append(strOverlayID);
	url.append("/peer");

	int resCode = 0;
	string rslt = HttpREST::Get(url, "", &resCode);

	if (resCode == HTTP_SUCCESS)
	{
		bsonobjbuilder b;
		stringstream st(rslt);
		bsonobj rsltjson = fromjson(st, b);

		bsonobj plist = rsltjson[JSON_KEY_PEERLIST].object();

		bsonobjiterator bit(plist);

		list<Peer> peers;

		while (1)
		{
			bsonelement e = bit.next(true);

			if (e.eoo()) break;

			bsonobj eobj = e.object();
			bsonobj peerobj = eobj[JSON_KEY_PEER].object();

			Peer peer;
			peer.PeerID = peerobj[JSON_KEY_PEER_ID].String();

			bsonobj netobj = peerobj[JSON_KEY_NETWORK].object();
			peer.IpAddress = netobj[JSON_KEY_IP_ADDRESS].String();
			peer.Port = netobj[JSON_KEY_PORT].Int();
			peer.IsPublic = netobj[JSON_KEY_PUBLIC].boolean();

			peers.push_back(peer);
		}

		*nCount = peers.size();

		OverlayItem_t **overlayItemList = (OverlayItem_t **)malloc(sizeof(OverlayItem_t *) * *nCount);

		int idx = 0;

		for (auto it = peers.begin(); it != peers.end(); ++it)
		{
			overlayItemList[idx] = (OverlayItem_t *)malloc(sizeof(OverlayItem_t));
			memset(overlayItemList[idx], 0, sizeof(OverlayItem_t));

			overlayItemList[idx]->nAgentPort = (*it).Port;
			overlayItemList[idx]->strAgentIP = _strdup((*it).IpAddress.c_str());
			overlayItemList[idx]->strPAID = _strdup((*it).PeerID.c_str());

			idx++;
		}

		return overlayItemList;
	}
	else
	{
		*nCount = -1;
		return NULL;
	}

	/*int ret, idx = 0;
	char *response;

	XMLDocument_t *XMLDocument=NULL;
	//XMLNamedNodeMap_t *XMLNamedNodeMap;
	XMLNodeList_t *XMLNodeList;

	OverlayItem_t **overlayItemList;

	char strQuery[512] = XML_HEAD;

	// OVERLAY_NETWORK_ID
	{
		char tmp[256];
		sprintf(tmp, "<prep-overlay id='%s'>\r\n", strOverlayID);
		strcat(strQuery, tmp);
	}

	// PROVIDER_ID
	if (strMyPAID != NULL && strlen(strMyPAID) > 0)
	{
		char tmp[256];
		sprintf(tmp, "<prep-node id='%s'/>\r\n", strMyPAID);
		strcat(strQuery, tmp);
	}

	// prep-overlay End
	{
		char tmp[256];
		sprintf(tmp, "</prep-overlay>\r\n");
		strcat(strQuery, tmp);
	}

	// tail
	{
		char tmp[256];
		sprintf(tmp, XML_TAIL);
		strcat(strQuery, tmp);
	}

	//puts("---<< Query String >>--");
	//puts(strQuery);

	//HTTP_Startup();

	ret=HTTP_GET(&response, strOsIP, nOsPort, strOsPath, strQuery, strlen(strQuery));

	//HTTP_Cleanup();

	if (ret <= 0)
	{
		*nCount = -1;
		return NULL;
	}
	
	*nCount = GetOverlayItemCountInXml(response, &XMLDocument, XML_PREP_OVERLAY);

	free(response);

	if (nCount <= 0)
	{
		FreeXMLDocument(XMLDocument);

		return NULL;
	}

	overlayItemList = (OverlayItem_t **)malloc(sizeof(OverlayItem_t *) * *nCount);

	if(XMLDocument->element!=(XMLNode_t *)0)
	{
		if(XMLDocument->element->NodeName!=(char *)0)
		{
			if(strcmp(XMLDocument->element->NodeName, XML_PREP_SERVICE))
			{
				FreeXMLDocument(XMLDocument);

				return NULL;
			}
			else
			{
				XMLNodeList=XMLDocument->element->ChildNodes;
			}
		}
	}

	idx = 0;
	while(XMLNodeList!=(XMLNodeList_t *)0)
	{
		if(!strncmp(XMLNodeList->XMLNode->NodeName, XML_PREP_OVERLAY, strlen(XML_PREP_OVERLAY)))
		{
			*(overlayItemList+(idx++)) = GetOverlayItemInXml(XMLNodeList->XMLNode);
		}

		XMLNodeList=XMLNodeList->next;
	}	

	FreeXMLDocument(XMLDocument);
	
	return overlayItemList;*/
}

OverlayItem_t ** overlayAction_RetrievePODOOverlayNetwork(char* strOverlayID, char* strOsIP, unsigned int nOsPort, char* strOsPath, int* nCount, char* strMyPAID)
{
	int ret, idx = 0, out = 0, tmpCnt = 0;
	char *response;
	char* chidx;
	
	OverlayItem_t **overlayItemList = NULL;
	char strQuery[512] = {'\0'};
	char strOut[512] = {'\0'};
	char strID[50] = {'\0'};
	char strIP[20] = {'\0'};
	char strPort[10] = {'\0'};
	char strVersion[10] = {'\0'};
		
	sprintf_s(strQuery, "%s%s%s", strOsPath, "/", strOverlayID);

	ret=HTTP_GET(&response, strOsIP, nOsPort, strQuery, "", 0);

	//HTTP_Cleanup();

	if (ret <= 0)
	{
		*nCount = -1;
		return NULL;
	}

	//*nCount = 0;
	tmpCnt = 0;

	while(1)
	{
		out = _strCropperByStr(response + idx, strOut, "{", "}", 512);
		if(out <= 0)
			break;

		idx += out;

		chidx = strstr(strOut, "\"ip\":\"");

		if (chidx == NULL) continue;

		chidx = strstr(strOut, "\"peerId\":\"");

		if (chidx == NULL) continue;

		out = _strCropperByStr(chidx + 8, strID, "\"", "\"", 50);

		if(out <= 0) continue;

		chidx = strstr(strOut, "\"ip\":\"");

		if (chidx == NULL) continue;

		out = _strCropperByStr(chidx + 4, strIP, "\"", "\"", 20);

		if(out <= 0) continue;

		chidx = strstr(strOut, "\"port\":");

		if (chidx == NULL) continue;

		out = _strCropperByStr(chidx + 5, strPort, ":", ",", 10);

		if(out <= 0)
		{
			out = _strCropperByStr(chidx + 5, strPort, ":", "}", 10);

			if(out <= 0) continue;
		}

		chidx = strstr(strOut, "\"version\":");

		if (chidx == NULL) continue;

		out = _strCropperByStr(chidx + 8, strVersion, ":", ",", 10);

		if(out <= 0)
		{
			out = _strCropperByStr(chidx + 8, strVersion, ":", "}", 10);

			if(out <= 0) continue;
		}

		tmpCnt++;

		if (overlayItemList == NULL)
		{
			overlayItemList = (OverlayItem_t **)malloc(sizeof(OverlayItem_t *) * tmpCnt);
		}
		else
		{
			overlayItemList = (OverlayItem_t **)realloc(overlayItemList, sizeof(OverlayItem_t *) * tmpCnt);
		}

		overlayItemList[tmpCnt - 1] = (OverlayItem_t *)malloc(sizeof(OverlayItem_t));
		memset(overlayItemList[tmpCnt - 1], 0, sizeof(OverlayItem_t));

		overlayItemList[tmpCnt - 1]->strPAID = GetStringValue(strID);
		overlayItemList[tmpCnt - 1]->strOverlayID = GetStringValue(strOverlayID);
		overlayItemList[tmpCnt - 1]->nAgentPort = atoi(strPort);
		overlayItemList[tmpCnt - 1]->strAgentIP = GetStringValue(strIP);
		overlayItemList[tmpCnt - 1]->nActiveTime = atoi(strVersion);
	}

	free(response);
	*nCount = tmpCnt;
	
	return overlayItemList;
}

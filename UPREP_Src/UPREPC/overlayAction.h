#ifndef __OVERLAYACTION_H
#define __OVERLAYACTION_H

//#define OVERLAY_URL_PATH "/services/prep/overlay"

#include <stdio.h>
#include <stdlib.h>
#include "commonDefine.h"
#include "NetworkUtil.h"

//int overlayAction_CreateOverlayNetwork(const char* strPAID, char* strOsIP, unsigned int nOsPort, char* strOsPath, const char* strOverlayID, char* strAgentIP, unsigned int nAgentPort, unsigned int nMaxServerConn);
//int overlayAction_DeleteOverlayNetwork(char* strPAID, char* strOsIP, unsigned int nOsPort, char* strOsPath, char* strOverlayID, char* strAgentIP, unsigned int nAgentPort);
OverlayItem_t ** overlayAction_RetrieveOverlayNetwork(char* strOverlayID, char* strOsIP, unsigned int nOsPort, char* strOsPath, int* nCount, char* strMyPAID);
//int GetOverlayItemCountInXml(char* response, void **XMLDocument, char* strNodeName);
//OverlayItem_t * GetOverlayItemInXml(void* xmlNode);

OverlayItem_t ** overlayAction_RetrievePODOOverlayNetwork(char* strOverlayID, char* strOsIP, unsigned int nOsPort, char* strOsPath, int* nCount, char* strMyPAID);
#endif
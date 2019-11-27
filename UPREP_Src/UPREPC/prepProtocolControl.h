#ifndef __PREP_PROTOCOL_CONTROL_H__
#define __PREP_PROTOCOL_CONTROL_H__

#include "prepBuffer.h"
#include "PODOBuffer.h"
#include "prepProtocol.h"
#include "commonStruct.h"
#include "bson/bsonobjbuilder.h"
#include "bson/json.h"

using namespace _bson;

int recvHELLO(PeerInfo_t * Info, bsonobj& bson);
int sendHELLO(PeerInfo_t * Info, double starttime);

int recvPELLO(PeerInfo_t * Info, bsonobj& bson);
int sendPELLO(PeerInfo_t * Info);
 
int recvGET(PeerInfo_t * Info, bsonobj& bson);
int sendGET(PeerInfo_t * Info, unsigned int piece_index);

int recvDATA(PeerInfo_t * Info, bsonobj& bson);
int sendDATA(PeerInfo_t * Info, int piece_index);

int recvBUSY(PeerInfo_t * Info, bsonobj& bson);
int sendBUSY(PeerInfo_t * Info);

int recvDATACANCEL(PeerInfo_t * Info, bsonobj& bson);
int sendDATACANCEL(PeerInfo_t * Info, unsigned int piece_index, unsigned int reason);

int recvREFRESH(PeerInfo_t * Info, bsonobj& bson);
int sendREFRESH(PeerInfo_t * Info, unsigned int piece_index);

int recvBUFFERMAP(PeerInfo_t * Info, bsonobj& bson);
int sendBUFFERMAP(PeerInfo_t * Info, unsigned int piece_index, unsigned int number) ;

int recvBYE(PeerInfo_t * Info, bsonobj& bson);
int sendBYE(PeerInfo_t * Info);
//int sendBYEToSOCKET(SOCKET sock);

int recvPARTNER(PeerInfo_t * Info, bsonobj& bson);
int sendPARTNER(PeerInfo_t * Info, unsigned int starting_piece_index);

int recvRESULT(PeerInfo_t * Info, bsonobj& bson);
int sendRESULT(PeerInfo_t * Info, unsigned int result);

int recvNOTIFY(PeerInfo_t * Info, bsonobj& bson);
int sendNOTIFY(PeerInfo_t * Info, SOCKET socket, unsigned int piece_index);

//typedef void (__stdcall *PrepDelegate)(char* key, char* overlayId, char* peerId, char* remotePeerId, unsigned int pieceId, unsigned int pieceSize);

//void PrepProtocol_SetCallback(PrepDelegate pd);

#endif
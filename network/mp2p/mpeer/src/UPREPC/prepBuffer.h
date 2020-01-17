#ifndef __PREPBUFFER_H
#define __PREPBUFFER_H

#include <stdlib.h>
#include <string.h>

#include "prepProtocol.h"

#ifdef WIN32
#include "Util/pthreadWin32/include/pthread.h"
#include <unordered_map>
#else
#include <pthread.h>
#ifdef MACOS
#include <unordered_map>
#else
#include <tr1/unordered_map>
using namespace std::tr1;
#endif

#endif

//using namespace std;

#define PIECE_STATUS_EMPTY 				0
#define PIECE_STATUS_COMPLETED 			1
#define PIECE_STATUS_DOWNLOADING 		2
#define PIECE_STATUS_RESERVED		 	3
#define PIECE_STATUS_ERROR		 		4
#define PIECE_STATUS_OUTOFDS	 		5

typedef struct _PrepBuffer_t
{
	char *key;

	int SP;
	int PP;
	int CP;
	int DP;
	int EP;
	int StartDP;

	unsigned int ES;

	unsigned int nPieceSize;

	unsigned int nBufferSize;
	unsigned char *buffer;

	unsigned int nBufferMapSize;

	unsigned char *downloadMap;
	unsigned int nDownloadWindowSize;
	unsigned short nSpStartPercent;
		
	unsigned int mStart;
	unsigned int mScraps;

	int nOutFile;

	pthread_mutex_t  bufMutex;

	unsigned int nDownloadFlag;

	long lAddedTime;
	long lCompleteTime;
#if defined(WIN32) || defined(MACOS)
	std::unordered_map<int, double> *TimestampMap;
#else
	unordered_map<int, double> *TimestampMap;
#endif
} PrepBuffer_t;


void prepBuffer_initBufferArray(unsigned int bufCnt);
PrepBuffer_t *PrepBuffer_getBufferByKey(char* key);

int prepBuffer_newBuffer(const char* key, unsigned int bufferSize, unsigned int pieceSize, unsigned int esSize, unsigned int downloadWindowSize, int outfile, unsigned short spStartPercent);

void prepBuffer_freeBufferByKey(char* key);
void prepBuffer_freeBufferArray();

void prepBuffer_setRecordData(char* key, char* data, unsigned int len);

int prepBuffer_setPieceData(char* key, unsigned int pieceNum, char* pieceData);
int prepBuffer_setPieceDataTimestamp(char* key, unsigned int pieceNum, double timestamp);
double prepBuffer_getPieceDataTimestampInterval(char* key);
int prepBuffer_removePieceDataTimestamp(char* key, unsigned int pieceNum, int lock);
//int prepBuffer_popPieceData(char* key, char* pieceData);
int prepBuffer_getPieceData(char* key, int pieceNum, char* pieceData);
double prepBuffer_getPieceDataTimestamp(char* key, unsigned int pieceNum);
int prepBuffer_getPieceIndex4Timestamp(char* key, double time, int& lastIndex);
char* prepBuffer_getPlayData(char* key, unsigned int errorPass);
int prepBuffer_isPlayable(char* key);

int prepBuffer_getBufferArrayIndex(PrepBuffer_t * buf);

char* prepBuffer_getDownloadMap(char* key);
int   prepBuffer_getDownloadMap4HELLO(char* key, ProtocolHello_t *hello, double starttime);
int   prepBuffer_getDownloadMap4BUFFERMAP(char* key, ProtocolBuffermap_t *buffermap, unsigned int startPieceIndex, unsigned int number);

int prepBuffer_setDownloadMapStatusByKey(char* key, unsigned int pieceNum, int status);
int prepBuffer_getDownloadMapStatusByKey(char* key, unsigned int pieceNum);

int prepBuffer_refreshDownloadMap(char *key, unsigned int sp_index, unsigned int complete_length, unsigned int dp_index, unsigned int ds_length, unsigned char *download_map);

int prepBuffer_getPieceIndex4Download(char *key, unsigned int sp_index, unsigned int complete_length, unsigned int dp_index, unsigned int ds_length, unsigned char *download_map);

int prepBuffer_getCurrentSP(char* key);
int prepBuffer_getCurrentDP(char* key);
int prepBuffer_getCurrentPP(char* key);
void prepBuffer_setCurrentPP(char* key, unsigned int pp);
int prepBuffer_getCurrentCP(char* key);
int prepBuffer_getCurrentCS(char* key);
void prepBuffer_getCurrentBufferStatus(char* key, int& sp, int& pp, int& cp, int& cs, int& dp);

//typedef void (__stdcall *PrepDelegate)(char* key, char* overlayId, char* peerId, char* remotePeerId, unsigned int pieceId, unsigned int pieceSize);

//void prepBuffer_SetCallback(PrepDelegate pd);

//void prepBuffer_addUploadBytes(char* key, int bytes);

#endif
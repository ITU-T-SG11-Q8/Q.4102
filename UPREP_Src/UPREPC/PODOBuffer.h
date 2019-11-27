#ifndef __PODOBUFFER_H
#define __PODOBUFFER_H

#include <stdlib.h>
#include <string.h>

#include "prepProtocol.h"

#ifdef WIN32
#include "Util/pthreadWin32/include/pthread.h"
#else
#include <pthread.h>
#endif

#define PIECE_STATUS_EMPTY 				0
#define PIECE_STATUS_COMPLETED 			1
#define PIECE_STATUS_DOWNLOADING 		2
#define PIECE_STATUS_RESERVED		 	3
#define PIECE_STATUS_ERROR		 		4
#define PIECE_STATUS_OUTOFDS	 		5

typedef struct _FileInfo_t
{
	char *fileName;
	char *rootDir;

	FILE *pFile;

	pthread_mutex_t  fileMutex;

	double nFileSize;
	double nDownSize;

	unsigned int nPieceStart;
	unsigned int nPieceEnd;

	unsigned int nIsComplete;
} FileInfo_t;

typedef struct _PODOBuffer_t
{
	char *key;

	FileInfo_t **pFileInfos;

	unsigned int nFileCount;

	unsigned int nPieceSize;

	unsigned char *downloadMap;
	unsigned int nDownloadMapSize;
		
	pthread_mutex_t  bufMutex;

	unsigned int nDownloadFlag;

	char *downDir;
	char *completeDir;

	unsigned int nVersion;
	int isServer;

	long lAddedTime;
	long lCompleteTime;

	double dTotalBytes;
} PODOBuffer_t;

void PODOBuffer_initBufferArray(unsigned int bufCnt);

PODOBuffer_t *PODOBuffer_getPODOBufferByKey(char* key);

int PODOBuffer_newBuffer(char* key, unsigned int pieceSize, unsigned int fileCount, FileInfo_t** fileInfos, int totalPieceCount, char* downDir, char* completeDir, int nVersion, int nIsServer);
int PODOBuffer_updateBuffer(char* key, unsigned int fileCount, FileInfo_t** fileInfos, int totalPieceCount, int nVersion);

void PODOBuffer_freeBufferByKey(char* key, int removeData);
void PODOBuffer_freeBufferArray();

//void PODOBuffer_setRecordData(char* key, char* data, unsigned int len);

int PODOBuffer_setPieceData(char* key, unsigned int pieceNum, char* pieceData);
//int PODOBuffer_popPieceData(char* key, char* pieceData);
int PODOBuffer_getPieceData(char* key, unsigned int pieceNum, char* pieceData);
//char* PODOBuffer_getPlayData(char* key, unsigned int errorPass);
//int PODOBuffer_isPlayable(char* key);

int PODOBuffer_getBufferArrayIndex(PODOBuffer_t * buf);

char* PODOBuffer_getDownloadMap(char* key);
int   PODOBuffer_getDownloadMap4HELLO(char* key, ProtocolHello_t *hello);
int   PODOBuffer_getDownloadMap4BUFFERMAP(char* key, ProtocolBuffermap_t *buffermap, unsigned int startPieceIndex, unsigned int number);

int PODOBuffer_setDownloadMapStatusByKey(char* key, unsigned int pieceNum, int status);
int PODOBuffer_getDownloadMapStatusByKey(char* key, unsigned int pieceNum);

int PODOBuffer_refreshDownloadMap(char *key, unsigned int sp_index, unsigned int complete_length, unsigned int dp_index, unsigned int ds_length, unsigned char *download_map);

int PODOBuffer_getPieceIndex4Download(char *key, unsigned int sp_index, unsigned int complete_length, unsigned int dp_index, unsigned int ds_length, unsigned char *download_map);

int PODOBuffer_getCurrentDP(char* key);

int PODOBuffer_isValidVersion(char* key, unsigned int version);

int PODOBuffer_isPODOComplete(char *key, int lock);

int PODOBuffer_removeDownFile(char *key);

//void PODOBuffer_addUploadBytes(char* key, int bytes);
FileInfo_t** PODOBuffer_GetFileInfos(char* key, int* cnt);

//typedef void (__stdcall *PrepDelegate)(char* key, char* overlayId, char* peerId, char* remotePeerId, unsigned int pieceId, unsigned int pieceSize);

//void PODOBuffer_SetCallback(PrepDelegate pd);

#endif
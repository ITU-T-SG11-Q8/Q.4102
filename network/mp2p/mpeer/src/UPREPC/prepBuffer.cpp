#ifdef WIN32
#define _CRTDBG_MAP_ALLOC
#include "crtdbg.h"
#else
#define NULL 0
#endif
#include <stdio.h>
#include <string.h>
#include "prepBuffer.h"
#include "commonDefine.h"
#include "NetworkUtil.h"
#include "Util.h"

PrepBuffer_t **gPrepBufferArray;
static unsigned int gnMaxBufferCount = 0;
static unsigned int gnCurrentBufferCount = 0;

//static PrepDelegate PrepProgress;

//////////////////////////////////////////////////////////////////////////
// private method

PrepBuffer_t *_getBufferByKey(char* key)
{
	unsigned int i=0;

	if (gPrepBufferArray == NULL) return NULL;

	for (i=0; i<gnMaxBufferCount; i++)
	{
		if (gPrepBufferArray[i] != NULL && gPrepBufferArray[i]->key != NULL)
		{
			if (!strcmp(gPrepBufferArray[i]->key, key))
			{
				return gPrepBufferArray[i];
			}
		}
	}

	return NULL;
}

PrepBuffer_t *PrepBuffer_getBufferByKey(char* key)
{
	return _getBufferByKey(key);
}

void _writeBuffer(PrepBuffer_t * pBuf, void *data, int size)
{
	if (pBuf->nBufferSize < pBuf->mStart + size)
	{
		int fin = 0, remainder = 0;
		fin = pBuf->nBufferSize - pBuf->mStart;
		remainder = size - fin;

		cpymem(pBuf->buffer + pBuf->mStart, data, fin);
		cpymem(pBuf->buffer, (char*)data + fin, remainder);

		pBuf->mStart = remainder;
	}
	else
	{
		cpymem(pBuf->buffer + pBuf->mStart, data, size);
		pBuf->mStart += size;
	}

	/////////////////////////////////////////////////////////////////////
	/*FILE *fp = fopen("11111.mp4", "ab");

	if (fp == NULL)
	{
		LogPrint(LOG_CRITICAL, "111111Outfile open error!!\n");
	}

	int fr = fwrite(data, 1, size, fp);

	if (fr < 0)
	{
		LogPrint(LOG_CRITICAL, "111111Outfile write error\n");
	}
	fclose(fp);*/
	/////////////////////////////////////////////////////////////////////
}

void _addPieceForRecord(PrepBuffer_t *pBuf, int pieceCnt)
{
	pBuf->DP += pieceCnt;// + (pBuf->DP == 0 ? 1 : 0);

	pBuf->EP = pBuf->DP;

	for (int i = 1; i <= pieceCnt; i++)
	{
		int idx = pBuf->DP - i;
		
		//auto ggg = pBuf->TimestampMap->find(idx);

		if (pBuf->TimestampMap->find(idx) == pBuf->TimestampMap->end())
		{
			(*pBuf->TimestampMap)[idx] = GetNTPTimestamp();
		}
	}

	if (pBuf->EP + pBuf->ES > pBuf->nBufferMapSize)
	{
		pBuf->SP = (pBuf->EP + pBuf->ES) - pBuf->nBufferMapSize;
	}

	pBuf->nDownloadWindowSize = 0;

	//LogPrint(LOG_DEBUG, "---------------------------SP : %d, DP : %d ---------------------------\n", pBuf->SP, pBuf->DP);
}

int _getDownloadMapStatus(PrepBuffer_t* pBuf, unsigned int pieceNum)
{
	int rslt = PIECE_STATUS_OUTOFDS;

	if (pBuf == NULL) return rslt;

	if (pBuf->downloadMap == NULL)
	{
		return rslt;
	}

	if (pieceNum >= pBuf->EP || pieceNum < pBuf->DP)
	{
		return rslt;
	}

	if (pieceNum - pBuf->DP >= pBuf->nDownloadWindowSize)
	{
		return rslt;
	}

	rslt = pBuf->downloadMap[pieceNum - pBuf->DP];

	return rslt;
}

void _freeBuffer(PrepBuffer_t* buffer)
{
	int bufidx = -1;

	if (buffer != NULL)
	{
		if (buffer->key != NULL && strlen_s(buffer->key))
		{
			free(buffer->key);
			buffer->key = NULL;
		}

		if (buffer->buffer != NULL)
		{
			free(buffer->buffer);
			buffer->buffer = NULL;
		}

		if (buffer->downloadMap != NULL)
		{
			free(buffer->downloadMap);
			buffer->downloadMap = NULL;
		}

		if (buffer->TimestampMap != NULL)
		{
			buffer->TimestampMap->clear();
			delete buffer->TimestampMap;
		}

		//if (buffer->bufMutex != NULL)
		{
			pthread_mutex_destroy(&buffer->bufMutex);
			//buffer->bufMutex = NULL;
		}

		bufidx = prepBuffer_getBufferArrayIndex(buffer);

		if (bufidx >= 0)
		{
			free(gPrepBufferArray[bufidx]);
			gPrepBufferArray[bufidx] = NULL;
			buffer = NULL;
		}
		else
		{
			free(buffer);
			buffer = NULL;
		}

		gnCurrentBufferCount--;
	}
}

void _shiftDownloadSection(PrepBuffer_t * pBuf, int shift)
{
	if (shift <= 0)
	{
		return;
	}
	else
	{
		unsigned char *tmpmap = (unsigned char *)malloc(pBuf->nDownloadWindowSize);
		memset(tmpmap, 0, pBuf->nDownloadWindowSize);
		cpymem(tmpmap, pBuf->downloadMap + shift, pBuf->nDownloadWindowSize - shift);
		free(pBuf->downloadMap);
		pBuf->downloadMap = tmpmap;

		pBuf->DP += shift;
		pBuf->EP = pBuf->DP + pBuf->nDownloadWindowSize;

		if (pBuf->EP + pBuf->ES > pBuf->nBufferMapSize)
		{
			if (pBuf->SP < (pBuf->EP + pBuf->ES) - pBuf->nBufferMapSize)
			{
				unsigned int tmpsp = (pBuf->EP + pBuf->ES) - pBuf->nBufferMapSize;

				for (unsigned int i = pBuf->SP; i < tmpsp; i++)
				{
					prepBuffer_removePieceDataTimestamp(pBuf->key, i, 0);
				}

				pBuf->SP = tmpsp;
			}			
		}
	}
}

//////////////////////////////////////////////////////////////////////////

void prepBuffer_initBufferArray(unsigned int bufCnt)
{
	gPrepBufferArray = (PrepBuffer_t **)malloc(sizeof(PrepBuffer_t *) * bufCnt);
	memset(gPrepBufferArray, 0, sizeof(PrepBuffer_t *) * bufCnt);
	gnMaxBufferCount = bufCnt;
	gnCurrentBufferCount = 0;
}

int prepBuffer_newBuffer(const char* key, unsigned int bufferSize, unsigned int pieceSize, unsigned int esSize, unsigned int downloadWindowSize, int outfile, unsigned short spStartPercent)
{
	unsigned int i = 0;
	PrepBuffer_t *buf = NULL;
	
	if (gnMaxBufferCount <= gnCurrentBufferCount)
	{
		return FAIL;
	}
	
	buf = (PrepBuffer_t *)malloc(sizeof(PrepBuffer_t));
	if (buf == NULL)
	{
		return FAIL;
	}
	memset(buf,0, sizeof(PrepBuffer_t));
		
	buf->key = _strdup(key);
#if defined(WIN32) || defined(MACOS)
	buf->TimestampMap = new std::unordered_map<int, double>();
#else
	buf->TimestampMap = new unordered_map<int, double>();
#endif
	
	buf->buffer = (unsigned char *)malloc(bufferSize * pieceSize);
	if (buf->buffer == NULL)
	{
		free(buf);
		return FAIL;
	}
	memset(buf->buffer, 0, bufferSize * pieceSize);
	buf->SP = -1;
	buf->nBufferSize = bufferSize * pieceSize;
	buf->nPieceSize = pieceSize;
	buf->nBufferMapSize = bufferSize;
	buf->ES = esSize;
	buf->nDownloadWindowSize = downloadWindowSize;
	buf->nOutFile = outfile;
	buf->nSpStartPercent = spStartPercent;
	
	for(i=0; i<gnMaxBufferCount; i++)
	{
		if (gPrepBufferArray[i] == NULL)
		{
			gPrepBufferArray[i] = buf;
			break;
		}
	}
	
	pthread_mutex_init(&buf->bufMutex, NULL);
	
	gnCurrentBufferCount++;
	
	buf->lAddedTime = (long)time(NULL);

	return SUCCESS;
}

void prepBuffer_freeBufferByKey(char* key)
{
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return;

	if (key == NULL || !strlen_s(key))
		return;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return;

	_freeBuffer(pBuf);
}

int prepBuffer_getBufferArrayIndex(PrepBuffer_t * buf)
{
	unsigned int i=0;
	if (gPrepBufferArray != NULL)
	{
		for (i=0; i<gnMaxBufferCount; i++)
		{
			if (gPrepBufferArray[i] == buf)
			{
				return i;
			}
		}
	}

	return -1;
}


void prepBuffer_freeBufferArray()
{
	unsigned int i=0;
	if (gPrepBufferArray != NULL)
	{
		for (i=0; i<gnMaxBufferCount; i++)
		{
			_freeBuffer(gPrepBufferArray[i]);
		}
	}

	free(gPrepBufferArray);
	gPrepBufferArray = NULL;

	gnCurrentBufferCount = 0;
}

void prepBuffer_setRecordData(char* key, char* data, unsigned int len)
{
	int pieceCnt = 0/*, remainder = 0, nextPiece = 0*/;

	PrepBuffer_t *pBuf = NULL;
	
	if (gPrepBufferArray == NULL) return;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return;

	pthread_mutex_lock(&pBuf->bufMutex);

	_writeBuffer(pBuf, data, len);

	pieceCnt = len / pBuf->nPieceSize;

	if (pieceCnt > 0)
	{
		_addPieceForRecord(pBuf, pieceCnt);
	}
	else
	{
		if (pBuf->mScraps + len > pBuf->nPieceSize)
		{
			_addPieceForRecord(pBuf, 1);
			pBuf->mScraps = (pBuf->mScraps + len) - pBuf->nPieceSize;
		}
		else
		{
			pBuf->mScraps += len;
		}
	}

	pthread_mutex_unlock(&pBuf->bufMutex);
}

char * prepBuffer_getDownloadMap(char* key)
{
	PrepBuffer_t *pBuf = NULL;
	char *maptmp = NULL;
	
	if (gPrepBufferArray == NULL) return NULL;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return NULL;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->nDownloadWindowSize > 0 && pBuf->downloadMap != NULL)
	{
		maptmp = (char *)malloc(sizeof(char) * pBuf->nDownloadWindowSize);
		memset(maptmp, 0, sizeof(char) * pBuf->nDownloadWindowSize);

		cpymem(maptmp, pBuf->downloadMap, pBuf->nDownloadWindowSize);
	}

	pthread_mutex_unlock(&pBuf->bufMutex);

	return maptmp;
}

int prepBuffer_getDownloadMap4HELLO(char* key, ProtocolHello_t *hello, double starttime)
{
	PrepBuffer_t *pBuf = NULL;
	
	if (gPrepBufferArray == NULL) return FAIL;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return FAIL;

	pthread_mutex_lock(&pBuf->bufMutex);

	LogPrint(LOG_DEBUG, "!!! getDownloadMap4HELLO recv Timestamp : %.0lf\n", starttime);

	int sp = pBuf->SP >= 0 ? pBuf->SP : 0;

	hello->ds_length = 0;
	hello->sp_index = sp;
	hello->complete_length = pBuf->DP - sp;
	hello->dp_index = pBuf->DP;

	int find = 0;
	if (starttime > 0)
	{		
		for (int i = sp; i < pBuf->DP; i++)
		{
			auto it = pBuf->TimestampMap->find(i);

			if (it != pBuf->TimestampMap->end())
			{
				LogPrint(LOG_DEBUG, "!!! my piece : %d, Timestamp : %.0lf\n", i, it->second);
				if (it->second >= starttime)
				{
					LogPrint(LOG_DEBUG, "!!!!! find!!!\n");
					hello->sp_index = i;
					hello->complete_length = pBuf->DP - i;
					find = 1;
					break;
				}
			}
		}

		if (!find)
		{
			hello->sp_index = pBuf->DP;
			hello->complete_length = 0;
		}
	}
	else
	{
		find = 1;
	}

	if (pBuf->nDownloadWindowSize > 0 && pBuf->downloadMap != NULL && find)
	{
		hello->download_map = (unsigned char *)malloc(sizeof(unsigned char) * pBuf->nDownloadWindowSize);
		memset(hello->download_map, 0, sizeof(unsigned char) * pBuf->nDownloadWindowSize);

		cpymem(hello->download_map, pBuf->downloadMap, pBuf->nDownloadWindowSize);
		hello->ds_length = pBuf->nDownloadWindowSize;
	}
	
	pthread_mutex_unlock(&pBuf->bufMutex);

	return SUCCESS;
}

int prepBuffer_getDownloadMap4BUFFERMAP(char* key, ProtocolBuffermap_t *buffermap, unsigned int startPieceIndex, unsigned int number)
{
	unsigned int endPieceIndex = 0;
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return FAIL;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return FAIL;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (startPieceIndex >= pBuf->EP)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return FAIL;
	}

	if (startPieceIndex + number < pBuf->SP && number > 0 && startPieceIndex > 0)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return FAIL;
	}	
	
	buffermap->piece_index = startPieceIndex;

	if (buffermap->piece_index < pBuf->SP)
	{
		buffermap->piece_index = pBuf->SP;
	}

	if (number > 0)
	{
		endPieceIndex = startPieceIndex + number - 1;

		if (buffermap->piece_index >= pBuf->DP)
		{
			buffermap->complete_length = 0;
			buffermap->dp_index = buffermap->piece_index;
			buffermap->ds_length = endPieceIndex >= pBuf->EP ? pBuf->EP - buffermap->piece_index : number;
		}
		else
		{
			if (endPieceIndex < pBuf->DP)
			{
				buffermap->complete_length = number - (buffermap->piece_index - startPieceIndex);
				buffermap->dp_index = endPieceIndex + 1;
				buffermap->ds_length = 0;
			}
			else
			{
				buffermap->complete_length = pBuf->DP - buffermap->piece_index;
				buffermap->dp_index = pBuf->DP;
				buffermap->ds_length = number - buffermap->complete_length;

				if (buffermap->ds_length > pBuf->EP - pBuf->DP)
				{
					buffermap->ds_length = pBuf->EP - pBuf->DP;
				}
			}
		}
	}
	else
	{
		if (buffermap->piece_index >= pBuf->DP)
		{
			buffermap->complete_length = 0;
			buffermap->dp_index = buffermap->piece_index;
			buffermap->ds_length = pBuf->EP - buffermap->piece_index;
		}
		else
		{
			buffermap->complete_length = pBuf->DP - buffermap->piece_index;
			buffermap->dp_index = pBuf->DP;
			buffermap->ds_length = pBuf->EP - pBuf->DP;
		}
	}

	if (buffermap->ds_length > 0 && pBuf->downloadMap != NULL && pBuf->nDownloadWindowSize > 0)
	{
		buffermap->download_map = (unsigned char *)malloc(sizeof(unsigned char) * buffermap->ds_length);
		memset(buffermap->download_map, 0, sizeof(unsigned char) * buffermap->ds_length);

		cpymem(buffermap->download_map, pBuf->downloadMap + (buffermap->dp_index - pBuf->DP), buffermap->ds_length);
	}

	pthread_mutex_unlock(&pBuf->bufMutex);

	return SUCCESS;
}

int prepBuffer_setDownloadMapStatusByKey(char* key, unsigned int pieceNum, int status)
{
	PrepBuffer_t *pBuf = NULL;
	
	if (gPrepBufferArray == NULL) return FAIL;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return FAIL;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->downloadMap == NULL)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return FAIL;
	}

	if (pieceNum >= pBuf->EP || pieceNum < pBuf->DP)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return FAIL;
	}

	if (pieceNum - pBuf->DP >= pBuf->nDownloadWindowSize)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return FAIL;
	}

	pBuf->downloadMap[pieceNum - pBuf->DP] = status;

	pthread_mutex_unlock(&pBuf->bufMutex);

	return SUCCESS;
}

int prepBuffer_getDownloadMapStatusByKey(char* key, unsigned int pieceNum)
{
	int rslt = PIECE_STATUS_OUTOFDS;

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pieceNum >= pBuf->SP && pieceNum < pBuf->DP)
	{
		rslt = PIECE_STATUS_COMPLETED;
	}
	else
	{
		rslt = _getDownloadMapStatus(pBuf, pieceNum);
	}

	pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

int prepBuffer_setPieceDataTimestamp(char* key, unsigned int pieceNum, double timestamp)
{
	int rslt = FAIL;

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	rslt = SUCCESS;

	pthread_mutex_lock(&pBuf->bufMutex);

	auto it = pBuf->TimestampMap->find(pieceNum);

	if (it == pBuf->TimestampMap->end())
	{
		(*pBuf->TimestampMap)[pieceNum] = timestamp;
	}

	pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

double prepBuffer_getPieceDataTimestampInterval(char* key)
{
	double rslt = FAIL;

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	if (pBuf->TimestampMap->size() > 1)
	{
		pthread_mutex_lock(&pBuf->bufMutex);

		for (auto it = pBuf->TimestampMap->begin(); it != pBuf->TimestampMap->end(); ++it)
		{
			if (rslt == FAIL)
			{
				auto find = pBuf->TimestampMap->find(it->first + 1);
				if (find != pBuf->TimestampMap->end())
				{
					rslt = find->second - it->second;
					break;
				}
			}
			else
			{
				break;
			}
		}

		pthread_mutex_unlock(&pBuf->bufMutex);
	}

	return rslt;
}


int prepBuffer_removePieceDataTimestamp(char* key, unsigned int pieceNum, int lock = 1)
{
	int rslt = FAIL;

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	rslt = SUCCESS;

	if (lock) pthread_mutex_lock(&pBuf->bufMutex);

	if (pieceNum < 0)
	{
		pBuf->TimestampMap->clear();
	}
	else
	{
		auto it = pBuf->TimestampMap->find(pieceNum);

		if (it != pBuf->TimestampMap->end())
		{
			pBuf->TimestampMap->erase(pieceNum);
		}
	}

	if (lock) pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

int prepBuffer_setPieceData(char* key, unsigned int pieceNum, char* pieceData)
{
	int rslt = FAIL;
	//unsigned char *tmpMap = NULL;

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	LogPrint(LOG_DEBUG, "\t\t\tsetPieceData : %d\n", pieceNum);

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->downloadMap == NULL)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if (pieceNum >= pBuf->EP || pieceNum < pBuf->DP)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if (pieceNum - pBuf->DP >= pBuf->nDownloadWindowSize)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}
	LogPrint(LOG_DEBUG, "\t\t\tsetPieceData memcpy: %d\n", pieceNum);
	cpymem(pBuf->buffer + (((pieceNum/* - pBuf->SP*/) % pBuf->nBufferMapSize) * pBuf->nPieceSize), pieceData, pBuf->nPieceSize);
	LogPrint(LOG_DEBUG, "\t\t\tsetPieceData memcpy end: %d\n", pieceNum);

	pBuf->nDownloadFlag++;
	//DebugPrintInfo("nDownloadFlag : %d\n", pBuf->nDownloadFlag);

	pBuf->downloadMap[pieceNum - pBuf->DP] = PIECE_STATUS_COMPLETED;

// 	LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~Piece : %d ~~~~~~~~~~~~~~~\n", pieceNum);
// 	LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~SP    : %d ~~~~~~~~~~~~~~~\n", pBuf->SP);
// 	LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~PP    : %d ~~~~~~~~~~~~~~~\n", pBuf->PP);
// 	LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~DP    : %d ~~~~~~~~~~~~~~~\n", pBuf->DP);
// 	LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~DS    : %d ~~~~~~~~~~~~~~~\n", pBuf->nDownloadWindowSize);
// 	LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~EP    : %d ~~~~~~~~~~~~~~~\n", pBuf->EP);
	
	if (pBuf->nOutFile > 0)
	{
		FILE *fp = fopen(key, "r+b");

		if (fp == NULL)
		{
			fp = fopen(key, "w+b");

			if (fp == NULL)
			{
				LogPrint(LOG_CRITICAL, "Outfile open error!!\n");
			}
		}

		int idx = pieceNum - pBuf->StartDP;

		if (pBuf->StartDP < 0)
		{
			idx = pieceNum + pBuf->StartDP;
		}

		fseek(fp, (idx * pBuf->nPieceSize), SEEK_SET);
		int fr = fwrite(pieceData, 1, pBuf->nPieceSize, fp);

		if (fr < 0)
		{
			LogPrint(LOG_CRITICAL, "Outfile write error\n");
		}

		fclose(fp);
	}

	//DebugPrintCritical("\t\t\tSetPiece : pieceNum : %d, DP : %d\n", pieceNum, pBuf->DP);

	if (pieceNum >= pBuf->DP)
	{
		int status = PIECE_STATUS_COMPLETED, shift = 0;
		while(status == PIECE_STATUS_COMPLETED)
		{
			status = _getDownloadMapStatus(pBuf, pBuf->DP + shift);

			if (status == PIECE_STATUS_COMPLETED) shift++;
		}

		rslt = SENDING;

		_shiftDownloadSection(pBuf, shift);

// 		LogPrint(LOG_DEBUG, "↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓\n", pBuf->EP);
// 		LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~SP    : %d ~~~~~~~~~~~~~~~\n", pBuf->SP);
// 		LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~PP    : %d ~~~~~~~~~~~~~~~\n", pBuf->PP);
// 		LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~DP++  : %d ~~~~~~~~~~~~~~~\n", pBuf->DP);
// 		LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~DS    : %d ~~~~~~~~~~~~~~~\n", pBuf->nDownloadWindowSize);
// 		LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~EP    : %d ~~~~~~~~~~~~~~~\n", pBuf->EP);
	}
	else
	{
		rslt = SUCCESS;
	}

	pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

int prepBuffer_isPlayable(char* key)
{
	PrepBuffer_t *pBuf = NULL;
	
	if (gPrepBufferArray == NULL) return 0;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return 0;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->PP >= pBuf->EP || pBuf->downloadMap == NULL || pBuf->nDownloadWindowSize <= 0)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);

		return 0;
	}

	if (pBuf->PP < pBuf->DP)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);

		return 1;
	}
	
	pthread_mutex_unlock(&pBuf->bufMutex);
	
	return 0;
}

char* prepBuffer_getPlayData(char* key, unsigned int errorPass)
{
	//unsigned char *tmpMap = NULL;
	char *rslt = NULL;
	int status = PIECE_STATUS_EMPTY;
	//int tmpDP = 0;

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	pthread_mutex_lock(&pBuf->bufMutex);
	
	LogPrint(LOG_DEBUG, "************************  getPlayData  **************************************\n");
	/*LogPrint(LOG_DEBUG, "\t\t\tbefore my sp : %d\n", pBuf->SP);
	LogPrint(LOG_DEBUG, "\t\t\tbefore my cs : %d\n", pBuf->DP - pBuf->SP);
	LogPrint(LOG_DEBUG, "\t\t\tbefore my pp : %d\n", pBuf->PP);
	LogPrint(LOG_DEBUG, "\t\t\tbefore my dp : %d\n", pBuf->DP);
	LogPrint(LOG_DEBUG, "\t\t\tbefore my ds : %d\n", pBuf->nDownloadWindowSize);
	LogPrint(LOG_DEBUG, "\t\t\tbefore my ep : %d\n", pBuf->EP);
	LogPrint(LOG_DEBUG, "*****************************************************************************\n");*/

//	DebugPrintCritical("\t\t\PP : %d\n", pBuf->PP);
		
	if (pBuf->PP >= pBuf->EP)
	{
		LogPrint(LOG_DEBUG, "\t\t!!!!!!!!!!! 1111 pBuf->PP >= pBuf->EP\n");
		/*LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
		LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!    NULL    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
		LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
		LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");*/
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if (pBuf->nDownloadFlag == 0)
	{
		LogPrint(LOG_DEBUG, "return nDownloadFlag : %d\n", pBuf->nDownloadFlag);
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if (pBuf->PP < pBuf->SP)
	{
		if (pBuf->SP - pBuf->PP > pBuf->ES) // 줄게 없다
		{
			//pBuf->PP = pBuf->SP;
			pBuf->PP = pBuf->SP + ((pBuf->DP - pBuf->SP) / 5);

			LogPrint(LOG_DEBUG, "\t\t!!!!!!!!!!! 22222 pBuf->PP = pBuf->SP\n");
		}
	}
	
	if (pBuf->PP >= pBuf->DP)
	{
		if (errorPass > 0)
		{
			status = _getDownloadMapStatus(pBuf, pBuf->PP);

			LogPrint(LOG_DEBUG, "!!!!status!!! : %d\n", status);

			if (/*status == PIECE_STATUS_DOWNLOADING || */status == PIECE_STATUS_OUTOFDS)
			{
				/*
				LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!    NULL    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");*/
				pthread_mutex_unlock(&pBuf->bufMutex);
				return rslt;
			}
			else if (status == PIECE_STATUS_EMPTY || status == PIECE_STATUS_ERROR || status == PIECE_STATUS_COMPLETED || status == PIECE_STATUS_DOWNLOADING)
			{
				if (status == PIECE_STATUS_COMPLETED)
				{
					rslt = (char *)malloc(sizeof(char *) * pBuf->nPieceSize);
					cpymem(rslt, pBuf->buffer + (((pBuf->PP/* - pBuf->SP*/) % pBuf->nBufferMapSize) * pBuf->nPieceSize), pBuf->nPieceSize);

					pBuf->PP++;

					if (pBuf->nDownloadFlag > 0) pBuf->nDownloadFlag--;
					//DebugPrintInfo("nDownloadFlag : %d\n", pBuf->nDownloadFlag);
				}
				
				LogPrint(LOG_DEBUG, "\t\tshift!!!!!!!!\n");
				_shiftDownloadSection(pBuf, 1);
			}
			else
			{
				/*LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!    NULL    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
				LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");*/
				LogPrint(LOG_DEBUG, "\t\t!!!!!!!!!!! 3333333333\n");
				pthread_mutex_unlock(&pBuf->bufMutex);
				return rslt;
			}
		}
		else
		{
			LogPrint(LOG_DEBUG, "\t\tif (errorPass < 0)  : %d\n", errorPass);
			/*LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
			LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!    NULL    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
			LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
			LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");*/
			pthread_mutex_unlock(&pBuf->bufMutex);
			return rslt;
		}
	}
	else // 완료 구간(CS)이면
	{
		rslt = (char *)malloc(sizeof(char *) * pBuf->nPieceSize);
		cpymem(rslt, pBuf->buffer + (((pBuf->PP/* - pBuf->SP*/) % pBuf->nBufferMapSize) * pBuf->nPieceSize), pBuf->nPieceSize);

		LogPrint(LOG_DEBUG, "\t\tmemcpy PP = %d\n", pBuf->PP);

		pBuf->PP++;

		if (pBuf->nDownloadFlag > 0) pBuf->nDownloadFlag--;
		//DebugPrintInfo("nDownloadFlag : %d\n", pBuf->nDownloadFlag);
		
	}

// 	LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
// 	LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!! SP : %d    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n", pBuf->SP);
 	LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!! PP : %d    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n", pBuf->PP - 1);
// 	LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!! DP : %d    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n", pBuf->DP);
// 	LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!! EP : %d    !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n", pBuf->EP);
 	LogPrint(LOG_DEBUG, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
	
	pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

double prepBuffer_getPieceDataTimestamp(char* key, unsigned int pieceNum)
{
	double rslt = -1;

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	pthread_mutex_lock(&pBuf->bufMutex);

	auto it = pBuf->TimestampMap->find(pieceNum);

	if (it != pBuf->TimestampMap->end())
	{
		rslt = it->second;
	}	

	pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

int prepBuffer_getPieceIndex4Timestamp(char* key, double time, int& lastIndex)
{
	int rslt = -1;

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	pthread_mutex_lock(&pBuf->bufMutex);

	LogPrint(LOG_WARNING, "Cur Time : %.0lf\n", time);
	LogPrint(LOG_WARNING, "lastIndex : %d\n", lastIndex);
	LogPrint(LOG_WARNING, "TimestampMap size : %d\n", pBuf->TimestampMap->size());
	LogPrint(LOG_WARNING, "SP : %d, PP : %d, DP : %d\n", pBuf->SP, pBuf->PP, pBuf->DP);

	int i = 0;

	for (i = lastIndex; i < pBuf->DP; i++)
	{
		auto it = pBuf->TimestampMap->find(i);
		if (it != pBuf->TimestampMap->end())
		{
			LogPrint(LOG_WARNING, "SYNC -- %d : %.0lf\n", it->first, it->second);

			if (it->second >= time)
			{
				if (i - 1 >= 0)
				{
					auto before = pBuf->TimestampMap->find(i - 1);
					if (before != pBuf->TimestampMap->end())
					{
						if (time - before->second < it->second - time)
						{
							rslt = before->first;
						}
						else
						{
							rslt = it->first;
						}
					}
					else
					{
						rslt = it->first;
					}
				}
				else
				{
					rslt = it->first;
				}
				break;
			}
		}
		else
		{
			LogPrint(LOG_WARNING, "Not found -- %d\n", i);
		}
	}

	lastIndex = i - 1;

	if (lastIndex < 0) lastIndex = 0;
	
	pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

int prepBuffer_getPieceData(char* key, int pieceNum, char* pieceData)
{
	//FILE *fp1, *fp2;
	//char filename[100];
	int rslt = FAIL/*, status = PIECE_STATUS_EMPTY*/;

	LogPrint(LOG_DEBUG, "prepBuffer_getPieceData\n");

	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL || pieceData == NULL) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	pthread_mutex_lock(&pBuf->bufMutex);

	LogPrint(LOG_DEBUG, "pieceNum:%d\n", pieceNum);
	LogPrint(LOG_DEBUG, "pieceNum:%u\n", pieceNum);
	LogPrint(LOG_DEBUG, "SP:%d, DP:%d, ES:%d, EP:%d\n", pBuf->SP, pBuf->DP, pBuf->ES, pBuf->EP);

	if (pieceNum < pBuf->SP)
	{
		LogPrint(LOG_DEBUG, "pieceNum < pBuf->SP\n");
	}

	if ((int)pieceNum < pBuf->SP)
	{
		LogPrint(LOG_DEBUG, "(int)pieceNum < pBuf->SP\n");
	}

	if (pieceNum > pBuf->SP)
	{
		LogPrint(LOG_DEBUG, "pieceNum > pBuf->SP\n");
	}

	if (pieceNum < pBuf->SP)
	{
		LogPrint(LOG_DEBUG, "pieceNum < pBuf->SP\n");
		if (pBuf->SP - pieceNum > pBuf->ES) // 줄게 없다
		{
			LogPrint(LOG_DEBUG, "pBuf->SP - pieceNum > pBuf->ES\n");
			pthread_mutex_unlock(&pBuf->bufMutex);
			return rslt;
		}
	}

	if (pieceNum >= pBuf->EP) // 줄게 없다
	{
		LogPrint(LOG_DEBUG, "pieceNum >= pBuf->EP\n");
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if (pieceNum < pBuf->DP) // 완료 구간(CS)이면
	{
		LogPrint(LOG_DEBUG, "pieceNum < pBuf->DP\n");
		rslt = SUCCESS;
	}
	else if (_getDownloadMapStatus(pBuf, pieceNum) == PIECE_STATUS_COMPLETED) // 다운로드 구간(DS)이면
	{
		LogPrint(LOG_DEBUG, "pieceNum in DS and complete\n");
		rslt = SUCCESS;
	}

	if (rslt == SUCCESS)
	{
		cpymem(pieceData, pBuf->buffer + ((pieceNum % pBuf->nBufferMapSize) * pBuf->nPieceSize), pBuf->nPieceSize);
		LogPrint(LOG_DEBUG, "cpymem\n");
		/*sprintf(filename, "D:\\preptemp\\ZZZZZZ%s.mp4", key);
		fp1=fopen(filename, "ab");
		if(!fp1) 
		{
			LogPrint(LOG_DEBUG, "wb file open failure\n");
		}
		else
		{
			fwrite(pieceData, pBuf->nPieceSize, 1, fp1);
		}
		fclose(fp1);*/
		/*{
			FILE *fp = fopen("D:\\preptemp\\123.mp4", "ab");
			fwrite(pieceData, pBuf->nPieceSize, 1, fp );
			fclose(fp);
		}*/
	}
		
	pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

int prepBuffer_refreshDownloadMap(char *key, unsigned int sp_index, unsigned int complete_length, unsigned int dp_index, unsigned int ds_length, unsigned char *download_map)
{
	PrepBuffer_t *pBuf = NULL;
	//unsigned int bufSize = complete_length + ds_length;

	int rslt = FAIL;

	if (gPrepBufferArray == NULL) return rslt;

	if (download_map == NULL && complete_length <= 0) return rslt;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return rslt;

	pthread_mutex_lock(&pBuf->bufMutex);

// 	LogPrint(LOG_DEBUG, "\t\t\trefreshMap start\n");
// 	LogPrint(LOG_DEBUG, "\t\t\trecv sp : %d\n", sp_index);
// 	LogPrint(LOG_DEBUG, "\t\t\trecv cs : %d\n", complete_length);
// 	LogPrint(LOG_DEBUG, "\t\t\trecv dp : %d\n", dp_index);
// 	LogPrint(LOG_DEBUG, "\t\t\trecv ds : %d\n", ds_length);
// 
// 	LogPrint(LOG_DEBUG, "\t\t\tbefore my sp : %d\n", pBuf->SP);
// 	LogPrint(LOG_DEBUG, "\t\t\tbefore my cs : %d\n", pBuf->DP - pBuf->SP);
// 	LogPrint(LOG_DEBUG, "\t\t\tbefore my pp : %d\n", pBuf->PP);
// 	LogPrint(LOG_DEBUG, "\t\t\tbefore my dp : %d\n", pBuf->DP);
// 	LogPrint(LOG_DEBUG, "\t\t\tbefore my ds : %d\n", pBuf->nDownloadWindowSize);
// 	LogPrint(LOG_DEBUG, "\t\t\tbefore my ep : %d\n", pBuf->EP);
// 	

	rslt = SUCCESS;

	if (pBuf->SP < 0 || pBuf->SP == pBuf->EP || pBuf->EP < sp_index)
	{
		int sp = sp_index + (int)(complete_length * (pBuf->nSpStartPercent / 100.0));

		if (pBuf->EP < sp_index && (pBuf->SP != pBuf->EP && pBuf->SP >= 0))
		{
			rslt = SENDING;

			LogPrint(LOG_WARNING, "___________________________________________________________\n");
			LogPrint(LOG_WARNING, "Buffermap refresh!!\n");
			LogPrint(LOG_WARNING, "peer Buffermap \n");
			LogPrint(LOG_WARNING, "sp : %d\n", sp_index);
			LogPrint(LOG_WARNING, "dp : %d\n", dp_index);
			LogPrint(LOG_WARNING, "___________________________________________________________\n");
			LogPrint(LOG_WARNING, "before my Buffermap \n");
			LogPrint(LOG_WARNING, "sp : %d\n", pBuf->SP);
			LogPrint(LOG_WARNING, "cs : %d\n", pBuf->DP - pBuf->SP);
			LogPrint(LOG_WARNING, "pp : %d\n", pBuf->PP);
			LogPrint(LOG_WARNING, "dp : %d\n", pBuf->DP);
			LogPrint(LOG_WARNING, "___________________________________________________________\n");

			pBuf->StartDP = pBuf->DP - sp;
		}
		else
		{
			pBuf->StartDP = sp;
		}

		pBuf->SP = sp;
		pBuf->DP = sp;
		pBuf->PP = sp;
		pBuf->EP = pBuf->DP + pBuf->nDownloadWindowSize;
		

		LogPrint(LOG_WARNING, "after my Buffermap \n");
		LogPrint(LOG_WARNING, "sp : %d\n", pBuf->SP);
		LogPrint(LOG_WARNING, "cs : %d\n", pBuf->DP - pBuf->SP);
		LogPrint(LOG_WARNING, "pp : %d\n", pBuf->PP);
		LogPrint(LOG_WARNING, "dp : %d\n", pBuf->DP);
		LogPrint(LOG_WARNING, "___________________________________________________________\n");
		
		if(pBuf->downloadMap != NULL) free(pBuf->downloadMap);
		pBuf->downloadMap = (unsigned char *)malloc(sizeof(unsigned char) * pBuf->nDownloadWindowSize);
		memset(pBuf->downloadMap, 0, sizeof(unsigned char) * pBuf->nDownloadWindowSize);
	}
	
// 	LogPrint(LOG_DEBUG, "\t\t\tafter my sp : %d\n", pBuf->SP);
// 	LogPrint(LOG_DEBUG, "\t\t\tafter my cs : %d\n", pBuf->DP - pBuf->SP);
// 	LogPrint(LOG_DEBUG, "\t\t\tafter my pp : %d\n", pBuf->PP);
// 	LogPrint(LOG_DEBUG, "\t\t\tafter my dp : %d\n", pBuf->DP);
// 	LogPrint(LOG_DEBUG, "\t\t\tafter my ds : %d\n", pBuf->nDownloadWindowSize);
// 	LogPrint(LOG_DEBUG, "\t\t\tafter my ep : %d\n", pBuf->EP);

	pthread_mutex_unlock(&pBuf->bufMutex);

	if (rslt == SENDING)
	{
		prepBuffer_removePieceDataTimestamp(key, -1);
	}

	return rslt;
}

int prepBuffer_getPieceIndex4Download(char *key, unsigned int sp_index, unsigned int complete_length, unsigned int dp_index, unsigned int ds_length, unsigned char *download_map)
{
	unsigned int i=0;
	int downIndex = -1;
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return downIndex;

	if (download_map == NULL && complete_length <= 0) return downIndex;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return downIndex;

	pthread_mutex_lock(&pBuf->bufMutex);	

	if (sp_index + complete_length + ds_length < pBuf->DP)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return downIndex;
	}

	if (pBuf->PP < pBuf->SP)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return downIndex;
	}

	for (i=0; i<pBuf->nDownloadWindowSize; i++)
	{
		if (pBuf->downloadMap[i] != PIECE_STATUS_COMPLETED && pBuf->downloadMap[i] != PIECE_STATUS_DOWNLOADING)
		{
			if (dp_index > pBuf->DP + i && pBuf->DP + i >= sp_index) // 완료 구간(CS)이면
			{
				downIndex = pBuf->DP + i;
				break;
			}
			else if (dp_index <= pBuf->DP + i && pBuf->DP + i < dp_index + ds_length && download_map != NULL) // 다운로드 구간(DS)이면
			{
				if (download_map[(pBuf->DP + i) - dp_index] == PIECE_STATUS_COMPLETED)
				{
					downIndex = pBuf->DP + i;
					break;
				}
				else
				{
					continue;
				}
			}
			else
			{
				break;
			}
		}
	}
	
	pthread_mutex_unlock(&pBuf->bufMutex);
	
	return downIndex;
}

int prepBuffer_getCurrentSP(char* key)
{
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return 0;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return 0;

	return pBuf->SP;
}

int prepBuffer_getCurrentDP(char* key)
{
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return 0;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return 0;

	return pBuf->DP;
}

int prepBuffer_getCurrentPP(char* key)
{
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return 0;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return 0;

	return pBuf->PP;
}

void prepBuffer_setCurrentPP(char* key, unsigned int pp)
{
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return;

	pBuf->PP = pp;
}

int prepBuffer_getCurrentCP(char* key)
{
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return 0;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return 0;

	return pBuf->CP;
}

int prepBuffer_getCurrentCS(char* key)
{
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return 0;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return 0;

	return pBuf->DP - pBuf->SP;
}

void prepBuffer_getCurrentBufferStatus(char* key, int& sp, int& pp, int& cp, int& cs, int& dp)
{
	PrepBuffer_t *pBuf = NULL;

	if (gPrepBufferArray == NULL) return;

	pBuf = _getBufferByKey(key);

	if (pBuf == NULL) return;

	sp = pBuf->SP;
	pp = pBuf->PP;
	cp = pBuf->CP;
	cs = pBuf->DP - pBuf->SP;
	dp = pBuf->DP;
}

/*void prepBuffer_SetCallback(PrepDelegate pd)
{
	PrepProgress = pd;
}*/
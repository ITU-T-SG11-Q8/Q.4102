#ifdef WIN32
#define _CRTDBG_MAP_ALLOC
#include "crtdbg.h"
#include <direct.h>
#include <io.h>
#else
#include <sys/stat.h>
#include <unistd.h>
#define _mkdir(x) mkdir(x, S_IRWXU | S_IRWXG | S_IROTH | S_IXOTH)
#define _access(x, y) access(x, y)
#endif
#include <stdio.h>
#include <string.h>
#include "PODOBuffer.h"
#include "commonDefine.h"
#include "NetworkUtil.h"
#include "Util.h"

PODOBuffer_t **gPODOBufferArray;
static unsigned int gnMaxBufferCount = 0;
static unsigned int gnCurrentBufferCount = 0;

//static PrepDelegate PrepProgress;
//////////////////////////////////////////////////////////////////////////
// private method

PODOBuffer_t *_getPODOBufferByKey(char* key)
{
	unsigned int i=0;

	if (gPODOBufferArray == NULL) return NULL;

	for (i=0; i<gnMaxBufferCount; i++)
	{
		if (gPODOBufferArray[i] != NULL && gPODOBufferArray[i]->key != NULL)
		{
			if (!strcmp(gPODOBufferArray[i]->key, key))
			{
				return gPODOBufferArray[i];
			}
		}
	}

	return NULL;
}

PODOBuffer_t *PODOBuffer_getPODOBufferByKey(char* key)
{
	return _getPODOBufferByKey(key);
}

int _getPODODownloadMapStatus(PODOBuffer_t* pBuf, unsigned int pieceNum)
{
	int rslt = PIECE_STATUS_OUTOFDS;

	if (pBuf == NULL) return rslt;

	if (pBuf->downloadMap == NULL)
	{
		return rslt;
	}

	if (pBuf->nDownloadMapSize < pieceNum)
	{
		return rslt;
	}

	rslt = pBuf->downloadMap[pieceNum];

	return rslt;
}

int _makeDir(char *rootPath, char *filePath)
{
	int i = 0, old = 0, limit = 0;
	char tmp[500] = { '\0' };

	sprintf_s(tmp, rootPath);

	tmp[strlen_s(rootPath)] = '\\';

	for (i = strlen_s(filePath) - 1; i >= 0; i--)
	{
		if (filePath[i] == '\\')
		{
			limit = i + 1;
			break;
		}
	}

	for (i = 0; i < limit; i++)
	{
		if (filePath[i] == '\\')
		{
			cpymem(tmp + strlen_s(tmp), filePath + old, i - old);
			tmp[i + strlen_s(tmp)] = '\0';

			if (_access(tmp, 0) < 0)
			{
				_mkdir(tmp);
			}

			old = i;
		}
	}

	return 0;
}

int _removeDir(char *dirPath)
{
#ifdef WIN32

	char tmp[500] = { '\0' };
	struct _finddata_t filedata;
	intptr_t hFile;
	intptr_t hSubFile;
	char path[] = "*.*";

	if ((hFile = _findfirst(dirPath, &filedata)) != -1L)
	{
		if (!(filedata.attrib & _A_SUBDIR))
		{
			remove(dirPath);
		}
		else
		{
			sprintf_s(tmp, "%s%s%s", dirPath, "\\", path);

			if ((hSubFile = _findfirst(tmp, &filedata)) != -1L)
			{
				do {
					if (!strcmp(filedata.name, ".") || !strcmp(filedata.name, ".."))
					{
						continue;
					}

					if (filedata.attrib & _A_SUBDIR)
					{
						sprintf_s(tmp, "%s%s%s", dirPath, "\\", filedata.name);

						_removeDir(tmp);
					}
					else
					{
						sprintf_s(tmp, "%s%s%s", dirPath, "\\", filedata.name);

						remove(tmp);
					}

				} while (_findnext(hSubFile, &filedata) == 0);

				_findclose(hSubFile);

				_rmdir(dirPath);
			}
		}

		_findclose(hFile);
	}
#endif
	return 0;
}

int _removeContent(char *rootPath, char *filePath)
{
	int i = 0, tmpIdx = 0;
	char tmp[500] = { '\0' };

	tmpIdx = strlen_s(rootPath);

	sprintf_s(tmp, rootPath);

	tmp[tmpIdx++] = '\\';

	for (i = 0; i < strlen_s(filePath); i++)
	{
		if (filePath[i] == '\\')
		{
			tmp[tmpIdx] = '\0';
			break;
		}
		else
		{
			tmp[tmpIdx++] = filePath[i];
		}
	}

	return _removeDir(tmp);
}

void _removePODOBufferDownFiles(PODOBuffer_t* buffer, int removeData)
{
	int bufidx = -1, i = 0;
	
	if (buffer != NULL)
	{
		if (buffer->downDir != NULL && strlen_s(buffer->downDir))
		{
			if (buffer->pFileInfos != NULL)
			{
				for (i = 0; i < buffer->nFileCount; i++)
				{
					if (buffer->pFileInfos[i] != NULL)
					{
						if (buffer->pFileInfos[i]->fileName != NULL && strlen_s(buffer->pFileInfos[i]->fileName))
						{
							pthread_mutex_lock(&buffer->pFileInfos[i]->fileMutex);

							if (buffer->pFileInfos[i]->pFile != NULL)
							{
								fclose(buffer->pFileInfos[i]->pFile);
								buffer->pFileInfos[i]->pFile = NULL;
							}

							_removeContent(buffer->downDir, buffer->pFileInfos[i]->fileName);
							if (removeData > 0)
							{
								_removeContent(buffer->completeDir, buffer->pFileInfos[i]->fileName);
							}

							pthread_mutex_unlock(&buffer->pFileInfos[i]->fileMutex);
						}
					}
				}
			}
		}
	}
}

void _freeFileInfos(FileInfo_t **pFileInfos, unsigned int nFileCount)
{
	int i = 0;
	for (i = 0; i < nFileCount; i++)
	{
		if (pFileInfos[i] != NULL)
		{
			if (pFileInfos[i]->fileName != NULL && strlen_s(pFileInfos[i]->fileName))
			{
				free(pFileInfos[i]->fileName);
				pFileInfos[i]->fileName = NULL;
			}

			if (pFileInfos[i]->rootDir != NULL)
			{
				free(pFileInfos[i]->rootDir);
				pFileInfos[i]->rootDir = NULL;
			}

			if (pFileInfos[i]->pFile != NULL)
			{
				fclose(pFileInfos[i]->pFile);
				pFileInfos[i]->pFile = NULL;
			}

			//if (pFileInfos[i]->fileMutex != NULL)
			{
				pthread_mutex_destroy(&pFileInfos[i]->fileMutex);
				//pFileInfos[i]->fileMutex = NULL;
			}

			free(pFileInfos[i]);
			pFileInfos[i] = NULL;
		}
	}

	free(pFileInfos);
}

void _freePODOBuffer(PODOBuffer_t* buffer, int removeData)
{
	int bufidx = -1, i = 0;

	if (buffer != NULL)
	{
		if (!buffer->isServer)
		{
			_removePODOBufferDownFiles(buffer, removeData);
		}

		if (buffer->key != NULL && strlen_s(buffer->key))
		{
			free(buffer->key);
			buffer->key = NULL;
		}

		if (buffer->downDir != NULL && strlen_s(buffer->downDir))
		{
			free(buffer->downDir);
			buffer->downDir = NULL;
		}

		if (buffer->completeDir != NULL && strlen_s(buffer->completeDir))
		{
			free(buffer->completeDir);
			buffer->completeDir = NULL;
		}

		if (buffer->pFileInfos != NULL)
		{
			_freeFileInfos(buffer->pFileInfos, buffer->nFileCount);
			buffer->pFileInfos = NULL;
		}

		if (buffer->downloadMap != NULL)
		{
			free(buffer->downloadMap);
			buffer->downloadMap = NULL;
		}

		//if (buffer->bufMutex != NULL)
		{
			pthread_mutex_destroy(&buffer->bufMutex);
			//buffer->bufMutex = NULL;
		}

		bufidx = PODOBuffer_getBufferArrayIndex(buffer);

		if (bufidx >= 0)
		{
			free(gPODOBufferArray[bufidx]);
			gPODOBufferArray[bufidx] = NULL;
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

/*void _shiftDownloadSection(PODOBuffer_t * pBuf, int shift)
{
	if (shift <= 0)
	{
		return;
	}
	else
	{
		unsigned char *tmpmap = (unsigned char *)malloc(pBuf->nDownloadWindowSize);
		memset(tmpmap, 0, pBuf->nDownloadWindowSize);
		memcpy(tmpmap, pBuf->downloadMap + shift, pBuf->nDownloadWindowSize - shift);
		free(pBuf->downloadMap);
		pBuf->downloadMap = tmpmap;

		pBuf->DP += shift;
		pBuf->EP = pBuf->DP + pBuf->nDownloadWindowSize;

		if (pBuf->EP + pBuf->ES > pBuf->nBufferMapSize)
		{
			if (pBuf->SP < (pBuf->EP + pBuf->ES) - pBuf->nBufferMapSize)
			{
				pBuf->SP = (pBuf->EP + pBuf->ES) - pBuf->nBufferMapSize;
			}			
		}
	}
}*/

FileInfo_t* _getPODOFileInfoByPieceIndex(PODOBuffer_t *pBuf, unsigned int pieceNum)
{
	int i = 0;

	for (i=0; i<pBuf->nFileCount; i++)
	{
		if (pBuf->pFileInfos[i]->nPieceStart <= pieceNum && pBuf->pFileInfos[i]->nPieceEnd >= pieceNum)
		{
			return pBuf->pFileInfos[i];
		}
	}

	return NULL;
}

void _errorPieceCheck(char* key)
{
	PODOBuffer_t *pBuf = NULL;

	int i = 0;

	if (gPODOBufferArray == NULL) return;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->downloadMap == NULL)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return;
	}

	if (pBuf->pFileInfos == NULL || pBuf->nFileCount <= 0)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return;
	}

	if (pBuf->downloadMap[pBuf->nDownloadMapSize - 1] != PIECE_STATUS_EMPTY)
	{
		for (i = 0; i < pBuf->nDownloadMapSize; i++)
		{
			if (pBuf->downloadMap[i] == PIECE_STATUS_DOWNLOADING)
				pBuf->downloadMap[i] = PIECE_STATUS_EMPTY;
		}
	}

	pthread_mutex_unlock(&pBuf->bufMutex);
}

int PODOBuffer_isPODOComplete(char *key, int lock)
{
	int i = 0;

	PODOBuffer_t *pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return 0;

	if (lock) pthread_mutex_lock(&pBuf->bufMutex);	

	for (i=0; i<pBuf->nFileCount; i++)
	{
		if (pBuf->pFileInfos[i] != NULL && !pBuf->pFileInfos[i]->nIsComplete)
		{
			if (lock) pthread_mutex_unlock(&pBuf->bufMutex);
			return 0;
		}
	}

	if (pBuf->lCompleteTime <= 0)
	{
		pBuf->lCompleteTime = (long)time(NULL);
	}

	if (lock) pthread_mutex_unlock(&pBuf->bufMutex);

	return 1;
}

int PODOBuffer_removeDownFile(char *key)
{
	PODOBuffer_t *pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return FAIL;
	
	if (!pBuf->isServer)
	{
		_removePODOBufferDownFiles(pBuf, 0);
	}

	return SUCCESS;
}


//////////////////////////////////////////////////////////////////////////

void PODOBuffer_initBufferArray(unsigned int bufCnt)
{
	gPODOBufferArray = (PODOBuffer_t **)malloc(sizeof(PODOBuffer_t *) * bufCnt);
	if (gPODOBufferArray != NULL)
	{
		memset(gPODOBufferArray, 0, sizeof(PODOBuffer_t *) * bufCnt);
	}
	
	gnMaxBufferCount = bufCnt;
	gnCurrentBufferCount = 0;
}

int PODOBuffer_newBuffer(char* key, unsigned int pieceSize, unsigned int fileCount, FileInfo_t** fileInfos, int totalPieceCount, char* downDir, char* completeDir, int nVersion, int nIsServer)
{
	unsigned int i = 0;
	PODOBuffer_t *buf = NULL;
	char fname[1000] = {'\0'};

	if (gnMaxBufferCount <= gnCurrentBufferCount)
	{
		return FAIL;
	}

	buf = (PODOBuffer_t *)malloc(sizeof(PODOBuffer_t));
	if (buf == NULL)
	{
		perror("malloc fail\n");
		return FAIL;
	}

	memset(buf,0, sizeof(PODOBuffer_t));
	
	buf->key = _strdup(key);
	buf->downDir = _strdup(downDir);
	buf->completeDir = _strdup(completeDir);
	buf->isServer = nIsServer;
	buf->nFileCount = fileCount;
	buf->nPieceSize = pieceSize;
	buf->nDownloadMapSize = totalPieceCount;

	buf->downloadMap = (unsigned char *)malloc(sizeof(unsigned char) * totalPieceCount);
	if (buf->downloadMap == NULL)
	{
		free(buf);
		return FAIL;
	}

	if (nIsServer)
	{
		memset(buf->downloadMap, PIECE_STATUS_COMPLETED, sizeof(unsigned char) * totalPieceCount);
	}
	else
	{
		memset(buf->downloadMap, PIECE_STATUS_EMPTY, sizeof(unsigned char) * totalPieceCount);
	}
	
	for(i=0; i<gnMaxBufferCount; i++)
	{
		if (gPODOBufferArray[i] == NULL)
		{
			gPODOBufferArray[i] = buf;
			break;
		}
	}

	pthread_mutex_init(&buf->bufMutex, NULL);

	buf->pFileInfos = (FileInfo_t **)malloc(sizeof(FileInfo_t *) * fileCount);
	if (buf->pFileInfos == NULL)
	{
		free(buf->downloadMap);
		free(buf);
		gPODOBufferArray[i] = NULL;
		return FAIL;
	}

	memset(buf->pFileInfos, 0, sizeof(FileInfo_t *) * fileCount);

	for(i=0; i<fileCount; i++)
	{
		buf->pFileInfos[i] = (FileInfo_t *)malloc(sizeof(FileInfo_t));
		if (buf->pFileInfos[i] != NULL)
		{
			memset(buf->pFileInfos[i], 0, sizeof(FileInfo_t));

			buf->pFileInfos[i]->fileName = _strdup(fileInfos[i]->fileName);
			buf->pFileInfos[i]->rootDir = _strdup(fileInfos[i]->rootDir);
			buf->pFileInfos[i]->nFileSize = fileInfos[i]->nFileSize;
			buf->dTotalBytes += fileInfos[i]->nFileSize;
			buf->pFileInfos[i]->nPieceStart = fileInfos[i]->nPieceStart;
			buf->pFileInfos[i]->nPieceEnd = fileInfos[i]->nPieceEnd;
			pthread_mutex_init(&buf->pFileInfos[i]->fileMutex, NULL);
		}

		if (!nIsServer)
		{
			sprintf_s(fname, "%s%s%s", buf->downDir, "\\", buf->pFileInfos[i]->fileName);

			_makeDir(buf->downDir, buf->pFileInfos[i]->fileName);
			remove(fname);
			buf->pFileInfos[i]->pFile = fopen(fname, "wb+");

			if (buf->pFileInfos[i]->pFile == NULL)
			{
				perror("fopen error");
				buf->pFileInfos[i]->pFile = NULL;
			}
		}
		else
		{
			buf->pFileInfos[i]->nIsComplete = 1;
		}

		free(fileInfos[i]);
	}
	free(fileInfos);

	buf->nVersion = nVersion;
	
	gnCurrentBufferCount++;

	buf->lAddedTime = (long)time(NULL);
	if (nIsServer > 0)
	{
		buf->lCompleteTime = buf->lAddedTime;
	}
	
	return SUCCESS;
}

int PODOBuffer_updateBuffer(char* key, unsigned int fileCount, FileInfo_t** fileInfos, int totalPieceCount, int nVersion)
{
	unsigned int i = 0, j = 0;
	PODOBuffer_t *buf = NULL;
	char fname[1000] = { '\0' };
	unsigned char* newDownloadMap = NULL;
	FileInfo_t ** newFileInfos = NULL;
	int nTmpIdx = 0;
	int oldfind = 0;

	buf = _getPODOBufferByKey(key);
	if (buf == NULL)
	{
		return FAIL;
	}

	if (buf->nVersion >= nVersion)
	{
		return SUCCESS;
	}

	pthread_mutex_lock(&buf->bufMutex);

	buf->nVersion = nVersion;

	if (buf->isServer)
	{
		if (buf->pFileInfos != NULL)
		{
			_freeFileInfos(buf->pFileInfos, buf->nFileCount);
			buf->pFileInfos = NULL;
		}

		buf->nFileCount = fileCount;
		buf->nDownloadMapSize = totalPieceCount;

		if (buf->downloadMap != NULL)
		{
			free(buf->downloadMap);
		}

		buf->downloadMap = (unsigned char *)malloc(sizeof(unsigned char) * totalPieceCount);
		if (buf->downloadMap == NULL)
		{
			pthread_mutex_unlock(&buf->bufMutex);
			return FAIL;
		}

		memset(buf->downloadMap, PIECE_STATUS_COMPLETED, sizeof(unsigned char) * totalPieceCount);

		buf->pFileInfos = (FileInfo_t **)malloc(sizeof(FileInfo_t *) * fileCount);
		if (buf->pFileInfos == NULL)
		{
			pthread_mutex_unlock(&buf->bufMutex);
			return FAIL;
		}

		memset(buf->pFileInfos, 0, sizeof(FileInfo_t *) * fileCount);

		buf->dTotalBytes = 0;
		for (i = 0; i < fileCount; i++)
		{
			buf->pFileInfos[i] = (FileInfo_t *)malloc(sizeof(FileInfo_t));
			if (buf->pFileInfos[i] != NULL)
			{
				memset(buf->pFileInfos[i], 0, sizeof(FileInfo_t));

				buf->pFileInfos[i]->fileName = _strdup(fileInfos[i]->fileName);
				buf->pFileInfos[i]->rootDir = _strdup(fileInfos[i]->rootDir);
				buf->pFileInfos[i]->nFileSize = fileInfos[i]->nFileSize;
				buf->dTotalBytes += fileInfos[i]->nFileSize;
				buf->pFileInfos[i]->nPieceStart = fileInfos[i]->nPieceStart;
				buf->pFileInfos[i]->nPieceEnd = fileInfos[i]->nPieceEnd;
				pthread_mutex_init(&buf->pFileInfos[i]->fileMutex, NULL);
				buf->pFileInfos[i]->nIsComplete = 1;
			}

			free(fileInfos[i]);
		}
		free(fileInfos);
	}
	else
	{
		newDownloadMap = (unsigned char *)malloc(sizeof(unsigned char) * totalPieceCount);

		if (newDownloadMap != NULL)
		{
			memset(newDownloadMap, PIECE_STATUS_EMPTY, sizeof(unsigned char) * totalPieceCount);
		}
		
		newFileInfos = (FileInfo_t **)malloc(sizeof(FileInfo_t *) * fileCount);

		if (newFileInfos != NULL)
		{
			memset(newFileInfos, 0, sizeof(FileInfo_t *) * fileCount);
		}		

		buf->dTotalBytes = 0;

		for (j = 0; j < fileCount; j++)
		{
			newFileInfos[j] = (FileInfo_t *)malloc(sizeof(FileInfo_t));

			if (newFileInfos[j] != NULL)
			{
				memset(newFileInfos[j], 0, sizeof(FileInfo_t));
			}			

			oldfind = 0;
			if (buf->pFileInfos != NULL)
			{
				for (i = 0; i < buf->nFileCount; i++)
				{
					if (buf->pFileInfos[i] != NULL)
					{
						if (buf->pFileInfos[i]->fileName != NULL && strlen_s(buf->pFileInfos[i]->fileName))
						{
							if (!strcmp(buf->pFileInfos[i]->fileName, fileInfos[j]->fileName) && buf->pFileInfos[i]->nFileSize == fileInfos[j]->nFileSize)
							{
								cpymem(newDownloadMap + (long)fileInfos[j]->nPieceStart, buf->downloadMap + (long)buf->pFileInfos[i]->nPieceStart, (long)(buf->pFileInfos[i]->nPieceEnd - buf->pFileInfos[i]->nPieceStart + 1));

								newFileInfos[j]->nIsComplete = buf->pFileInfos[i]->nIsComplete;
								newFileInfos[j]->pFile = buf->pFileInfos[i]->pFile;
								newFileInfos[j]->fileMutex = buf->pFileInfos[i]->fileMutex;

								free(buf->pFileInfos[i]->fileName);
								buf->pFileInfos[i]->fileName = NULL;

								free(buf->pFileInfos[i]);
								buf->pFileInfos[i] = NULL;

								oldfind = 1;
								break;
							}
						}
					}
				}
			}

			if (!oldfind)
			{
				pthread_mutex_init(&newFileInfos[j]->fileMutex, NULL);

				sprintf_s(fname, "%s%s%s", buf->downDir, "\\", fileInfos[j]->fileName);

				_makeDir(buf->downDir, fileInfos[j]->fileName);
				newFileInfos[j]->pFile = fopen(fname, "wb+");

				if (newFileInfos[j]->pFile == NULL)
				{
					perror("fopen error");
					newFileInfos[j]->pFile = NULL;
				}
			}

			newFileInfos[j]->fileName = _strdup(fileInfos[j]->fileName);
			newFileInfos[j]->nFileSize = fileInfos[j]->nFileSize;
			buf->dTotalBytes += fileInfos[j]->nFileSize;
			newFileInfos[j]->nPieceStart = fileInfos[j]->nPieceStart;
			newFileInfos[j]->nPieceEnd = fileInfos[j]->nPieceEnd;
			
			free(fileInfos[j]);
			fileInfos[j] = NULL;
		}

		free(fileInfos);

		for (i = 0; i < buf->nFileCount; i++)
		{
			if (buf->pFileInfos[i] != NULL)
			{
				if (buf->pFileInfos[i]->fileName != NULL && strlen_s(buf->pFileInfos[i]->fileName))
				{
					if (buf->pFileInfos[i]->pFile != NULL)
					{
						fclose(buf->pFileInfos[i]->pFile);
						buf->pFileInfos[i]->pFile = NULL;
					}

					if (buf->pFileInfos[i]->nIsComplete)
					{
						sprintf_s(fname, "%s%s%s", buf->completeDir, "\\", buf->pFileInfos[i]->fileName);

						_removeDir(fname);
					}
					else
					{
						sprintf_s(fname, "%s%s%s", buf->downDir, "\\", buf->pFileInfos[i]->fileName);

						_removeDir(fname);
					}

					free(buf->pFileInfos[i]->fileName);
					buf->pFileInfos[i]->fileName = NULL;

					//if (buf->pFileInfos[i]->fileMutex != NULL)
					{
						pthread_mutex_destroy(&buf->pFileInfos[i]->fileMutex);
						//buf->pFileInfos[i]->fileMutex = NULL;
					}

					if (buf->pFileInfos[i]->rootDir != NULL )
					{
						free(buf->pFileInfos[i]->rootDir);
						buf->pFileInfos[i]->rootDir = NULL;
					}

					free(buf->pFileInfos[i]);
					buf->pFileInfos[i] = NULL;
				}
			}
		}

		free(buf->downloadMap);
		buf->downloadMap = newDownloadMap;
		buf->nFileCount = fileCount;
		buf->nDownloadMapSize = totalPieceCount;

		free(buf->pFileInfos);
		buf->pFileInfos = newFileInfos;

		nTmpIdx = 0;
		for (i = 0; i < buf->nDownloadMapSize; i++)
		{
			if (buf->downloadMap[i] == PIECE_STATUS_COMPLETED)
			{
				nTmpIdx++;
			}
		}

		//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_UPDATE_DOWNLOAD_PIECE, buf->key, NULL, NULL, 0, nTmpIdx);

		if (nTmpIdx == buf->nDownloadMapSize)
		{
			//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_COMPLETE, buf->key, NULL, NULL, 0, 0);

			PODOBuffer_removeDownFile(buf->key);

			buf->lCompleteTime = (long)time(NULL);
		}
		else
		{
			buf->lCompleteTime = 0;
			//if (PrepProgress != NULL) PrepProgress(PREP_EVENT_START, buf->key, NULL, NULL, 0, 0);
		}
	}

	pthread_mutex_unlock(&buf->bufMutex);

	_errorPieceCheck(key);

	return SUCCESS;
}

void PODOBuffer_freeBufferByKey(char* key, int removeData)
{
	PODOBuffer_t *pBuf = NULL;

	if (gPODOBufferArray == NULL) return;

	if (key == NULL || !strlen_s(key))
		return;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return;

	_freePODOBuffer(pBuf, removeData);
}

int PODOBuffer_getBufferArrayIndex(PODOBuffer_t * buf)
{
	unsigned int i=0;
	if (gPODOBufferArray != NULL)
	{
		for (i=0; i<gnMaxBufferCount; i++)
		{
			if (gPODOBufferArray[i] == buf)
			{
				return i;
			}
		}
	}

	return -1;
}


void PODOBuffer_freeBufferArray()
{
	unsigned int i=0;
	if (gPODOBufferArray != NULL)
	{
		for (i=0; i<gnMaxBufferCount; i++)
		{
			_freePODOBuffer(gPODOBufferArray[i], 0);
		}
	}

	free(gPODOBufferArray);
	gPODOBufferArray = NULL;

	gnCurrentBufferCount = 0;
}
/*
void PODOBuffer_setRecordData(char* key, char* data, unsigned int len)
{
	int pieceCnt = 0, nextPiece = 0;

	PODOBuffer_t *pBuf = NULL;
	
	if (gPODOBufferArray == NULL) return;

	pBuf = _getPODOBufferByKey(key);

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
}*/

char * PODOBuffer_getDownloadMap(char* key)
{
	PODOBuffer_t *pBuf = NULL;
	char *maptmp = NULL;
	
	if (gPODOBufferArray == NULL) return NULL;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return NULL;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->nDownloadMapSize > 0 && pBuf->downloadMap != NULL)
	{
		maptmp = (char *)malloc(sizeof(char) * pBuf->nDownloadMapSize);
		if (maptmp != NULL)
		{
			memset(maptmp, 0, sizeof(char) * pBuf->nDownloadMapSize);
			cpymem(maptmp, pBuf->downloadMap, pBuf->nDownloadMapSize);
		}
	}

	pthread_mutex_unlock(&pBuf->bufMutex);

	return maptmp;
}

int PODOBuffer_getDownloadMap4HELLO(char* key, ProtocolHello_t *hello)
{
	PODOBuffer_t *pBuf = NULL;
	
	if (gPODOBufferArray == NULL) return FAIL;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return FAIL;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->nDownloadMapSize > 0 && pBuf->downloadMap != NULL)
	{
		hello->download_map = (unsigned char *)malloc(sizeof(unsigned char) * pBuf->nDownloadMapSize);
		if (hello->download_map != NULL)
		{
			memset(hello->download_map, 0, sizeof(unsigned char) * pBuf->nDownloadMapSize);

			cpymem(hello->download_map, pBuf->downloadMap, pBuf->nDownloadMapSize);
		}
		hello->ds_length = pBuf->nDownloadMapSize;
	}
	else
	{
		hello->ds_length = 0;
	}
	
	hello->sp_index = 0;
	hello->complete_length = 0;
	hello->dp_index = 0;
	
	hello->valid_time = pBuf->nVersion;

	pthread_mutex_unlock(&pBuf->bufMutex);

	return SUCCESS;
}

int PODOBuffer_getDownloadMap4BUFFERMAP(char* key, ProtocolBuffermap_t *buffermap, unsigned int startPieceIndex, unsigned int number)
{
	unsigned int endPieceIndex = 0;
	PODOBuffer_t *pBuf = NULL;

	if (gPODOBufferArray == NULL) return FAIL;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return FAIL;

	pthread_mutex_lock(&pBuf->bufMutex);

	buffermap->piece_index = 0;
	buffermap->complete_length = 0;
	buffermap->dp_index = 0;
	buffermap->ds_length = pBuf->nDownloadMapSize;

	if (buffermap->ds_length > 0 && pBuf->downloadMap != NULL && pBuf->nDownloadMapSize > 0)
	{
		buffermap->download_map = (unsigned char *)malloc(sizeof(unsigned char) * buffermap->ds_length);
		if (buffermap->download_map != NULL)
		{
			memset(buffermap->download_map, 0, sizeof(unsigned char) * buffermap->ds_length);

			cpymem(buffermap->download_map, pBuf->downloadMap, buffermap->ds_length);
		}
	}

	pthread_mutex_unlock(&pBuf->bufMutex);

	return SUCCESS;
}

int PODOBuffer_setDownloadMapStatusByKey(char* key, unsigned int pieceNum, int status)
{
	PODOBuffer_t *pBuf = NULL;
	
	if (gPODOBufferArray == NULL) return FAIL;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return FAIL;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->downloadMap == NULL)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return FAIL;
	}

	if (pieceNum >= pBuf->nDownloadMapSize)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return FAIL;
	}

	pBuf->downloadMap[pieceNum] = status;

	pthread_mutex_unlock(&pBuf->bufMutex);

	return SUCCESS;
}

int PODOBuffer_getDownloadMapStatusByKey(char* key, unsigned int pieceNum)
{
	int rslt = PIECE_STATUS_OUTOFDS;

	PODOBuffer_t *pBuf = NULL;

	if (gPODOBufferArray == NULL) return rslt;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return 0;

	pthread_mutex_lock(&pBuf->bufMutex);

	rslt = _getPODODownloadMapStatus(pBuf, pieceNum);
	
	pthread_mutex_unlock(&pBuf->bufMutex);

	return rslt;
}

FileInfo_t** PODOBuffer_GetFileInfos(char* key, int* cnt)
{
	PODOBuffer_t *pBuf = NULL;
	FileInfo_t **pFileInfos = NULL;
	int i = 0;

	*cnt = 0;

	if (gPODOBufferArray == NULL) return NULL;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return NULL;

	pthread_mutex_lock(&pBuf->bufMutex);

	pFileInfos = (FileInfo_t **)malloc(sizeof(FileInfo_t *) * pBuf->nFileCount);

	if (pFileInfos != NULL)
	{
		for (i = 0; i < pBuf->nFileCount; i++)
		{
			pFileInfos[i] = (FileInfo_t *)malloc(sizeof(FileInfo_t));

			if (pFileInfos[i] != NULL)
			{
				pFileInfos[i]->fileName = _strdup(pBuf->pFileInfos[i]->fileName);
				pFileInfos[i]->nDownSize = pBuf->pFileInfos[i]->nDownSize;
				pFileInfos[i]->nFileSize = pBuf->pFileInfos[i]->nFileSize;
				pFileInfos[i]->nIsComplete = pBuf->pFileInfos[i]->nIsComplete;
				pFileInfos[i]->nPieceEnd = pBuf->pFileInfos[i]->nPieceEnd;
				pFileInfos[i]->nPieceStart = pBuf->pFileInfos[i]->nPieceStart;
			}
		}
	}

	*cnt = pBuf->nFileCount;

	pthread_mutex_unlock(&pBuf->bufMutex);

	return pFileInfos;
}

int PODOBuffer_setPieceData(char* key, unsigned int pieceNum, char* pieceData)
{
	int i = 0, j = 0, tmp = 0;
	double tmpSize = 0;
	int rslt = FAIL;
	int complete = 0;
	unsigned char *tmpMap = NULL;

	char foldname[1000] = {'\0'};
	char fnewname[1000] = {'\0'};

	PODOBuffer_t *pBuf = NULL;

	FileInfo_t *pFileInfo = NULL;

	if (gPODOBufferArray == NULL) return rslt;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return rslt;

	pthread_mutex_lock(&pBuf->bufMutex);

	if (pBuf->downloadMap == NULL)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if (pieceNum >= pBuf->nDownloadMapSize)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if (pBuf->pFileInfos == NULL || pBuf->nFileCount <= 0)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	pFileInfo = _getPODOFileInfoByPieceIndex(pBuf, pieceNum);

	if(pFileInfo == NULL)
	{
		LogPrint(LOG_CRITICAL, "\t\t\tsetPieceData save error: fileInfo not found.\n");
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	pthread_mutex_lock(&pFileInfo->fileMutex);

	if (!pFileInfo->nIsComplete)
	{
		tmp = pieceNum - pFileInfo->nPieceStart;

		if (pieceNum == pFileInfo->nPieceEnd)
		{
			tmpSize = (unsigned long)pFileInfo->nFileSize % pBuf->nPieceSize;
		}
		else
		{
			tmpSize = pBuf->nPieceSize;
		}

		if (pFileInfo->pFile == NULL)
		{
			LogPrint(LOG_CRITICAL, "\t\t\tsetPieceData save error: file not open.\n");
			pthread_mutex_unlock(&pFileInfo->fileMutex);
			pthread_mutex_unlock(&pBuf->bufMutex);
			return rslt;
		}

		if (pBuf->downloadMap[pieceNum] != PIECE_STATUS_COMPLETED)
		{
			fseek(pFileInfo->pFile, pBuf->nPieceSize * tmp, SEEK_SET);
			fwrite(pieceData, 1, (unsigned long)tmpSize, pFileInfo->pFile);
			pFileInfo->nDownSize += tmpSize;

			pBuf->downloadMap[pieceNum] = PIECE_STATUS_COMPLETED;
			pBuf->nDownloadFlag++;

			rslt = SUCCESS;
		}

		complete = 1;
		for(j=pFileInfo->nPieceStart; j<=pFileInfo->nPieceEnd; j++)
		{
			if (pBuf->downloadMap[j] != PIECE_STATUS_COMPLETED)
			{
				complete = 0;
				break;
			}
		}

		if (complete == 1)
		{
			pFileInfo->nIsComplete = 1;
			fclose(pFileInfo->pFile);
			pFileInfo->pFile = NULL;
/*#ifdef WIN32
			strcat_s(foldname, pBuf->downDir);
			strcat_s(foldname, "\\");
			strcat_s(foldname, pFileInfo->fileName);

			strcat_s(fnewname, pBuf->completeDir);
			strcat_s(fnewname, "\\");
			strcat_s(fnewname, pFileInfo->fileName);
#else*/
			char tmmp[1000] = {0,};
			sprintf_s(tmmp, "%s%s%s%s", foldname, pBuf->downDir, "\\", pFileInfo->fileName);
			sprintf_s(foldname, "%s", tmmp);

			sprintf_s(tmmp, "%s%s%s%s", fnewname, pBuf->completeDir, "\\", pFileInfo->fileName);
			sprintf_s(fnewname, "%s", tmmp);
//#endif
			_makeDir(pBuf->completeDir, pFileInfo->fileName);

			remove(fnewname);
			rename(foldname, fnewname);

			LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~Complete : %s ~~~~~~~~~~~~~~~\n", fnewname);
		}
	}

	pthread_mutex_unlock(&pFileInfo->fileMutex);

	LogPrint(LOG_DEBUG, "\t\t\tsetPieceData save end: %d\n", pieceNum);

	LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~Piece : %d ~~~~~~~~~~~~~~~\n", pieceNum);
	LogPrint(LOG_DEBUG, "~~~~~~~~~~~~~~~~~~DS    : %d ~~~~~~~~~~~~~~~\n", pBuf->nDownloadMapSize);
	
	pthread_mutex_unlock(&pBuf->bufMutex);

	_errorPieceCheck(key);

	return rslt;
}

int PODOBuffer_getPieceData(char* key, unsigned int pieceNum, char* pieceData)
{
	//FILE *fp1, *fp2;
	char fname[1000] = {'\0'};
	int rslt = FAIL, status = PIECE_STATUS_EMPTY, tmp = 0, tmpSize = 0;

	PODOBuffer_t *pBuf = NULL;
	FileInfo_t *pFileInfo = NULL;

	if (gPODOBufferArray == NULL || pieceData == NULL) return rslt;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return rslt;

	pthread_mutex_lock(&pBuf->bufMutex);

	if(pBuf->downloadMap == NULL || pBuf->nDownloadMapSize <= 0)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if(pBuf->nDownloadMapSize <= pieceNum)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	if(pBuf->downloadMap[pieceNum] != PIECE_STATUS_COMPLETED)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	pFileInfo = _getPODOFileInfoByPieceIndex(pBuf, pieceNum);

	if(pFileInfo == NULL)
	{
		LogPrint(LOG_CRITICAL, "\t\t\tgetPieceData error: fileInfo not found.\n");
		pthread_mutex_unlock(&pBuf->bufMutex);
		return rslt;
	}

	pthread_mutex_lock(&pFileInfo->fileMutex);

	if (pFileInfo->nIsComplete)
	{
		if (pFileInfo->pFile == NULL)
		{
			if (pBuf->isServer)
			{
				sprintf_s(fname, "%s%s%s", pFileInfo->rootDir, "\\", pFileInfo->fileName);
			}
			else
			{
				sprintf_s(fname, "%s%s%s", pBuf->completeDir, "\\", pFileInfo->fileName);
			}

			pFileInfo->pFile = fopen(fname, "rb");

			if (pFileInfo->pFile == NULL)
			{
				LogPrint(LOG_CRITICAL, "\t\t\tgetPieceData error: complete file not found.\n");
				pthread_mutex_unlock(&pFileInfo->fileMutex);
				pthread_mutex_unlock(&pBuf->bufMutex);
				return rslt;
			}
		}
	}
	else
	{
		if (pFileInfo->pFile == NULL)
		{
			LogPrint(LOG_CRITICAL, "\t\t\tgetPieceData error: down file not found.\n");
			pthread_mutex_unlock(&pFileInfo->fileMutex);
			pthread_mutex_unlock(&pBuf->bufMutex);
			return rslt;
		}
	}
	
	tmp = pieceNum - pFileInfo->nPieceStart;

	if (pieceNum == pFileInfo->nPieceEnd)
	{
		tmpSize = (unsigned long)pFileInfo->nFileSize % pBuf->nPieceSize;
	}
	else
	{
		tmpSize = pBuf->nPieceSize;
	}

	fseek(pFileInfo->pFile, pBuf->nPieceSize * tmp, SEEK_SET);

	fread(pieceData, 1, tmpSize, pFileInfo->pFile);

	pthread_mutex_unlock(&pFileInfo->fileMutex);
	pthread_mutex_unlock(&pBuf->bufMutex);

	return tmpSize;
}

int PODOBuffer_refreshDownloadMap(char *key, unsigned int sp_index, unsigned int complete_length, unsigned int dp_index, unsigned int ds_length, unsigned char *download_map)
{
	
	return SUCCESS;
}

int PODOBuffer_getPieceIndex4Download(char *key, unsigned int sp_index, unsigned int complete_length, unsigned int dp_index, unsigned int ds_length, unsigned char *download_map)
{
	unsigned int i=0;
	int downIndex = -1;
	PODOBuffer_t *pBuf = NULL;

	if (gPODOBufferArray == NULL) return downIndex;

	if (download_map == NULL) return downIndex;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return downIndex;

	pthread_mutex_lock(&pBuf->bufMutex);	

	if (pBuf->downloadMap ==NULL || pBuf->nDownloadMapSize <= 0)
	{
		pthread_mutex_unlock(&pBuf->bufMutex);
		return downIndex;
	}

	for (i=0; i<pBuf->nDownloadMapSize; i++)
	{
		if (pBuf->downloadMap[i] != PIECE_STATUS_COMPLETED && pBuf->downloadMap[i] != PIECE_STATUS_DOWNLOADING)
		{
			downIndex = i;
			break;
		}
	}
	
	pthread_mutex_unlock(&pBuf->bufMutex);
	
	return downIndex;
}

int PODOBuffer_getCurrentDP(char* key)
{
	/*PODOBuffer_t *pBuf = NULL;

	if (gPODOBufferArray == NULL) return 0;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return 0;

	return pBuf->DP;*/
	return 0;
}

int PODOBuffer_isValidVersion(char* key, unsigned int version)
{
	PODOBuffer_t *pBuf = NULL;

	if (gPODOBufferArray == NULL) return 0;

	pBuf = _getPODOBufferByKey(key);

	if (pBuf == NULL) return 0;

	if (pBuf->nVersion > version)
	{
		return 0;
	}
	else if (pBuf->nVersion == version)
	{
		return 1;
	}
	
	return -1;
}

/*void PODOBuffer_SetCallback(PrepDelegate pd)
{
	PrepProgress = pd;
}*/

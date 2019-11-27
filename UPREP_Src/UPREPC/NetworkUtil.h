#ifndef __NETWORKUTIL_H__
#define __NETWORKUTIL_H__

#ifdef WIN32
#include "Util/pthreadWin32/include/pthread.h"
#define BIG_ENDIAN 9000
#define LITTLE_ENDIAN 9001
#else
#include <pthread.h>
#endif

#define LOG_DEBUG 0
#define LOG_INFO 1
#define LOG_WARNING 2
#define LOG_CRITICAL 3
#define LOG_SILENT 4
#define LOG_SIMULATION 99

int HTTP_Startup();
void HTTP_Cleanup();

void SetLogLevel(int level);
int GetLogLevel();
void SetSimulationLogPrint(int print);
int GetSimulationLogPrint();

int HTTP_GET(char **response, char *address, unsigned int port, char *path, char xmlstr[], int len);
int HTTP_PUT(char **response, char *address, unsigned int port, char *path, char xmlstr[], int len);
int HTTP_POST(char **response, char *address, unsigned int port, char *path, char xmlstr[], int len);
int HTTP_DELETE(char **response, char *address, unsigned int port, char *path, char xmlstr[], int len);

//unsigned char *HTTP_DELETE(char *IP, unsigned int port, char *path, unsigned char *http_body);

int HTTP_TrackerPUT(char *address, unsigned int port, char *path, char xmlstr[], int len);
int HTTP_TrackerDELETE(char *address, unsigned int port, char *path, char xmlstr[], int len);


int TCP_Send(int sockfd, char stream[]);
int TCP_Connect(const char dest_ip[], unsigned short dest_port);
void TCP_Server(void *param);


//int genRandomString(char dest[], int seed, int length);
//int genRandomStringWithPrefix(char *prefix, char dest[], int seed, int length);
pthread_t PTHREAD_CREATE(void *(*start) (void *), void *param);

int strGet_NIC_address(char GetIPArray[]);

char* GetStringValue(char* src);

short align2LittleEndianS(short digit);
int align2LittleEndianI(int digit);
int align2MyEndianS(short digit);
int align2MyEndianI(int digit);

void LogPrint(int level, const char *format, ...);
void SLEEP(unsigned long ulMilliseconds);

double GetNTPTimestamp();
char* GetTimeString(double time);

void SetNTPTimestamp(int use);

//void SetPAMInfo(char *url, int intervalMilli);

double GetCurMilli();


#endif

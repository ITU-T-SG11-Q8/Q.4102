#include "NetworkUtil.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdarg.h>
#include "Util.h"

#ifdef WIN32
#include <windows.h>
#include <winsock.h>
#define close(x)			closesocket(x)
#define sscanf				sscanf_s
#include "Util/pthreadWin32/include/pthread.h"

#pragma comment (lib, "ws2_32.lib")
#pragma comment (lib, "Util/pthreadWin32/lib/pthreadVC.lib")
//#pragma comment (lib, "C:/Users/Jay/Desktop/PrepAgent/PrepAgent/Util/pthreadWin32/lib/pthreadVC.lib")

#else

#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>
#include <ifaddrs.h>

#include <pthread.h>

#include <sys/fcntl.h>
#include <errno.h>

typedef int BOOL;
#define TRUE 1
#define FALSE 0
#define SOCKET_ERROR -1
#define _strdup(x) strdup(x)
#endif

static int LogPrintfLevel = LOG_WARNING;
static int SimulationLogPrint = 0;
static int UseNTPTimestamp = 0;

static char *http_get_message = "GET %s HTTP/1.0\r\nHost: %s\r\nAccept: text/html\r\nUser-Agent: prep-agent\r\nContent-Length: %d\r\n\r\n";

static char *http_put_message = "PUT %s HTTP/1.0\r\nHost: %s\r\nAccept: text/html\r\nUser-Agent: prep-agent\r\nContent-Length: %d\r\n\r\n";

static char *http_post_message = "POST %s HTTP/1.0\r\nHost: %s\r\nAccept: text/html\r\nUser-Agent: prep-agent\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: %d\r\n\r\n";

static char *http_delete_message = "DELETE %s HTTP/1.0\r\nHost: %s\r\nAccept: text/html\r\nUser-Agent: prep-agent\r\nContent-Length: %d\r\n\r\n";

static double NTPTime = 0;
static time_t StartTimeval;

void SetLogLevel(int level)
{
	LogPrintfLevel = level;
	LogPrint(LOG_DEBUG, "LogPrintfLevel!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  %d\n", LogPrintfLevel);
}

int GetLogLevel()
{
	return LogPrintfLevel;
}

void SetSimulationLogPrint(int print)
{
	LogPrint(LOG_DEBUG, "SetSimulationLogPrint!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  %d\n", print);
	SimulationLogPrint = print;
	LogPrint(LOG_DEBUG, "SetSimulationLogPrint!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!  %d\n", SimulationLogPrint);
}

int GetSimulationLogPrint()
{
	return SimulationLogPrint;
}

void SetNTPTimestamp(int use)
{
	UseNTPTimestamp = use;
}

int HTTP_Startup()
{
#ifdef WIN32
	int nErrorStatus;
	WORD wVersionRequested = MAKEWORD(2, 2);
	WSADATA wsaData;

	nErrorStatus = WSAStartup(wVersionRequested, &wsaData);
	if (nErrorStatus != 0)
	{
		return 0;
	}
#endif
	return 1;
}

void HTTP_Cleanup()
{
#ifdef WIN32
	WSACleanup();
#endif
}

#ifdef WIN32
#include < time.h >
#if defined(_MSC_VER) || defined(_MSC_EXTENSIONS)
#define DELTA_EPOCH_IN_MICROSECS  11644473600000000ULL
#else
#define DELTA_EPOCH_IN_MICROSECS  11644473600000000ULL
#endif
struct timezone
{
	int  tz_minuteswest;
	int  tz_dsttime;
};

int gettimeofday(struct timeval *tv, int tz/*struct timezone *tz*/)
{
	FILETIME ft;
	unsigned __int64 tmpres = 0;
	static int tzflag;

	if (NULL != tv)
	{
		GetSystemTimeAsFileTime(&ft);

		tmpres |= ft.dwHighDateTime;
		tmpres <<= 32;
		tmpres |= ft.dwLowDateTime;

		tmpres /= 10;
		tmpres -= DELTA_EPOCH_IN_MICROSECS;
		tv->tv_sec = (long)(tmpres / 1000000UL);
		tv->tv_usec = (long)(tmpres % 1000000UL);
	}

	/*if (NULL != tz)
	{
	if (!tzflag)
	{
	_tzset();
	tzflag++;
	}
	tz->tz_minuteswest = _timezone / 60;
	tz->tz_dsttime = _daylight;
	}*/

	return 0;
}
#endif


double GetCurMilli()
{
	struct timeval tv;
	gettimeofday(&tv, 0);

	double ms = tv.tv_sec * 1000.0 + tv.tv_usec / 1000.0;

	return ms;
}

/*
int HTTP_DELETE(char **response, char *address, unsigned int port, char *path, char xmlstr[], int len)
{
int ret;
int sockfd;

char recv_buf[5192];
char message[2048];


if(address==(char *)0) return 0;

//response[0]='\0';

if(xmlstr==(char *)0) len=0;
else if(len==0) len=strlen(xmlstr);

sprintf(message, http_delete_message, path, address, len);
if(len>0) strcat(message, xmlstr);

/////////////////////////////////////
// TCP CONNECT
sockfd=TCP_Connect(address, port);
if(sockfd<0)
{
return 0;
}

/////////////////////////////////////
// TCP SEND
ret=TCP_Send(sockfd, message);
if(ret<0)
{
printf("[%s:%d] TCP_Send has failed\n", __FILE__, __LINE__);
return 0;
}

//free(message);

/////////////////////////////////////
// TCP RECV
ret=recv(sockfd, recv_buf, sizeof(recv_buf), 0);
if(ret!=SOCKET_ERROR && ret!=0)
{
char *ch;

char version[10];
int response_code;
char reason[1024];

recv_buf[ret]='\0';
ch=strstr(recv_buf, "\r\n\r\n")+4;

*response=(char *)malloc(ret);
if(ch!=(char *)0)
{
if(ch<recv_buf+ret) {
memcpy(*response, ch, ret-(ch-recv_buf));
(*response)[ret-(ch-recv_buf)]='\0';
}
}
close(sockfd);
//return ret-(ch-recv_buf);

sscanf(recv_buf, "%s %d %s[^\n]",version, 10, &response_code, reason, 1024);
return response_code;
}
else
{
return 0;
//return 400;
}

}*/

int HTTP_GET(char **response, char *address, unsigned int port, char *path, char xmlstr[], int len)
{
	int ret;
	int sockfd;

	char recv_buf[5192 * 2] = { 0, };
	char message[2048] = { 0, };

	if (address == (char *)0) return 0;

	//response[0]='\0';

	if (xmlstr == (char *)0) len = 0;
	else if (len == 0) len = strlen_s(xmlstr);
#ifdef WIN32
	sprintf_s(message, http_get_message, path, address, len);
	if (len>0) strcat_s(message, xmlstr);
#else
	if (len > 0)
	{
		char tmmp[2048] = { 0, };
		sprintf_s(tmmp, http_get_message, path, address, len);
		sprintf_s(message, "%s%s", tmmp, xmlstr);
	}
	else
	{
		sprintf_s(message, http_get_message, path, address, len);
	}
#endif



	/////////////////////////////////////
	// TCP CONNECT
	sockfd = TCP_Connect(address, port);
	if (sockfd<0)
	{
		return 0;
	}

	/////////////////////////////////////
	// TCP SEND
	ret = TCP_Send(sockfd, message);
	if (ret<0)
	{
		printf("[%s:%d] TCP_Send has failed\n", __FILE__, __LINE__);
		return 0;
	}

	//free(message);

	/////////////////////////////////////
	// TCP RECV

	ret = recv(sockfd, recv_buf, sizeof(recv_buf), 0);
	if (ret != SOCKET_ERROR && ret != 0)
	{
		char *ch;

		//char version[10];
		//		int response_code;
		//		char reason[1024];

		recv_buf[ret] = '\0';
		ch = strstr(recv_buf, "\r\n\r\n") + 4;

		*response = (char *)malloc(ret);
		if (ch != (char *)0)
		{
			if (ch<recv_buf + ret) {
				cpymem(*response, ch, ret - (ch - recv_buf));
				(*response)[ret - (ch - recv_buf)] = '\0';
			}
		}
		close(sockfd);
		return ret - (ch - recv_buf);

		// following code should be removed(2-line)
		//sscanf(recv_buf, "%s %d %s[^\n]",version, &response_code, reason);
		//return response_code;
	}
	else
	{
		return 0;
		//return 400;
	}

}


//TODO: input으로 들어오는 xmlstr이 NULL일 경우에 대해서도 처리가능하도록 수정 요망
/*
int HTTP_PUT(char **response, char *address, unsigned int port, char *path, char xmlstr[], int len)
{
int ret;
int sockfd;

char recv_buf[5192];
char message[2048];

if(address==(char *)0) return 0;

//response[0]='\0';

if(xmlstr==(char *)0) len=0;
else if(len==0) len=strlen(xmlstr);

sprintf(message, http_put_message, path, address, len);
if(len>0) strcat(message, xmlstr);


/////////////////////////////////////
// TCP CONNECT
sockfd=TCP_Connect(address, port);
if(sockfd<0)
{
return 0;
}

/////////////////////////////////////
// TCP SEND
ret=TCP_Send(sockfd, message);
if(ret<0)
{
printf("[%s:%d] TCP_Send has failed\n", __FILE__, __LINE__);
return 0;
}

//free(message);

/////////////////////////////////////
// TCP RECV
ret=recv(sockfd, recv_buf, sizeof(recv_buf), 0);
if(ret!=SOCKET_ERROR && ret!=0)
{
char *ch;

char version[10];
int response_code;
char reason[1024];

recv_buf[ret]='\0';
ch=strstr(recv_buf, "\r\n\r\n")+4;

*response=(char *)malloc(ret);
if(ch!=(char *)0)
{
if(ch<recv_buf+ret) {
memcpy(*response, ch, ret-(ch-recv_buf));
(*response)[ret-(ch-recv_buf)]='\0';
}
}
close(sockfd);
puts(recv_buf);
return ret-(ch-recv_buf);

// following code should be removed(2-line)
sscanf(recv_buf, "%s %d %s[^\n]",version, &response_code, reason);
return response_code;
}
else
{
return 0;
//return 400;
}

}

int HTTP_POST(char **response, char *address, unsigned int port, char *path, char xmlstr[], int len)
{
int ret;
int sockfd;

char recv_buf[5192];
char message[2048];

if(address==(char *)0) return 0;

//response[0]='\0';

if(xmlstr==(char *)0) len=0;
else if(len==0) len=strlen(xmlstr);

sprintf(message, http_post_message, path, address, len);
if(len>0) strcat(message, xmlstr);


/////////////////////////////////////
// TCP CONNECT
sockfd=TCP_Connect(address, port);
if(sockfd<0)
{
return 0;
}

/////////////////////////////////////
// TCP SEND
ret=TCP_Send(sockfd, message);
if(ret<0)
{
printf("[%s:%d] TCP_Send has failed\n", __FILE__, __LINE__);
return 0;
}

//free(message);

/////////////////////////////////////
// TCP RECV
ret=recv(sockfd, recv_buf, sizeof(recv_buf), 0);
if(ret!=SOCKET_ERROR && ret!=0)
{
char *ch;

char version[10];
int response_code;
char reason[1024];

recv_buf[ret]='\0';
ch=strstr(recv_buf, "\r\n\r\n")+4;

*response=(char *)malloc(ret);
if(ch!=(char *)0)
{
if(ch<recv_buf+ret) {
memcpy(*response, ch, ret-(ch-recv_buf));
(*response)[ret-(ch-recv_buf)]='\0';
}
}
close(sockfd);
puts(recv_buf);
return ret-(ch-recv_buf);

// following code should be removed(2-line)
sscanf(recv_buf, "%s %d %s[^\n]",version, &response_code, reason);
return response_code;
}
else
{
return 0;
//return 400;
}

}


int HTTP_TrackerPUT(char *address, unsigned int port, char *path, char xmlstr[], int len)
{
int ret;
int sockfd;
char message[2048];
char  recv_buf[5192];

if(address==(char *)0) return 0;

if(xmlstr==(char *)0) len=0;
else if(len==0) len=strlen(xmlstr);

sprintf(message, http_put_message, path, address, len);
if(len>0) strcat(message, xmlstr);

/////////////////////////////////////
// TCP CONNECT
sockfd=TCP_Connect(address, port);
if(sockfd<0)
{
return 0;
}

/////////////////////////////////////
// TCP SEND
ret=TCP_Send(sockfd, message);
if(ret<0)
{
return 0;
}


/////////////////////////////////////
// TCP RECV
ret=recv(sockfd, recv_buf, sizeof(recv_buf), 0);
if(ret!=SOCKET_ERROR && ret!=0)
{
char version[10];
int response_code;
char reason[128];
recv_buf[ret]='\0';
puts(recv_buf);
sscanf(recv_buf, "%s %d %s[^\n]",version, 10, &response_code, reason, 128);

return response_code;
}
else
{
return 0;
}
}


int HTTP_TrackerDELETE(char *address, unsigned int port, char *path, char xmlstr[], int len)
{
int ret;
int sockfd;
char message[2048];
char  recv_buf[5192];

if(address==(char *)0) return 0;

if(xmlstr==(char *)0) len=0;
else if(len==0) len=strlen(xmlstr);

sprintf(message, http_delete_message, path, address, len);
if(len>0) strcat(message, xmlstr);

/////////////////////////////////////
// TCP CONNECT
sockfd=TCP_Connect(address, port);
if(sockfd<0)
{
return 0;
}

/////////////////////////////////////
// TCP SEND
ret=TCP_Send(sockfd, message);
if(ret<0)
{
return 0;
}

/////////////////////////////////////
// TCP RECV
ret=recv(sockfd, recv_buf, sizeof(recv_buf), 0);
if(ret!=SOCKET_ERROR && ret!=0)
{
char version[10];
int response_code;
char reason[128];
recv_buf[ret]='\0';
puts(recv_buf);
sscanf(recv_buf, "%s %d %s[^\n]",version, 10, &response_code, reason, 128);
return response_code;

}
else
{
return 0;
}
}
*/
int TCP_Connect(const char dest_ip[], unsigned short dest_port)
{
	int sockfd = 0;
	struct sockaddr_in servaddr;

	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if (sockfd < 0)
	{
		perror("Create sock Error");
		return -1;
	}

	memset(&servaddr, 0, sizeof(struct sockaddr_in));
	servaddr.sin_family = AF_INET;
	servaddr.sin_addr.s_addr = inet_addr(dest_ip);
	servaddr.sin_port = htons(dest_port);

	long arg = 0;

	// Set non-blocking 
#ifdef WIN32
	ULONG nonBlk = TRUE;

	if (ioctlsocket(sockfd, FIONBIO, &nonBlk) < 0)
	{
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("ioctlsocket Error");
		return -1;
	}
#else
	if ((arg = fcntl(sockfd, F_GETFL, NULL)) < 0) {
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("fcntl sock Error");
		return -1;
	}
	arg |= O_NONBLOCK;
	if (fcntl(sockfd, F_SETFL, arg) < 0) {
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("fcntl sock Error");
		return -1;
	}
#endif

	int res = connect(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr));

#ifdef WIN32
	if (res == SOCKET_ERROR && WSAGetLastError() != WSAEWOULDBLOCK)
	{
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("connect Error");
		return -1;
	}

	fd_set fdset;
	FD_ZERO(&fdset);
	FD_SET(sockfd, &fdset);

	struct  timeval     timevalue;
	timevalue.tv_sec = 1;
	timevalue.tv_usec = 0;

	if (select(0, NULL, &fdset, NULL, &timevalue) < 0)
	{
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("connect Error");
		return -1;
	}

	if (!FD_ISSET(sockfd, &fdset))
	{
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("connect Error");
		return -1;
	}

	nonBlk = FALSE;
	if (ioctlsocket(sockfd, FIONBIO, &nonBlk) < 0)
	{
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("ioctlsocket Error");
		return -1;
	}
#else
	if (res < 0) {
		if (errno == EINPROGRESS) {
			fd_set myset;
			struct timeval tv;
			socklen_t lon;
			int valopt;
			do {
				tv.tv_sec = 1;
				tv.tv_usec = 0;
				FD_ZERO(&myset);
				FD_SET(sockfd, &myset);
				res = select(sockfd + 1, NULL, &myset, NULL, &tv);
				if (res < 0 && errno != EINTR) {
					shutdown(sockfd, 0x02);
					close(sockfd);
					perror("connect Error");
					return -1;
				}
				else if (res > 0) {
					// Socket selected for write 
					lon = sizeof(int);
					if (getsockopt(sockfd, SOL_SOCKET, SO_ERROR, (void*)(&valopt), &lon) < 0) {
						shutdown(sockfd, 0x02);
						close(sockfd);
						perror("getsockopt Error");
						return -1;
					}
					// Check the value returned... 
					if (valopt) {
						shutdown(sockfd, 0x02);
						close(sockfd);
						perror("connect Error");
						return -1;
					}
					break;
				}
				else {
					shutdown(sockfd, 0x02);
					close(sockfd);
					//perror("connect timeout Error");
					return -1;
				}
			} while (1);
		}
		else {
			shutdown(sockfd, 0x02);
			close(sockfd);
			perror("connect Error");
			return -1;
		}
	}
	// Set to blocking mode again... 
	if ((arg = fcntl(sockfd, F_GETFL, NULL)) < 0) {
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("fcntl sock Error");
		return -1;
	}
	arg &= (~O_NONBLOCK);
	if (fcntl(sockfd, F_SETFL, arg) < 0) {
		shutdown(sockfd, 0x02);
		close(sockfd);
		perror("fcntl sock Error");
		return -1;
	}
#endif

	return sockfd;
}


int TCP_Send(int sockfd, char stream[])
{
	int ret;
	ret = send(sockfd, stream, strlen_s(stream), 0);
	if (ret > 0)
	{
		//printf("TCP_Send: success\n");
	}
	return ret;
}


//TODO: Length를 반영해줘야 함.. 그냥 MD5돌려서 사이즈 끊어주는게 나을꺼 가틈
/*int genRandomString(char dest[], int seed, int length)
{

srand((unsigned)(time(NULL)+seed));
sprintf(dest, "%d", rand());

return 1;

}
*/
/*int genRandomStringWithPrefix(char *prefix, char dest[], int seed, int length)
{

srand((unsigned)(time(NULL)+seed));
sprintf(dest, "%s%d", prefix, rand());

return 1;

}*/



pthread_t PTHREAD_CREATE(void *(*start) (void *), void *param)
{
	pthread_t tid;
	pthread_attr_t attr;

	if (pthread_attr_init(&attr) <0) return 0;
	if (pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_DETACHED) != 0)
	{
		pthread_attr_destroy(&attr);
		return 0;
	}
	if (pthread_create(&tid, &attr, start, param) != 0)
	{
		pthread_attr_destroy(&attr);
		return 0;
	}
	return tid;
}



int check_endian(void)
{
	int i = 0x00000001;
	if (((char *)&i)[0])
		return LITTLE_ENDIAN;
	else
		return BIG_ENDIAN;
}

short align2LittleEndianS(short digit)
{
	if (check_endian() == BIG_ENDIAN)
	{
		return htons(digit);
	}
	else return digit;
}

int align2LittleEndianI(int digit)
{
	if (check_endian() == BIG_ENDIAN)
	{
		return htonl(digit);
	}
	else return digit;
}

int align2MyEndianS(short digit)
{
	if (check_endian() == BIG_ENDIAN)
	{
		return ntohs(digit);
	}
	else return digit;
}

int align2MyEndianI(int digit)
{
	if (check_endian() == BIG_ENDIAN)
	{
		return ntohl(digit);
	}
	else return digit;
}




int strGet_NIC_address(char GetIPArray[])
{
#ifdef WIN32
	struct in_addr ip;
	struct in_addr **ppip;
	struct hostent *pHost;
	char strHostName[81], *pIP;

	pIP = (char *)0;

	if (gethostname(strHostName, 80) == 0)
	{
		pHost = gethostbyname(strHostName);
		if (pHost->h_addrtype == AF_INET)
		{
			ppip = (struct in_addr **)pHost->h_addr_list;

			//Enumarate all addresses
			while (*ppip)
			{
				ip = **ppip;
				pIP = inet_ntoa(ip);
				ppip++;
				if (pIP != (char *)0 && *pIP != (char)0)
				{
					if (!strcmp(pIP, "127.0.0.1")) continue;

					cpymem(GetIPArray, pIP, 24);
					return 1;
					break;
				}
			}
		}
	}
#else
	struct ifaddrs * ifAddrStruct = NULL;
	struct ifaddrs * ifa = NULL;
	void * tmpAddrPtr = NULL;

	getifaddrs(&ifAddrStruct);

	for (ifa = ifAddrStruct; ifa != NULL; ifa = ifa->ifa_next) {
		if (!ifa->ifa_addr) {
			continue;
		}
		if (ifa->ifa_addr->sa_family == AF_INET) { // check it is IP4
			// is a valid IP4 Address
			tmpAddrPtr = &((struct sockaddr_in *)ifa->ifa_addr)->sin_addr;
			char addressBuffer[INET_ADDRSTRLEN] = { 0, };
			inet_ntop(AF_INET, tmpAddrPtr, addressBuffer, INET_ADDRSTRLEN);

			if (!strcmp(addressBuffer, "127.0.0.1")) continue;
			if (ifa->ifa_name[0] == 'l') continue;

			cpymem(GetIPArray, addressBuffer, 24);
			return 1;
			break;
			//printf("%s IP Address %s\n", ifa->ifa_name, addressBuffer);
		}
		// 		else if (ifa->ifa_addr->sa_family == AF_INET6) { // check it is IP6
		// 			// is a valid IP6 Address
		// 			tmpAddrPtr = &((struct sockaddr_in6 *)ifa->ifa_addr)->sin6_addr;
		// 			char addressBuffer[INET6_ADDRSTRLEN];
		// 			inet_ntop(AF_INET6, tmpAddrPtr, addressBuffer, INET6_ADDRSTRLEN);
		// 			printf("%s IP Address %s\n", ifa->ifa_name, addressBuffer);
		// 		}
	}
	if (ifAddrStruct != NULL) freeifaddrs(ifAddrStruct);
#endif
	return 0;
}

char* GetStringValue(char* src)
{
	if (src == NULL)
	{
		return "";
	}

	return _strdup(src);
}

void LogPrint(int level, const char *format, ...)
{
	va_list arglist;
	//	int buffing;
	//int retval;

	static int isFirst = TRUE;
	static int isSimulFirst = TRUE;
	FILE *fp = 0;
	char filename[20];

	if (SimulationLogPrint && level == LOG_SIMULATION)
	{
		sprintf_s(filename, "%s", "simulationLog.log");

		if (isSimulFirst)
		{
			isFirst = TRUE;
			isSimulFirst = FALSE;
		}
	}
	else if (LogPrintfLevel <= level)
	{
		sprintf_s(filename, "%s", "agent.log");
	}
	else return;

	
	if (level != LOG_SIMULATION)
	{
		va_start(arglist, format);
#ifdef WIN32
		char szBuf[4096];

		vsprintf(szBuf, format, arglist);
		OutputDebugStringA(szBuf);
		printf(szBuf);
#else
		vprintf(format, arglist);
#endif
		va_end(arglist);
	}
	
	va_start(arglist, format);
	if (isFirst)
	{
		isFirst = FALSE;
		fp = fopen(filename, "w+");
	}
	else
	{
		fp = fopen(filename, "a");
	}

	if (fp)
	{
		vfprintf(fp, format, arglist);
		//fwrite(szBuf, strlen(szBuf), 1, fp);
		//fwrite("\n", strlen("\n"), 1, fp);

		fclose(fp);
	}

	va_end(arglist);
	fflush(stdout);
}

void SLEEP(unsigned long ulMilliseconds)
{
#ifdef WIN32
	Sleep(ulMilliseconds);
#else
	usleep(ulMilliseconds * 1000);
#endif
}

double GetNTPTimestamp()
{
	double rslt = 0;

	if (NTPTime <= 0)
	{
		if (UseNTPTimestamp)
		{
			//char *hostname = (char *)"200.20.186.76";
			struct hostent *h = gethostbyname("1.kr.pool.ntp.org");

			if (h == 0)
			{
				perror("hostbyname");
				return -1;
			}

			//char *hostname = (char *)"211.233.78.116";
			int portno = 123;
			int i;
			unsigned char msg[48] = { 010, 0, 0, 0, 0, 0, 0, 0, 0 };
			unsigned int  buf[1024] = { 0, };
			struct protoent *proto;
			struct sockaddr_in server_addr;
			int s;

			proto = getprotobyname("udp");
			s = socket(PF_INET, SOCK_DGRAM, proto->p_proto);

			if (s <= 0)
			{
				perror("socket");
				return -1;
			}

			memset(&server_addr, 0, sizeof(server_addr));
			server_addr.sin_family = AF_INET;
			//server_addr.sin_addr.s_addr = inet_addr(hostname);
			cpymem(&server_addr.sin_addr, h->h_addr_list[0], h->h_length);
			server_addr.sin_port = htons(portno);
			i = sendto(s, (char*)msg, sizeof(msg), 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
			if (i <= 0)
			{
				shutdown(s, 0x02);
				close(s);
				perror("sendto");
				return -1;
			}

			struct sockaddr saddr;
			int saddr_l = sizeof(saddr);
#ifdef WIN32
			i = recvfrom(s, (char*)buf, 48, 0, &saddr, &saddr_l);
#else
			i = recvfrom(s, (char*)buf, 48, 0, &saddr, (socklen_t *)&saddr_l);
#endif
			if (i <= 0)
			{
				shutdown(s, 0x02);
				close(s);
				perror("recvfr:");
				return -1;
			}
			/*
#ifdef MACOS
			NTPTime = ntohl((time_t)buf[4]);
#else
			NTPTime = ntohl((time_t)buf[10]);
#endif
			*/
			NTPTime = ntohl((time_t)buf[10]);
			NTPTime -= 2208988800U;

			struct timeval tv;
			gettimeofday(&tv, 0);

			NTPTime = NTPTime * 1000.0 + tv.tv_usec / 1000.0;

			shutdown(s, 0x02);
			close(s);
		}
		else
		{
			NTPTime = GetCurMilli();
		}
		
		StartTimeval = GetCurMilli();

		rslt = NTPTime;
	}
	else
	{
		rslt = NTPTime + (GetCurMilli() - StartTimeval);
	}

	return rslt;
}

char* GetTimeString(double timeva)
{
	struct tm* pTime;
	time_t ti = timeva;

	if (timeva <= 0)
	{
		ti = time(NULL);
	}

#ifdef WIN32
	pTime = new struct tm;
	localtime_s(pTime, &ti);
#else
	pTime = localtime(&ti);
#endif // WIN32


	char *rslt = new char[50];
	//ctime_s(aa, 100, &cur_time);

	strftime(rslt, 50, "%Y-%m-%d %H:%M:%S", pTime);
#ifdef WIN32
	delete pTime;
#endif // WIN32
	return rslt;
}
/*
void SetPAMInfo(char *url, int intervalMilli)
{

}*/
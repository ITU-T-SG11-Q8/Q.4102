#pragma once

#ifdef WIN32
#include <winsock.h>
#define close(x)			closesocket(x)
#define sscanf				sscanf_s

#pragma comment (lib, "ws2_32.lib")

#else

#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <unistd.h>

typedef int SOCKET;
#define INVALID_SOCKET  (SOCKET)(~0)
#define SOCKET_ERROR            (-1)

#endif
#include <string>
#include <string.h>

#define HTTP_SUCCESS 200
#define HTTP_CERT_FAIL 401
#define HTTP_NOTFOUND 404
#define HTTP_AUTH_FAIL 406
#define HTTP_FAIL 500

//using namespace std;

class HttpREST
{
public:
	HttpREST();
	~HttpREST();

	static std::string Get(std::string url, std::string content, int *resCode);
	static std::string Put(std::string url, std::string content, int *resCode);
	static std::string Post(std::string url, std::string content, int *resCode);
	static std::string Delete(std::string url, std::string content, int *resCode);
	static void IPPortFromURL(std::string url, std::string* ip, int *port, std::string* path);


private:
	static SOCKET Connect(std::string ip, int port);
	static int Send(SOCKET sock, const char* msg);
	static std::string GetConnectSendResponse(std::string ip, int port, char* header, std::string path, std::string content, int *resCode);
};
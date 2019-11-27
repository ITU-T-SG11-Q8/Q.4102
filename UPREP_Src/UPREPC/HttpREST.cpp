#include "HttpREST.h"
#include <sstream>
#include <string>
#include "Util.h"

#define HTTP_GET_MESSAGE "GET %s HTTP/1.0\r\nHost: %s\r\nAccept: text/html\r\nUser-Agent: prep-agent\r\nContent-Length: %d\r\n\r\n"
#define HTTP_PUT_MESSAGE "PUT %s HTTP/1.0\r\nHost: %s\r\nAccept: text/html\r\nUser-Agent: prep-agent\r\nContent-Length: %d\r\n\r\n"
#define HTTP_POST_MESSAGE "POST %s HTTP/1.0\r\nHost: %s\r\nAccept: text/html\r\nUser-Agent: prep-agent\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: %d\r\n\r\n"
#define HTTP_DELETE_MESSAGE "DELETE %s HTTP/1.0\r\nHost: %s\r\nAccept: text/html\r\nUser-Agent: prep-agent\r\nContent-Length: %d\r\n\r\n"

HttpREST::HttpREST()
{
}


HttpREST::~HttpREST()
{
}

SOCKET HttpREST::Connect(std::string ip, int port)
{
	SOCKET sockfd = -1;
	struct sockaddr_in servaddr;

	sockfd = socket(AF_INET, SOCK_STREAM, 0);
	if (sockfd < 0)
	{
		perror("Error");
		return -1;
	}

	memset(&servaddr, 0, sizeof(struct sockaddr_in));
	servaddr.sin_family = AF_INET;
	servaddr.sin_addr.s_addr = inet_addr(ip.c_str());
	servaddr.sin_port = htons(port);

	if (connect(sockfd, (struct sockaddr *)&servaddr, sizeof(servaddr)) < 0)
	{
		shutdown(sockfd, 0x02);
		close(sockfd);
		return -1;
	}

	return sockfd;
}

int HttpREST::Send(SOCKET sock, const char* msg)
{
	int ret = 0, size = 0;

	int len = strlen_s(msg);

	int bufsize = 1024;

	while (len >= size)
	{
		ret = send(sock, msg + size, len - size > bufsize ? bufsize : len - size, 0);

		if (ret <= 0)
		{
			break;
		}
		size += ret;
	}
	
	return size;
}

std::string HttpREST::GetConnectSendResponse(std::string ip, int port, char* header, std::string path, std::string content, int *resCode)
{
	int sock = Connect(ip, port);

	if (sock > 0)
	{
		char htmp[2048] = { 0 };

		sprintf_s(htmp, header, path.c_str(), ip.c_str(), content.length());

		std::stringstream ss;

		ss << htmp;

		//char *message = new char[strlen(header)+content.length()];

		if (content.length() > 0)
		{
			ss << content;
			//strcat(message, content.c_str());
		}

		int ret = Send(sock, ss.str().c_str());

		if (ret < 0)
		{
			shutdown(sock, 0x02);
			close(sock);
			return "";
		}

		char recv_buf[5192 * 2] = { 0, };

		ret = recv(sock, recv_buf, sizeof(recv_buf), 0);
		if (ret != SOCKET_ERROR && ret != 0)
		{
			char *ch;

			recv_buf[ret] = '\0';
			ch = strstr(recv_buf, "\r\n\r\n") + 4;

			char *response = new char[ret];
			memset(response, 0, ret);
			if (ch != (char *)0)
			{
				if (ch < recv_buf + ret) {
					cpymem(response, ch, ret - (ch - recv_buf));
					response[ret - (ch - recv_buf)] = '\0';
				}
			}
			shutdown(sock, 0x02);
			close(sock);
			/*
			char version[10];
			char reason[128];
#ifdef WIN32
			sscanf_s(recv_buf, "%s %d %s[^\n]", version, 10, resCode, reason, 128);
#else
			sscanf_s(recv_buf, "%s %d %s[^\n]", version, resCode, reason);
#endif
			*/

			std::stringstream ss(recv_buf);
			std::string ver = "";

			ss >> ver >> *resCode;			

			std::string rslt = response;

			delete[] response;

			return rslt;
		}
		else
		{
			shutdown(sock, 0x02);
			close(sock);
		}
	}
	else
	{
		*resCode = HTTP_FAIL;
	}

	return "";
}
void HttpREST::IPPortFromURL(std::string url, std::string* ip, int *port, std::string* path)
{
	if (url.length() <= 0)
	{
		return;
	}

	std::string tmp = url;

	if ((int)tmp.find("http://") >= 0)
	{
		tmp.replace(0, 7, "");
	}

	if ((int)tmp.find("https://") >= 0)
	{
		tmp.replace(0, 8, "");
	}

	int idx = tmp.find(":");

	if (idx > 0)
	{
		*ip = tmp.substr(0, idx);
		tmp.replace(0, idx + 1, "");

		idx = tmp.find("/");

		if (idx > 0)
		{
			*port = stoi(tmp.substr(0, idx));
			tmp.replace(0, idx, "");
			*path = tmp;
		}
	}
	else
	{
		*port = 80;

		idx = tmp.find("/");

		if (idx > 0)
		{
			*ip = tmp.substr(0, idx);
			tmp.replace(0, idx, "");
			*path = tmp;
		}
	}
}

std::string HttpREST::Get(std::string url, std::string content, int* resCode)
{
	std::string ip = "", path = "";
	int port = 0;

	IPPortFromURL(url, &ip, &port, &path);

	std::string resp = GetConnectSendResponse(ip, port, HTTP_GET_MESSAGE, path, content, resCode);
	
	return resp;
}

std::string HttpREST::Put(std::string url, std::string content, int* resCode)
{
	std::string ip = "", path = "";
	int port = 0;

	IPPortFromURL(url, &ip, &port, &path);

	std::string resp = GetConnectSendResponse(ip, port, HTTP_PUT_MESSAGE, path, content, resCode);

	return resp;
}

std::string HttpREST::Post(std::string url, std::string content, int* resCode)
{
	std::string ip = "", path = "";
	int port = 0;

	IPPortFromURL(url, &ip, &port, &path);

	std::string resp = GetConnectSendResponse(ip, port, HTTP_POST_MESSAGE, path, content, resCode);

	return resp;
}

std::string HttpREST::Delete(std::string url, std::string content, int* resCode)
{
	std::string ip = "", path = "";
	int port = 0;

	IPPortFromURL(url, &ip, &port, &path);

	std::string resp = GetConnectSendResponse(ip, port, HTTP_DELETE_MESSAGE, path, content, resCode);

	return resp;
}
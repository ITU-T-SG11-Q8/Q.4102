#pragma once
#include <string>

using namespace std;

class Peer
{
public:
	string PeerID;
	string IpAddress;
	int Port;
	bool IsPublic;

	Peer()
	{
		PeerID = "";
		IpAddress = "";
		Port = 0;
		IsPublic = false;
	}

	~Peer()
	{

	}
};
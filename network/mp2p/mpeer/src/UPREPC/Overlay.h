#pragma once
#include <string>
#include "HttpREST.h"
#include <list>
#include "bson/bsonobjbuilder.h"
#include "bson/json.h"
#include "bson/bsonobjiterator.h"
#include "Protocol/JsonKey.h"
#include "Protocol/Peer.h"
#include "NetworkUtil.h"

using namespace _bson;
using namespace std;

#define AUTH_CLOSED_YES "yes"
#define AUTH_CLOSED_NO "no"
#define AUTH_CLOSED_AUTH "auth"

void* ExpireThreadMain(void* arg);

std::string AddDoubleQuote(std::string val)
{
	return "\"" + val + "\"";
}

class Overlay
{
public:
	string OverlayID;
	string URL;
	int Expires;
	int IsPAMEnabled;
	string AuthClosed;
	string AuthKey;
	list<string> AuthPeers;
	int Version;
	
	string PeerID;
	string PeerIp;
	int PeerPort;
	bool IsPublic;

	string PAMSURL;
	int PAMInterval;

	list<Peer> JoinPeers;

	Overlay()
	{
		PeerID = "";
		URL = "";
		OverlayID = "";
		Expires = 0;
		IsPAMEnabled = 0;
		AuthClosed = AUTH_CLOSED_NO;
		AuthKey = "";
		PeerIp = "";
		PeerPort = 0;
		IsPublic = false;

		PAMInterval = 0;
		PAMSURL = "";
	}
	~Overlay()
	{
		Stop = true;
		while (ExpireThread != 0)
		{
			SLEEP(100);
		}
	}
	
	int Create()
	{
		if (URL.length() <= 0)
		{
			return 0;
		}

		bsonobjbuilder bson;
		bson.append(AddDoubleQuote(JSON_KEY_OWNER_ID), PeerID);
		bson.append(AddDoubleQuote(JSON_KEY_EXPIRES), Expires);
		bson.append(AddDoubleQuote(JSON_KEY_PAM_ENABLED), IsPAMEnabled > 0);
		bsonobjbuilder auth;
		auth.append(AddDoubleQuote(JSON_KEY_CLOSED), AuthClosed);
		if (AuthClosed == AUTH_CLOSED_AUTH)
		{
			auth.append(AddDoubleQuote(JSON_KEY_AUTH_KEY), AuthKey);
		}
		bson.append(AddDoubleQuote(JSON_KEY_AUTH), auth.obj());
		if (AuthClosed == AUTH_CLOSED_YES)
		{
			bsonobjbuilder users;
			for (auto it = AuthPeers.begin(); it != AuthPeers.end(); ++it)
			{
				users.append(AddDoubleQuote(""), (*it));
			}
			bson.appendArray(AddDoubleQuote(JSON_KEY_USERS), users.obj());
		}

		string content = bson.obj().toString();

		int resCode = 0;
		string rslt = HttpREST::Post(URL, content, &resCode);

		if (resCode == HTTP_SUCCESS)
		{
			bsonobjbuilder b;
			stringstream st(rslt);
			bsonobj rsltjson = fromjson(st, b);

			string aaaa = rsltjson.toString();

			Version = rsltjson[JSON_KEY_VERSION].Int();
			OverlayID = rsltjson[JSON_KEY_OVERLAY_NETWORK_ID].String();

			ExpireThreadStart();
		}
		
		return resCode;
	}

	int Update()
	{
		if (URL.length() <= 0)
		{
			return 0;
		}

		if (OverlayID.length() <= 0)
		{
			return 0;
		}

		string url = URL + "/" + OverlayID + "/peer/" + PeerID;

		bsonobjbuilder bson;

		bsonobjbuilder peer;
		peer.append(AddDoubleQuote(JSON_KEY_PEER_ID), PeerID);

		bsonobjbuilder net;
		net.append(AddDoubleQuote(JSON_KEY_IP_ADDRESS), PeerIp);
		net.append(AddDoubleQuote(JSON_KEY_PORT), PeerPort);
		net.append(AddDoubleQuote(JSON_KEY_PUBLIC), IsPublic);

		peer.append(AddDoubleQuote(JSON_KEY_NETWORK), net.obj());

		bson.append(AddDoubleQuote(JSON_KEY_PEER), peer.obj());

		if (AuthClosed == AUTH_CLOSED_AUTH)
		{
			bsonobjbuilder auth;
			auth.append(AddDoubleQuote(JSON_KEY_AUTH_KEY), AuthKey);

			bson.append(AddDoubleQuote(JSON_KEY_AUTH), auth.obj());
		}

		string content = bson.obj().toString();

		int resCode = 0;
		string rslt = HttpREST::Put(url, content, &resCode);

		if (resCode == HTTP_SUCCESS)
		{
			bsonobjbuilder b;
			stringstream st(rslt);
			bsonobj rsltjson = fromjson(st, b);

			if (rsltjson.hasElement(JSON_KEY_EXPIRES))
			{
				Expires = rsltjson[JSON_KEY_EXPIRES].Int();
			}
		}

		return resCode;
	}
	
	int Delete()
	{
		if (URL.length() <= 0)
		{
			return 0;
		}

		if (OverlayID.length() <= 0)
		{
			return 0;
		}

		string url = URL + "/" + OverlayID;
		int resCode = 0;

		HttpREST::Delete(url, "", &resCode);

		Stop = true;

		return resCode;
	}

	int Join()
	{
		if (URL.length() <= 0)
		{
			return 0;
		}

		if (OverlayID.length() <= 0)
		{
			return 0;
		}

		string url = URL + "/" + OverlayID + "/peer";

		bsonobjbuilder bson;

		bsonobjbuilder peer;
		peer.append(AddDoubleQuote(JSON_KEY_PEER_ID), PeerID);

		bsonobjbuilder net;
		net.append(AddDoubleQuote(JSON_KEY_IP_ADDRESS), PeerIp);
		net.append(AddDoubleQuote(JSON_KEY_PORT), PeerPort);
		net.append(AddDoubleQuote(JSON_KEY_PUBLIC), IsPublic);

		peer.append(AddDoubleQuote(JSON_KEY_NETWORK), net.obj());
		
		bson.append(AddDoubleQuote(JSON_KEY_PEER), peer.obj());

		if (AuthClosed == AUTH_CLOSED_AUTH)
		{
			bsonobjbuilder auth;
			auth.append(AddDoubleQuote(JSON_KEY_AUTH_KEY), AuthKey);

			bson.append(AddDoubleQuote(JSON_KEY_AUTH), auth.obj());
		}

		string content = bson.obj().toString();

		int resCode = 0;
		string rslt = HttpREST::Post(url, content, &resCode);

		if (resCode == HTTP_SUCCESS)
		{
			ExpireThreadStart();

			bsonobjbuilder b;
			stringstream st(rslt);
			bsonobj rsltjson = fromjson(st, b);

			Version = rsltjson[JSON_KEY_VERSION].Int();
			Expires = rsltjson[JSON_KEY_EXPIRES].Int();

			if (rsltjson.hasElement(JSON_KEY_PAM_CONF))
			{
				bsonobj pamobj = rsltjson[JSON_KEY_PAM_CONF].object();

				string fff = pamobj.toString();
				bool pamena = pamobj[JSON_KEY_PAM_ENABLED].Bool();

				if (pamena)
				{
					IsPAMEnabled = 1;
					PAMSURL = pamobj[JSON_KEY_PAMS_URL].String();
					PAMInterval = pamobj[JSON_KEY_PAM_INTERVAL].Int();
				}
				else
				{
					IsPAMEnabled = 0;
				}
			}
			
			bsonobj plist = rsltjson[JSON_KEY_PEERLIST].object();

			bsonobjiterator bit(plist);

			JoinPeers.clear();
			while (1)
			{
				bsonelement e = bit.next(true);

				if (e.eoo()) break;

				bsonobj eobj = e.object();
				bsonobj peerobj = eobj[JSON_KEY_PEER].object();

				string aaaa = peerobj.toString();

				Peer peer;
				peer.PeerID = peerobj[JSON_KEY_PEER_ID].String();

				bsonobj netobj = peerobj[JSON_KEY_NETWORK].object();
				peer.IpAddress = netobj[JSON_KEY_IP_ADDRESS].String();
				peer.Port = netobj[JSON_KEY_PORT].Int();
				peer.IsPublic = netobj[JSON_KEY_PUBLIC].boolean();

				JoinPeers.push_back(peer);
			}

		}

		return resCode;
	}

	bool Stop = false;

	pthread_t ExpireThread = 0;

private:

	void ExpireThreadStart()
	{
		if (Expires > 0)
		{
			if (ExpireThread == 0)
				ExpireThread = PTHREAD_CREATE(ExpireThreadMain, this);
		}
	}
};

void CleanupExpireThread(void *arg)
{
	Overlay *overlay = (Overlay *)arg;

	overlay->ExpireThread = 0;
}

void* ExpireThreadMain(void* arg)
{
	Overlay *overlay = (Overlay *)arg;

	pthread_cleanup_push(CleanupExpireThread, overlay);
	pthread_setcancelstate(PTHREAD_CANCEL_ENABLE, NULL);
	pthread_setcanceltype(PTHREAD_CANCEL_ASYNCHRONOUS, NULL);

	int Expires = overlay->Expires;
	int gap = Expires - (Expires / 10);

	int sec = 0;

	while (!overlay->Stop)
	{
		SLEEP(1000);
		sec++;

		if (overlay->Stop) break;
		
		if (sec >= gap)
		{
			sec = 0;

			int res = overlay->Update();

			if (res == HTTP_SUCCESS && Expires != overlay->Expires)
			{
				Expires = overlay->Expires;
				gap = Expires - (Expires / 10);
			}
		}
	}

	pthread_exit(NULL);

	pthread_cleanup_pop(0);

	return 0;
}
#include <stdio.h>
#include <string>
#include "Overlay.h"
#include "NetworkUtil.h"
#include "prepAgentManager.h"
#include "Util.h"
#include <signal.h>


using namespace std;

int main(int argc, char* argv[]);

void _usage(void)
{
	fprintf(stderr, "Usage:\n");
	fprintf(stderr, "  -p, --peer id\t\tpeer id.\n");
	fprintf(stderr, "  -i, --input streaming listen\t\t[ip:]port to listen to. MUST set for IPv4\n");
	fprintf(stderr, "  -o, --output streaming listen\t\t[ip:]port to listen to. MUST set for IPv4\n");
	fprintf(stderr, "  -l, --listen\t\t[ip:]port to listen to. MUST set for IPv4\n");
	fprintf(stderr, "  -v, --overlay network id\t\toverlay network id\n");
	fprintf(stderr, "  -s, --overlay server\t\turl of the overlay server\n");
	fprintf(stderr, "  -k, --piece size\t\tpiece size (KB)\n");
	fprintf(stderr, "  -f, --output file save\n");


	//fprintf(stderr, "  -h, --hash\t\tswarm ID of the content (root hash or public key)\n");
	//fprintf(stderr, "  -f, --file\t\tname of file to use (root hash by default)\n");
	//fprintf(stderr, "  -d, --dir\t\tname of directory to scan and seed\n");
	
	//fprintf(stderr, "  -t, --tracker\t\tip:port of the tracker\n");
	//fprintf(stderr, "  -d, --debug\t\tshow debug logs.\n");
	// 	fprintf(stderr, "  -D, --debug\t\tfile name for debugging logs (default: stdout)\n");
	// 	fprintf(stderr, "  -p, --progress\treport transfer progress\n");
	// 	fprintf(stderr, "  -g, --httpgw\t\t[ip:|host:]port to bind HTTP content gateway to (no default)\n");
	// 	fprintf(stderr, "  -s, --statsgw\t\t[ip:|host:]port to bind HTTP stats listen socket to (no default)\n");
	// 	fprintf(stderr, "  -c, --cmdgw\t\t[ip:|host:]port to bind CMD listen socket to (no default)\n");
	// 	fprintf(stderr, "  -C, --cmdgwint\tcmdgw report interval in seconds\n");
	// 	fprintf(stderr, "  -E, --perscmdgw\tmake the cmdgw persistent, the client will close when the cmd socket is closed\n");
	// 	fprintf(stderr, "  -o, --destdir\t\tdirectory for saving data (default: none)\n");
	// 	fprintf(stderr, "  -u, --uprate\t\tupload rate limit in KiB/s (default: unlimited)\n");
	// 	fprintf(stderr, "  -y, --downrate\tdownload rate limit in KiB/s (default: unlimited)\n");
	// 	fprintf(stderr, "  -w, --wait\t\tlimit running time, e.g. 1[DHMs] (default: infinite with -l, -g)\n");
	// 	fprintf(stderr, "  -H, --checkpoint\tcreate checkpoint of file when complete for fast restart\n");
	//fprintf(stderr, "  -z, --chunksize\tchunk size in bytes (default: %d)\n", SWIFT_DEFAULT_CHUNK_SIZE);
	// 	fprintf(stderr, "  -m, --printurl\tcompose URL from tracker, file and chunksize\n");
	// 	fprintf(stderr, "  -q, --quiet\t\tquiet mode: don't print general status information on stderr\n");
	// 	fprintf(stderr, "  -r, --urlfile\t\tfile to write URL to for --printurl\n");
	// 	fprintf(stderr, "  -M, --multifile\tcreate multi-file spec with given files\n");
	// 	fprintf(stderr, "  -e, --zerosdir\tdirectory with checkpointed content to serve from with zero state\n");
	// 	fprintf(stderr, "  -i, --source\t\tlive source input (URL or filename or - for stdin)\n");
	// 	fprintf(stderr, "  -k, --live\t\tperform live download, use with -t and -h\n");
	// 	fprintf(stderr, "  -1 filename-in-hex\ta win32 workaround for non UTF-16 popen\n");
	// 	fprintf(stderr, "  -2 urlfilename-in-hex\ta win32 workaround for non UTF-16 popen\n");
	// 	fprintf(stderr, "  -3 zerosdir-in-hex\ta win32 workaround for non UTF-16 popen\n");
	// 	fprintf(stderr, "  -B\tdebugging logs to stdout (win32 hack)\n");
	// 	fprintf(stderr, "  -r filename\tto save URL to\n");
	// 	fprintf(stderr, "  -T time-out\tin seconds for slow zero state connections\n");
	// 	fprintf(stderr, "  -G GTest mode\n");
	// 	fprintf(stderr, "  -K live keypair filename\n");
	// 	fprintf(stderr, "  -P live checkpoint filename\n");
	// 	fprintf(stderr, "  -S content integrity protection method\n");
	// 	fprintf(stderr, "  -a live signature algorithm\n");
	// 	fprintf(stderr, "  -W live discard window in chunks\n");
	// 	fprintf(stderr, "  -I live source address (used with ext tracker)\n");

	/*fprintf(stderr, "\nex)1.1. Start seeder with file. (Port only)\n");
	fprintf(stderr, "\tEtriPPSP.exe -f xxx.mp4 -l 20000\n");
	fprintf(stderr, "\nex)1.2. Start seeder with file. (Port only) + debug logs\n");
	fprintf(stderr, "\tEtriPPSP.exe -f xxx.mp4 -l 20000 -d\n");
	fprintf(stderr, "\nex)1.3. Start seeder with file. (IP & Port)\n");
	fprintf(stderr, "\tEtriPPSP.exe -f xxx.mp4 -l 192.168.0.2:20000\n");
	fprintf(stderr, "\nex)2.1. Start peer with tracker(Listen port).\n");
	fprintf(stderr, "\tEtriPPSP.exe -t 192.168.0.2:20000 -h e13dd7bd5c7d4f60f7c598da27cd669af6576680e13dd7bd5c7d4f60f7c598da -l 20001 -f xxx.mp4\n");
	fprintf(stderr, "\nex)2.2. Start peer with tracker(Listen port). + debug logs\n");
	fprintf(stderr, "\tEtriPPSP.exe -t 192.168.0.2:20000 -h e13dd7bd5c7d4f60f7c598da27cd669af6576680e13dd7bd5c7d4f60f7c598da -l 20001 -f xxx.mp4 -d\n");
	fprintf(stderr, "\nex)2.3. Start peer with tracker(Listen IP & port).\n");
	fprintf(stderr, "\tEtriPPSP.exe -t 192.168.0.2:20000 -h e13dd7bd5c7d4f60f7c598da27cd669af6576680e13dd7bd5c7d4f60f7c598da -l 192.168.0.3:20001 -f xxx.mp4\n");*/
}

int main(int argc, char* argv[])
{
#ifndef WIN32
	signal(SIGPIPE, SIG_IGN);
#endif

	int idx = 1;
	string inputIp = "";
	int inputPort = 0;
	string outputIp = "";
	int outputPort = 0;
	string listenIp = "";
	int listenPort = 0;
	string overlayUrl = "";
	int communicatePort = 0;

	string peerId = "";
	string overlayId = "";

	string authClosed = "";
	string authkey = "";
	string authUsers = "";
	
	int peiceSize = 0;

	int outfile = 0;

	int maxUpByte = 0;
	int maxDnByte = 0;
	int maxPeer = 0;

	int pamEnabled = 0;

	int isCS = 0;
	int isRS = 0;

	int logLevel = -1;

	int playSync = -1;
	int playSyncTime = 0;
	
	if (argc < 6)
	{
		_usage();
		exit(0);
	}

	while (argc > idx)
	{

		char* arg = argv[idx];

		if (strlen_s(arg) == 2 && arg[0] == '-')
		{
			idx++;

			switch (arg[1])
			{
			case 'i':
			{
				printf("i : %s\n", argv[idx]);
				char* semi = strchr(argv[idx], ':');
				if (semi)
				{
					*semi = 0;
					inputIp = argv[idx];
					inputPort = atoi(semi + 1);
				}
				else
				{
					inputPort = atoi(argv[idx]);
				}

				break;
			}

			case 'o':
			{
				printf("o : %s\n", argv[idx]);
				char* semi = strchr(argv[idx], ':');
				if (semi)
				{
					*semi = 0;
					outputIp = argv[idx];
					outputPort = atoi(semi + 1);
				}
				else
				{
					outputPort = atoi(argv[idx]);
				}

				break;
			}

			case 'l':
			{
				printf("l : %s\n", argv[idx]);
				char* semi = strchr(argv[idx], ':');
				if (semi)
				{
					*semi = 0;
					listenIp = argv[idx];
					listenPort = atoi(semi + 1);
				}
				else
				{
					listenPort = atoi(argv[idx]);
				}

				break;
			}

			case 's':
				printf("s : %s\n", argv[idx]);
				overlayUrl = argv[idx];

				break;

			case 'p':
				printf("p : %s\n", argv[idx]);
				peerId = argv[idx];

				break;

			case 'v':
				printf("v : %s\n", argv[idx]);
				overlayId = argv[idx];

				break;

			case 'k':
				printf("k : %s\n", argv[idx]);
				peiceSize = atoi(argv[idx]);

				break;

			case 'f':
				outfile = 1;
				idx--;

				break;

			case 'a':
				pamEnabled = 1;
				idx--;

				break;

			case 'h':
				isCS = 1;
				idx--;

				break;

			case 'r':
				isRS = 1;
				idx--;

				break;
			
			case 'c':
				printf("c : %s\n", argv[idx]);
				authClosed = argv[idx];
				
				break;

			case 'w':
				printf("w : %s\n", argv[idx]);
				authkey = argv[idx];

				break;

			case 'e':
				printf("e : %s\n", argv[idx]);
				authUsers = argv[idx];

				break;

			case 'u':
				printf("u : %s\n", argv[idx]);
				maxUpByte = atoi(argv[idx]);

				break;

			case 'd':
				printf("d : %s\n", argv[idx]);
				maxDnByte = atoi(argv[idx]);

				break;

			case 'x':
				printf("x : %s\n", argv[idx]);
				maxPeer = atoi(argv[idx]);

				break;

			case 'm':
				printf("m : %s\n", argv[idx]);
				communicatePort = atoi(argv[idx]);

				break;

			case 'D':
				printf("D : %s\n", argv[idx]);
				logLevel = atoi(argv[idx]);

				break;
			
			case 'y':
				printf("y : %s\n", argv[idx]);
				playSync = atoi(argv[idx]);

				break;

			case 't':
				printf("t : %s\n", argv[idx]);
				playSyncTime = atoi(argv[idx]);

				break;
			}

			idx++;
		}
	}

	if (overlayUrl.length() <= 0)
	{
		_usage();
		exit(0);
	}
	
	if (listenPort <= 0)
	{
		_usage();
		exit(0);
	}

	if (peiceSize <= 0)
	{
		_usage();
		exit(0);
	}

	if (inputPort <= 0 && outputPort <= 0)
	{
		_usage();
		exit(0);
	}

	if (inputPort > 0 && outputPort > 0)
	{
		_usage();
		exit(0);
	}
	/*
	if (inputPort > 0)
	{
		if (inputIp.length() <= 0)
		{
			inputIp = "127.0.0.1";
		}
	}

	if (outputPort > 0)
	{
		if (outputIp.length() <= 0)
		{
			outputIp = "127.0.0.1";
		}
	}
	*/
	HTTP_Startup();

	double aaa = GetNTPTimestamp();

	Overlay overlay;
	overlay.PeerID = peerId;
	overlay.URL = overlayUrl;

	if (authClosed.length() > 0)
		overlay.AuthClosed = authClosed;
	
	if (authClosed == AUTH_CLOSED_AUTH)
	{
		overlay.AuthKey = authkey;
	}
	else if (authClosed == AUTH_CLOSED_YES)
	{
		string token = "";
		int pos = 0;
		while ((pos = authUsers.find("|")) != std::string::npos)
		{
			token = authUsers.substr(0, pos);
			overlay.AuthPeers.push_back(token);
			authUsers.erase(0, token.length() + 1);
		}

		if (authUsers.length() > 0)
		{
			overlay.AuthPeers.push_back(authUsers);
		}
	}

	overlay.Expires = 0;
	overlay.IsPAMEnabled = pamEnabled;

	PrepAgent_Init();

	if (logLevel >= 0)
	{
		SetLogLevel(logLevel);
	}

	if (inputPort > 0)
	{
		if (overlayId.length() > 0)
		{
			overlay.Version = 1;
			overlay.OverlayID = overlayId;
		}
		else
		{
			if (overlay.Create() != HTTP_SUCCESS)
			{
				fprintf(stderr, "Failed to create overlay network!!\n");
				exit(0);
			}
		}

		overlay.IsPublic = false;

		if (listenIp.length() > 0)
		{
			overlay.PeerIp = listenIp;
		}
		else
		{
			char ip[24] = {0};
			printf("!!!!!!!!!!!!!!!!!!!!!!!!!!!\n");
			strGet_NIC_address(ip);
			printf("############################\n");
			overlay.PeerIp = ip;
		}

		string str = "$$NETWORK_IP$$";
		str.append(overlay.PeerIp);
		str.append("$$NETWORK_IP$$");
		perror(str.c_str());

		overlay.PeerPort = listenPort;

		char tmpch[30] = { 0, };

		sprintf_s(tmpch, "$$NETWORK_PORT$$%d", overlay.PeerPort);

		str = tmpch;
		str.append("$$NETWORK_PORT$$");
		perror(str.c_str());

		int resCode = overlay.Join();

		if (resCode != HTTP_SUCCESS)
		{
			if (resCode == HTTP_CERT_FAIL)
			{
				perror("$$CERT_FAIL$$");
			}
			else
			{
				perror("$$SERVER_FAIL$$");
			}

			fprintf(stderr, "Failed to join overlay network!!\n");
			exit(0);
		}

		fprintf(stderr, "create overlay network!! overlayid : %s\n", overlay.OverlayID.c_str());
		
		str = "$$OvID$$";
		str.append(overlay.OverlayID);
		str.append("$$OvID$$");

		perror(str.c_str());
		
		int rp = PrepAgent_RunPrepAgent(peerId.c_str(), inputPort, listenPort, communicatePort, overlay.OverlayID.c_str(), peiceSize * 1024, overlay.PAMInterval, overlay.PAMSURL, isCS > 0 ? PAMP_TYPE_CS : (isRS > 0 ? PAMP_TYPE_RS : PAMP_TYPE_SEEDER), overlayUrl.c_str());

		if (rp <= 0)
		{
			perror("$$CLIENT_FAIL$$");

			fprintf(stderr, "Failed to run prep agent!!  - %s\n", overlay.OverlayID.c_str());

			overlay.Delete();

			exit(0);
		}
		else
		{
			perror("$$SUCCESS$$");
		}
	}
	else if (outputPort > 0)
	{
		overlay.OverlayID = overlayId;

		overlay.IsPublic = false;
		
		if (listenIp.length() > 0)
		{
			overlay.PeerIp = listenIp;
		}
		else
		{
			char ip[24] = { 0 };
			strGet_NIC_address(ip);
			overlay.PeerIp = ip;
		}

		overlay.PeerPort = listenPort;

		string str = "$$NETWORK_IP$$";
		str.append(overlay.PeerIp);
		str.append("$$NETWORK_IP$$");
		perror(str.c_str());

		char tmpch[30] = { 0, };

		sprintf_s(tmpch, "$$NETWORK_PORT$$%d", overlay.PeerPort);

		str = tmpch;
		str.append("$$NETWORK_PORT$$");
		perror(str.c_str());

		if (authClosed == AUTH_CLOSED_AUTH)
		{
			overlay.AuthKey = authkey;
		}

		int resCode = overlay.Join();

		if (resCode != HTTP_SUCCESS)
		{
			if (resCode == HTTP_CERT_FAIL)
			{
				perror("$$CERT_FAIL$$");
			}
			else
			{
				perror("$$SERVER_FAIL$$");
			}

			fprintf(stderr, "Failed to join overlay network!!\n");
			exit(0);
		}

		if (playSync >= 0)
			PrepAgent_SetPlaySync(-1, playSyncTime, playSync);
		
		int rslt = PrepAgent_JoinChannel(peerId.c_str(), overlayUrl.c_str(), overlay.OverlayID.c_str(), listenPort, outputPort, communicatePort, peiceSize * 1024, outfile, overlay.PAMInterval, overlay.PAMSURL, isCS > 0 ? PAMP_TYPE_CS : (isRS > 0 ? PAMP_TYPE_RS : PAMP_TYPE_PEER));

		if (rslt == SUCCESS)
		{
			perror("$$SUCCESS$$");
		}
		else
		{
			perror("$$CLIENT_FAIL$$");
		}
	}
	
	while (true)
	{
		char end;
		scanf("%c", &end);

		if (end == 'Q')
		{
			break;
		}
	}

	HTTP_Cleanup();

	return 0;
}
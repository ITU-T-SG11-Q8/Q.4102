#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class Hello
{
public:
	string MessageName;
	int ProtocolVersion;
	string PeerId;
	string OverlayId;
	int ValidTime;
	int SPIndex;
	int CPLength;
	int DPIndex;
	int DSLength;
	double StartTimestamp;
	char* BufferMap;
	char* ObjectBin;

	Hello()
	{
		Init();
	}

	Hello(char* bin)
	{
		Init();

		SetBin(bin);
	}

	Hello(bsonobj bson)
	{
		Init();

		SetBson(bson);
	}

	~Hello()
	{
		if (BufferMap != 0)
		{
			delete[] BufferMap;
		}

		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_HELLO;
		PeerId = "";
		OverlayId = "";

		ProtocolVersion = 1;
		ValidTime = 4;
		SPIndex = 0;
		CPLength = 0;
		DPIndex = 0;
		DSLength = 0;
		BufferMap = 0;
		ObjectBin = 0;
		StartTimestamp = 0;
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);

		//string aaaa = bson.toString();

		MessageName = bson[JSON_KEY_METHOD].String();
		ProtocolVersion = bson[JSON_KEY_PROTOCOL_VERSION].Int();
		PeerId = bson[JSON_KEY_PEER_ID].String();
		OverlayId = bson[JSON_KEY_OVERLAY_NETWORK_ID].String();
		ValidTime = bson[JSON_KEY_VALID_TIME].Int();
		SPIndex = bson[JSON_KEY_SP_INDEX].Int();
		CPLength = bson[JSON_KEY_CP_LENGTH].Int();
		DPIndex = bson[JSON_KEY_DP_INDEX].Int();
		DSLength = bson[JSON_KEY_DS_LENGTH].Int();
		StartTimestamp = bson[JSON_KEY_TIMESTAMP].Double();

		if (DSLength > 0)
		{
			BufferMap = new char[DSLength];
			int len = 0;
			const char * buf = bson[JSON_KEY_BUFFERMAP].binData(len);
			cpymem(BufferMap, buf, len);
		}
	}

	void SetBson(bsonobj& bson)
	{
		//string aaaa = bson.toString();

		MessageName = bson[JSON_KEY_METHOD].String();
		ProtocolVersion = bson[JSON_KEY_PROTOCOL_VERSION].Int();
		PeerId = bson[JSON_KEY_PEER_ID].String();
		OverlayId = bson[JSON_KEY_OVERLAY_NETWORK_ID].String();
		ValidTime = bson[JSON_KEY_VALID_TIME].Int();
		SPIndex = bson[JSON_KEY_SP_INDEX].Int();
		CPLength = bson[JSON_KEY_CP_LENGTH].Int();
		DPIndex = bson[JSON_KEY_DP_INDEX].Int();
		DSLength = bson[JSON_KEY_DS_LENGTH].Int();
		StartTimestamp = bson[JSON_KEY_TIMESTAMP].Double();

		if (DSLength > 0)
		{
			BufferMap = new char[DSLength];
			int len = 0;
			const char * buf = bson[JSON_KEY_BUFFERMAP].binData(len);
			cpymem(BufferMap, buf, len);
		}
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		bson.append(JSON_KEY_PROTOCOL_VERSION, ProtocolVersion);
		bson.append(JSON_KEY_PEER_ID, PeerId);
		bson.append(JSON_KEY_OVERLAY_NETWORK_ID, OverlayId);
		bson.append(JSON_KEY_VALID_TIME, ValidTime);
		bson.append(JSON_KEY_SP_INDEX, SPIndex);
		bson.append(JSON_KEY_CP_LENGTH, CPLength);
		bson.append(JSON_KEY_DP_INDEX, DPIndex);
		bson.append(JSON_KEY_DS_LENGTH, DSLength);
		bson.append(JSON_KEY_TIMESTAMP, StartTimestamp);

		if (DSLength > 0)
		{
			bson.appendBinData(JSON_KEY_BUFFERMAP, DSLength, BinDataGeneral, BufferMap);
		}
		
		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
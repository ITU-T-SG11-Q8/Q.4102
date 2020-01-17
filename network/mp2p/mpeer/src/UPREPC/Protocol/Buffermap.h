#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class Buffermap
{
public:
	string MessageName;
	int PieceIndex;
	int CPLength;
	int DPIndex;
	int DSLength;
	long long TimeStamp;
	char* BuffermapBin;
	char* ObjectBin;
	
	Buffermap()
	{
		Init();
	}

	Buffermap(char* bin)
	{
		Init();

		SetBin(bin);
	}

	Buffermap(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~Buffermap()
	{
		if (BuffermapBin != 0)
		{
			delete[] BuffermapBin;
		}

		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_BUFFERMAP;
		PieceIndex = 0;
		CPLength = 0;
		DPIndex = 0;
		DSLength = 0;
		TimeStamp = 0;
		BuffermapBin = 0;
		ObjectBin = 0;
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
		CPLength = bson[JSON_KEY_CP_LENGTH].Int();
		DPIndex = bson[JSON_KEY_DP_INDEX].Int();
		DSLength = bson[JSON_KEY_DS_LENGTH].Int();
		TimeStamp = bson[JSON_KEY_TIMESTAMP].Long();

		if (DSLength > 0)
		{
			BuffermapBin = new char[DSLength];
			int len = 0;
			const char * buf = bson[JSON_KEY_BUFFERMAP].binData(len);
			cpymem(BuffermapBin, buf, len);
		}
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
		CPLength = bson[JSON_KEY_CP_LENGTH].Int();
		DPIndex = bson[JSON_KEY_DP_INDEX].Int();
		DSLength = bson[JSON_KEY_DS_LENGTH].Int();
		TimeStamp = bson[JSON_KEY_TIMESTAMP].Long();

		if (DSLength > 0)
		{
			BuffermapBin = new char[DSLength];
			int len = 0;
			const char * buf = bson[JSON_KEY_BUFFERMAP].binData(len);
			cpymem(BuffermapBin, buf, len);
		}
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		bson.append(JSON_KEY_PIECE_INDEX, PieceIndex);
		bson.append(JSON_KEY_CP_LENGTH, CPLength);
		bson.append(JSON_KEY_DP_INDEX, DPIndex);
		bson.append(JSON_KEY_DS_LENGTH, DSLength);
		bson.append(JSON_KEY_TIMESTAMP, TimeStamp);
		bson.appendBinData(JSON_KEY_BUFFERMAP, DSLength, BinDataGeneral, BuffermapBin);

		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
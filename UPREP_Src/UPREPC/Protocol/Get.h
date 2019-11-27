#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class Get
{
public:
	string MessageName;
	int PieceIndex;
	int Offset;

	char *ObjectBin;

	Get()
	{
		Init();
	}

	Get(char* bin)
	{
		Init();

		SetBin(bin);
	}

	Get(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~Get()
	{
		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_GET;
		PieceIndex = 0;
		Offset = 0;

		ObjectBin = 0;
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
		Offset = bson[JSON_KEY_OFFSET].Int();
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
		Offset = bson[JSON_KEY_OFFSET].Int();
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		bson.append(JSON_KEY_PIECE_INDEX, PieceIndex);
		bson.append(JSON_KEY_OFFSET, Offset);
				
		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
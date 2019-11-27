#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class Refresh
{
public:
	string MessageName;
	int PieceIndex;
	int PieceNumber;
	char* ObjectBin;

	Refresh()
	{
		Init();
	}

	Refresh(char* bin)
	{
		Init();

		SetBin(bin);
	}

	Refresh(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~Refresh()
	{
		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_REFRESH;
		PieceIndex = 0;
		PieceNumber = 0;

		ObjectBin = 0;
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
		PieceNumber = bson[JSON_KEY_PIECE_NUMBER].Int();
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
		PieceNumber = bson[JSON_KEY_PIECE_NUMBER].Int();
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		bson.append(JSON_KEY_PIECE_INDEX, PieceIndex);
		bson.append(JSON_KEY_PIECE_NUMBER, PieceNumber);

		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
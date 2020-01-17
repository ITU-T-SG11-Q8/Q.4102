#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class Notify
{
public:
	string MessageName;
	int PieceIndex;
	char *ObjectBin;

	Notify()
	{
		Init();
	}

	Notify(char* bin)
	{
		Init();

		SetBin(bin);
	}

	Notify(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~Notify()
	{
		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_NOTIFY;
		PieceIndex = 0;
		ObjectBin = 0;
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		bson.append(JSON_KEY_PIECE_INDEX, PieceIndex);

		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
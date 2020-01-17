#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class Busy
{
public:
	string MessageName;
	string Reason;
	char *ObjectBin;

	Busy()
	{
		Init();
	}

	Busy(char* bin)
	{
		Init();

		SetBin(bin);
	}

	Busy(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~Busy()
	{
		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_BUSY;
		Reason = "";
		ObjectBin = 0;
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
		if(bson.hasElement(JSON_KEY_REASON))
			Reason = bson[JSON_KEY_REASON].String();
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
		if (bson.hasElement(JSON_KEY_REASON))
			Reason = bson[JSON_KEY_REASON].String();
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		if (Reason.length() > 0)
		{
			bson.append(JSON_KEY_REASON, Reason);
		}
		
		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
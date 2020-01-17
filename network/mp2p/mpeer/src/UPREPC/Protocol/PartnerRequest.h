#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class PartnerRequest
{
public:
	string MessageName;
	int StartIndex;
	char *ObjectBin;

	PartnerRequest()
	{
		Init();
	}

	PartnerRequest(char* bin)
	{
		Init();

		SetBin(bin);
	}

	PartnerRequest(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~PartnerRequest()
	{
		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_PARTNER_REQUEST;
		StartIndex = 0;

		ObjectBin = 0;
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
		StartIndex = bson[JSON_KEY_START_INDEX].Int();
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
		StartIndex = bson[JSON_KEY_START_INDEX].Int();
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		bson.append(JSON_KEY_START_INDEX, StartIndex);

		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
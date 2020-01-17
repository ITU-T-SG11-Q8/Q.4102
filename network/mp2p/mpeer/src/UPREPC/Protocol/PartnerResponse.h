#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

#define PARTNER_RESPONSE_REASON_NO_MORE_PARTNER "NO_MORE_PARTNER"
#define PARTNER_RESPONSE_REASON_NO_AUTHORITY "NO_AUTHORITY"

using namespace _bson;
using namespace std;

class PartnerResponse
{
public:
	string MessageName;
	bool Result;
	string Reason;
	char *ObjectBin;

	PartnerResponse()
	{
		Init();
	}

	PartnerResponse(char* bin)
	{
		Init();

		SetBin(bin);
	}

	PartnerResponse(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~PartnerResponse()
	{
		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_PARTNER_RESPONSE;
		Result = false;
		Reason = "";
		ObjectBin = 0;
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
		Result = bson[JSON_KEY_RESULT].Bool();
		if (bson.hasElement(JSON_KEY_REASON))
			Reason = bson[JSON_KEY_REASON].String();
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
		Result = bson[JSON_KEY_RESULT].Bool();
		if(bson.hasElement(JSON_KEY_REASON))
			Reason = bson[JSON_KEY_REASON].String();
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		bson.append(JSON_KEY_RESULT, Result);
		if (!Result)
		{
			bson.append(JSON_KEY_REASON, Reason);
		}

		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
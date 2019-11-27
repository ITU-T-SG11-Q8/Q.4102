#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class Bye
{
public:
	string MessageName;
	
	char *ObjectBin;

	Bye()
	{
		Init();
	}

	Bye(char* bin)
	{
		Init();

		SetBin(bin);
	}

	Bye(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~Bye()
	{
		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_BYE;

		ObjectBin = 0;
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
	}

	const char* GetBin(int &len)
	{
		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		
		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
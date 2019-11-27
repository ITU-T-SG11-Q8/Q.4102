#pragma once
#include <string>
#include "../bson/bsonobjbuilder.h"
#include "../bson/json.h"
#include "../bson/bsonobjiterator.h"
#include "JsonKey.h"
#include "../NetworkUtil.h"
#include "../sha1.h"
#include "../Util.h"

using namespace _bson;
using namespace std;

class Data
{
public:
	string MessageName;
	int PieceIndex;
	int Offset;
	int DataSize;
	double TimeStamp;
	int HopCount;
	string Hash;
	string Signature;
	string EncryptedHash;
	char *DataBin;
	char *ObjectBin;

	Data()
	{
		Init();
	}

	Data(char* bin)
	{
		Init();

		SetBin(bin);
	}

	Data(bsonobj& bson)
	{
		Init();

		SetBson(bson);
	}

	~Data()
	{
		if (DataBin != 0)
		{
			delete[] DataBin;
		}

		if (ObjectBin != 0)
		{
			delete[] ObjectBin;
		}
	}

	void Init()
	{
		MessageName = PP_METHOD_DATA;
		PieceIndex = 0;
		Offset = 0;
		DataSize = 0;
		TimeStamp = 0;
		HopCount = 0;
		Hash = "";
		Signature = "";
		EncryptedHash = "";
		DataBin = 0;
		ObjectBin = 0;
	}

	void SetBson(bsonobj& bson)
	{
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
		Offset = bson[JSON_KEY_OFFSET].Int();
		DataSize = bson[JSON_KEY_DATA_SIZE].Int();
		TimeStamp = bson[JSON_KEY_TIMESTAMP].Double();
		HopCount = bson[JSON_KEY_HOP_COUNT].Int();

		if(bson.hasElement(JSON_KEY_HASH))
		{
			Hash = bson[JSON_KEY_HASH].String();
		}

		if (bson.hasElement(JSON_KEY_SIGNATURE))
		{
			Signature = bson[JSON_KEY_SIGNATURE].String();
		}

		if (bson.hasElement(JSON_KEY_ENCRYPTED_HASH))
		{
			EncryptedHash = bson[JSON_KEY_ENCRYPTED_HASH].String();
		}
		
		DataBin = new char[DataSize];
		int len = 0;
		const char *data = bson[JSON_KEY_DATA].binData(len);
		cpymem(DataBin, data, DataSize);
	}

	void SetBin(char* bin)
	{
		bsonobj bson(bin);
		MessageName = bson[JSON_KEY_METHOD].String();
		PieceIndex = bson[JSON_KEY_PIECE_INDEX].Int();
		Offset = bson[JSON_KEY_OFFSET].Int();
		DataSize = bson[JSON_KEY_DATA_SIZE].Int();
		TimeStamp = bson[JSON_KEY_TIMESTAMP].Double();
		HopCount = bson[JSON_KEY_HOP_COUNT].Int();
		Hash = bson[JSON_KEY_HASH].String();
		Signature = bson[JSON_KEY_SIGNATURE].String();
		EncryptedHash = bson[JSON_KEY_ENCRYPTED_HASH].String();
		DataBin = new char[DataSize];
		int len = 0;
		const char *data = bson[JSON_KEY_DATA].binData(len);
		cpymem(DataBin, data, DataSize);
	}

	const char* GetBin(int &len)
	{
		if (TimeStamp <= 0)
		{
			TimeStamp = GetNTPTimestamp();
		}

		if (DataBin != 0)
		{
			unsigned char *hashout = new unsigned char[SHA1_DIGEST_BLOCKLEN];
			SHA1_Encrypt((unsigned char*)DataBin, DataSize, hashout);
			Hash = "";
			Hash.append((char *)hashout);
			delete[] hashout;
		}

		bsonobjbuilder bson;
		bson.append(JSON_KEY_METHOD, MessageName);
		bson.append(JSON_KEY_PIECE_INDEX, PieceIndex);
		bson.append(JSON_KEY_OFFSET, Offset);
		bson.append(JSON_KEY_DATA_SIZE, DataSize);
		bson.append(JSON_KEY_TIMESTAMP, TimeStamp);
		bson.append(JSON_KEY_HOP_COUNT, HopCount);
		bson.append(JSON_KEY_HASH, Hash);
		bson.append(JSON_KEY_SIGNATURE, Signature);
		bson.append(JSON_KEY_ENCRYPTED_HASH, EncryptedHash);
		bson.appendBinData(JSON_KEY_DATA, DataSize, BinDataGeneral, DataBin);

		len = bson.obj().objsize();

		ObjectBin = new char[len];
		cpymem(ObjectBin, bson.obj().objdata(), len);

		return ObjectBin;
	}
};
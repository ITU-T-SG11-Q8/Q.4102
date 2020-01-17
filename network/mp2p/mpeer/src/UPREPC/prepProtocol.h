#ifndef __PREP_PROTOCOL_H__
#define __PREP_PROTOCOL_H__

#define PREP_PROTOCOL_HELLO			0x01		//Peer간 서로 인지하고 최초 버퍼맵을 교환하는 메시지
#define PREP_PROTOCOL_GET			0x02		//특정 piece를 요구하는 메시지
#define PREP_PROTOCOL_DATA			0x03		//GET의 응답으로, 보내고자 하는 PIECE/BLOCK 내부 data가 있는 메시지
#define PREP_PROTOCOL_BUSY			0x04		//GET의 응답으로, 요구한 PIECE를 보내 줄 수 없을 때 알려주는 메시지
#define PREP_PROTOCOL_DATACANCEL	0x05		//Peer이 PIECE를 보내주는데, 더 이상 데이터를 받고 싶지 않을 때, 보내는 메시지
#define PREP_PROTOCOL_REFRESH		0x06		//갖고 있는 최근 버퍼맵을 요청하는 메시지
#define PREP_PROTOCOL_BUFFERMAP     0x07		//REFRESH의 응답으로, 피어가 요구한 버퍼맵을 보내는 메시지
#define PREP_PROTOCOL_BYE			0x08		//피어가 서로 연결을 끊을 때 보내는 메시지
#define PREP_PROTOCOL_PARTNER		0x09		//피어가 파트너 되었으면 할 때 보내는 메시지
#define PREP_PROTOCOL_RESULT		0x0A		//PARTNER에 대한 응답 메시지로, 파트너가 되는 결과를 보내는 메시지
#define PREP_PROTOCOL_NOTIFY		0x0B		//PARTNER 상태에서 새로운 PIECE를 보내 줄 수 있다는 메시지

#define PA_ID_LEN					36 + 1		//PREP Agent(PA) ID는 각 PREP Agent를 구분하기 위한 것으로 24 octet의 크기를 가지며, 어떻게 구성될지는 아직 정해지지 않았으나, PREP기반의 program version, IP/MAC 주소 혹은 난수를 이용할 수 있다.
#define OVERLAY_ID_LEN				36 + 1		//OVERLAY ID는 각 오버레이(채널)을 구분하기 위한 것으로 24 octet의 HASH값이다. 단, 어떠한 값을 기반으로 hash값을 만들지는 아직 정하지 않았으며 채널의 이름, 스트리밍 피어의 IP/MAC 주소, 오버레이 생성 시간 등을 이용할 수 있다.

#define PREP_CLIENT_MODE			1000
//#define PREP_CLIENT_SERVER_MODE		1001
#define PREP_SERVER_MODE			1002

typedef struct _ProtocolHeader_t {
	unsigned char Type;							//메시지 종류
	unsigned char Ver;							//PREP 버전을 표시함. 2010년 버전은 1임
	unsigned char Resv;							//현재 zero(0)임. 추후 사용 가능
	unsigned int mLen;						//전체 메시지 길이를 나타냄
} ProtocolHeader_t;

typedef struct _ProtocolHello_t {
	unsigned char   pa_id[PA_ID_LEN];			//메시지를 보내는 PREP Agent ID (발신 PA)
	unsigned char   overlay_id[OVERLAY_ID_LEN];	//Overlay Identification
	unsigned int    valid_time;					//버퍼맵 정보의 유효 시간으로 단위는 초(sec)임. (0의 경우 무한대)
	unsigned int    sp_index;					//Starting Point의 Piece 번호로 현재 보유하고 있는 Piece의 시작 번호임.
	unsigned int    complete_length;			//SS+PS+CS의 합으로 현재 보유하고 있는 Piece의 총 개수
	unsigned int    dp_index;					//Download Point의 Piece 번호로 조각맵의 시작 index임
	unsigned int    ds_length;					//Download 구간의 Piece의 개수로 Download 구간의 크기임
	unsigned char   *download_map;				//Download 구간의 맵으로 크기는 DS length이고, piece가 존재하면 TRUE(1)이고 piece가 존재하지 않으면 FALSE(0)으로 표시됨
} ProtocolHello_t;

typedef struct _ProtocolGet_t {
	unsigned int	piece_index;				//요청하는 piece의 구분자
	unsigned int	offset;						//요청하는 piece 안에서 시작 block의 구분자로 특정 시작 block이 없고 전체 piece가 필요하면 offset을 0으로 하면 된다.
} ProtocolGet_t;

typedef struct _ProtocolData_t {
	unsigned int    piece_index;				//전송하는 piece의 구분자
	unsigned int	offset;						//전송하는 piece 안에서 시작 block의 구분자임
	unsigned int	size;						//보내는 DATA의 크기 (1~MAX_DATA)
	unsigned char	*data;						//실제 데이터
} ProtocolData_t;

typedef struct _ProtocolDataCancel_t {
	unsigned int	piece_index;				//요청하는 piece의 구분자
	unsigned int	reason;						//취소 원인 예) data 수신 느림
} ProtocolDataCancel_t;

typedef struct _ProtocolRefresh_t {
	unsigned int 	piece_index;				//요구자가 필요한 버퍼맵의 시작 Piece 번호. Piece index가 zero이면 상대 peer에서 보유하고 있는 buffermap에서 시작부터 보내줌
	unsigned int 	number;						//요구한 Piece 개수로 값이 zero이면 상대 peer이 갖고 있는 buffermap 끝까지 보내줌.
} ProtocolRefresh_t;

typedef struct _ProtocolBuffermap_t {
	unsigned int 	piece_index;				//REFRESH message의 piece 번호임. 만약, REFRESH에서 zero이면, 자신의 버퍼맵의 시작 (= SP index) 지점부터 보냄.
	unsigned int	complete_length;			//REFRESH message의 개수(number) 안에 있는 piece에서 모든 block을 보유하고 있는 piece의 개수 만약, REFRESH message의 개수(number) 값이 zero 이면, 자신이 보유하고 있는 버퍼맵 끝까지 보내줘야 하는데, 이때, DP index 직전까지의 piece의 개수임.
	unsigned int	dp_index;					//REFRESH message에서 요구한 piece 중에서 모든 block을 보유하고 있지 않는 경우 다운로드맵으로 보냄. Download Point의 Piece 번호로 다운로드맵의 시작 index임.
	unsigned int	ds_length;					//Download 맵의 Piece의 개수로 Download 맵의 크기임. 값은 REFRESH 메시지의 number ? complete length 임.
	unsigned char 	*download_map;				//Download 맵의 크기는 DS length이고, piece가 존재하면 TRUE(1)이고 piece가 존재하지 않으면 FALSE(0)으로 표시됨
} ProtocolBuffermap_t;

typedef struct _ProtocolPartner_t {
	unsigned int	starting_piece_index;		//Notify 받고자 하는 piece의 시작 index
} ProtocolPartner_t;
	
typedef struct _ProtocolResult_t {
	unsigned int result;						//PARTNER 요청의 결과임.
} ProtocolResult_t;

typedef struct _ProtocolNotify_t {
	unsigned int piece_index;					//새로 생성되어 파트너에게 전송할 수 있는 piece의 index
} ProtocolNotify_t;

////////////

typedef struct _Buffermap_t {
	unsigned int 	piece_index;
	unsigned int	download_map_length;
	unsigned char 	*download_map;
} Buffermap_t;
#endif

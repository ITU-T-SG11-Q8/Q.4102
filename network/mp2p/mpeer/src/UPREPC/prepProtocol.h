#ifndef __PREP_PROTOCOL_H__
#define __PREP_PROTOCOL_H__

#define PREP_PROTOCOL_HELLO			0x01		//Peer�� ���� �����ϰ� ���� ���۸��� ��ȯ�ϴ� �޽���
#define PREP_PROTOCOL_GET			0x02		//Ư�� piece�� �䱸�ϴ� �޽���
#define PREP_PROTOCOL_DATA			0x03		//GET�� ��������, �������� �ϴ� PIECE/BLOCK ���� data�� �ִ� �޽���
#define PREP_PROTOCOL_BUSY			0x04		//GET�� ��������, �䱸�� PIECE�� ���� �� �� ���� �� �˷��ִ� �޽���
#define PREP_PROTOCOL_DATACANCEL	0x05		//Peer�� PIECE�� �����ִµ�, �� �̻� �����͸� �ް� ���� ���� ��, ������ �޽���
#define PREP_PROTOCOL_REFRESH		0x06		//���� �ִ� �ֱ� ���۸��� ��û�ϴ� �޽���
#define PREP_PROTOCOL_BUFFERMAP     0x07		//REFRESH�� ��������, �Ǿ �䱸�� ���۸��� ������ �޽���
#define PREP_PROTOCOL_BYE			0x08		//�Ǿ ���� ������ ���� �� ������ �޽���
#define PREP_PROTOCOL_PARTNER		0x09		//�Ǿ ��Ʈ�� �Ǿ����� �� �� ������ �޽���
#define PREP_PROTOCOL_RESULT		0x0A		//PARTNER�� ���� ���� �޽�����, ��Ʈ�ʰ� �Ǵ� ����� ������ �޽���
#define PREP_PROTOCOL_NOTIFY		0x0B		//PARTNER ���¿��� ���ο� PIECE�� ���� �� �� �ִٴ� �޽���

#define PA_ID_LEN					36 + 1		//PREP Agent(PA) ID�� �� PREP Agent�� �����ϱ� ���� ������ 24 octet�� ũ�⸦ ������, ��� ���������� ���� �������� �ʾ�����, PREP����� program version, IP/MAC �ּ� Ȥ�� ������ �̿��� �� �ִ�.
#define OVERLAY_ID_LEN				36 + 1		//OVERLAY ID�� �� ��������(ä��)�� �����ϱ� ���� ������ 24 octet�� HASH���̴�. ��, ��� ���� ������� hash���� �������� ���� ������ �ʾ����� ä���� �̸�, ��Ʈ���� �Ǿ��� IP/MAC �ּ�, �������� ���� �ð� ���� �̿��� �� �ִ�.

#define PREP_CLIENT_MODE			1000
//#define PREP_CLIENT_SERVER_MODE		1001
#define PREP_SERVER_MODE			1002

typedef struct _ProtocolHeader_t {
	unsigned char Type;							//�޽��� ����
	unsigned char Ver;							//PREP ������ ǥ����. 2010�� ������ 1��
	unsigned char Resv;							//���� zero(0)��. ���� ��� ����
	unsigned int mLen;						//��ü �޽��� ���̸� ��Ÿ��
} ProtocolHeader_t;

typedef struct _ProtocolHello_t {
	unsigned char   pa_id[PA_ID_LEN];			//�޽����� ������ PREP Agent ID (�߽� PA)
	unsigned char   overlay_id[OVERLAY_ID_LEN];	//Overlay Identification
	unsigned int    valid_time;					//���۸� ������ ��ȿ �ð����� ������ ��(sec)��. (0�� ��� ���Ѵ�)
	unsigned int    sp_index;					//Starting Point�� Piece ��ȣ�� ���� �����ϰ� �ִ� Piece�� ���� ��ȣ��.
	unsigned int    complete_length;			//SS+PS+CS�� ������ ���� �����ϰ� �ִ� Piece�� �� ����
	unsigned int    dp_index;					//Download Point�� Piece ��ȣ�� �������� ���� index��
	unsigned int    ds_length;					//Download ������ Piece�� ������ Download ������ ũ����
	unsigned char   *download_map;				//Download ������ ������ ũ��� DS length�̰�, piece�� �����ϸ� TRUE(1)�̰� piece�� �������� ������ FALSE(0)���� ǥ�õ�
} ProtocolHello_t;

typedef struct _ProtocolGet_t {
	unsigned int	piece_index;				//��û�ϴ� piece�� ������
	unsigned int	offset;						//��û�ϴ� piece �ȿ��� ���� block�� �����ڷ� Ư�� ���� block�� ���� ��ü piece�� �ʿ��ϸ� offset�� 0���� �ϸ� �ȴ�.
} ProtocolGet_t;

typedef struct _ProtocolData_t {
	unsigned int    piece_index;				//�����ϴ� piece�� ������
	unsigned int	offset;						//�����ϴ� piece �ȿ��� ���� block�� ��������
	unsigned int	size;						//������ DATA�� ũ�� (1~MAX_DATA)
	unsigned char	*data;						//���� ������
} ProtocolData_t;

typedef struct _ProtocolDataCancel_t {
	unsigned int	piece_index;				//��û�ϴ� piece�� ������
	unsigned int	reason;						//��� ���� ��) data ���� ����
} ProtocolDataCancel_t;

typedef struct _ProtocolRefresh_t {
	unsigned int 	piece_index;				//�䱸�ڰ� �ʿ��� ���۸��� ���� Piece ��ȣ. Piece index�� zero�̸� ��� peer���� �����ϰ� �ִ� buffermap���� ���ۺ��� ������
	unsigned int 	number;						//�䱸�� Piece ������ ���� zero�̸� ��� peer�� ���� �ִ� buffermap ������ ������.
} ProtocolRefresh_t;

typedef struct _ProtocolBuffermap_t {
	unsigned int 	piece_index;				//REFRESH message�� piece ��ȣ��. ����, REFRESH���� zero�̸�, �ڽ��� ���۸��� ���� (= SP index) �������� ����.
	unsigned int	complete_length;			//REFRESH message�� ����(number) �ȿ� �ִ� piece���� ��� block�� �����ϰ� �ִ� piece�� ���� ����, REFRESH message�� ����(number) ���� zero �̸�, �ڽ��� �����ϰ� �ִ� ���۸� ������ ������� �ϴµ�, �̶�, DP index ���������� piece�� ������.
	unsigned int	dp_index;					//REFRESH message���� �䱸�� piece �߿��� ��� block�� �����ϰ� ���� �ʴ� ��� �ٿ�ε������ ����. Download Point�� Piece ��ȣ�� �ٿ�ε���� ���� index��.
	unsigned int	ds_length;					//Download ���� Piece�� ������ Download ���� ũ����. ���� REFRESH �޽����� number ? complete length ��.
	unsigned char 	*download_map;				//Download ���� ũ��� DS length�̰�, piece�� �����ϸ� TRUE(1)�̰� piece�� �������� ������ FALSE(0)���� ǥ�õ�
} ProtocolBuffermap_t;

typedef struct _ProtocolPartner_t {
	unsigned int	starting_piece_index;		//Notify �ް��� �ϴ� piece�� ���� index
} ProtocolPartner_t;
	
typedef struct _ProtocolResult_t {
	unsigned int result;						//PARTNER ��û�� �����.
} ProtocolResult_t;

typedef struct _ProtocolNotify_t {
	unsigned int piece_index;					//���� �����Ǿ� ��Ʈ�ʿ��� ������ �� �ִ� piece�� index
} ProtocolNotify_t;

////////////

typedef struct _Buffermap_t {
	unsigned int 	piece_index;
	unsigned int	download_map_length;
	unsigned char 	*download_map;
} Buffermap_t;
#endif

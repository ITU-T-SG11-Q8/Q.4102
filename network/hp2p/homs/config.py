# 서버 환경 설정
SERVER_CONFIG = {
    'HOST': '0.0.0.0',  # 서버 IP
    'PORT': 8081,  # 서버 Port
    'DEBUG': False,
    'WEB_ROOT': 'static',
    'CLEAR_DATABASE': False,  # 서버 실행시 Database 초기화 여부
    'RECOVERY_DATABASE': True,  # 서버 실행시 Database 데이터 복구 여부
    'USING_EXPIRES_SCHEDULER': True,  # 서버 Expires 체크 여부
    'EXPIRES_SCHEDULER_INTERVAL': 30  # 서버 Expires 체크 주기(초)
}
# 웹소켓 서버 환경 설정
WEB_SOCKET_CONFIG = {
    'HOST': '0.0.0.0',  # 웹소켓 서버 IP
    'PORT': 8082  # 웹소켓 서버 Port
}
# DB 환경 설정
DATABASE_CONFIG = {
    'DB_HOST': 'localhost',  # DB 접속 Host
    'DB_PORT': 3306,  # DB 접속 Port
    'DB_USER': 'root',  # DB 사용자
    'DB_PASS': 'root',  # DB 비밀번호
    'DB_DATABASE': 'hp2p'  # DB 이름
}
# 프로토콜 환경 설정
HOMS_CONFIG = {
    'INITIAL_ENTRY_POINT_POS': {  # (접속 시) 서버에서 제공하는 Peer 기준점, 상위 N% 값 제공
        5: 30,
        10: 40,
        20: 60,
        30: 80
    },
    'RECOVERY_ENTRY_POINT_POS': 20,  # (복구 시) 서버에서 제공하는 Peer 기준점, 상위 N% 값 제공
    'PEER_INFO_LIST_COUNT': 3,  # 서버에서 제공하는 목록의 Peer 수
    'OVERLAY_EXPIRES': 0,  # Overlay Expires 값(초)
    'PEER_EXPIRES': 60,  # Peer Expires 값(초)
    'REMOVE_EMPTY_OVERLAY': True
}
# LOG 출력 환경 설정
LOG_CONFIG = {
    'PRINT_PROTOCOL_LOG': True,  # Protocol Log 메시지 출력 여부
    'PRINT_WEB_SOCKET_LOG': True  # Web Socket Log 메시지 출력 여부
}

SERVER_CONFIG = {
    'HOST': '127.0.0.1',  # 서버 IP
    'PORT': 8081,  # 서버 Port
    'DEBUG': False,
    'WEB_ROOT': 'static',
    'CLEAR_DATABASE': False,  # 서버 실행시 Database 초기화 여부
    'RECOVERY_DATABASE': True,  # 서버 실행시 Database 데이터 복구 여부
    'USING_EXPIRES_SCHEDULER': True,  # 서버 Expires 체크 여부
    'EXPIRES_SCHEDULER_INTERVAL': 30  # 서버 Expires 체크 주기(초)
}

WEB_SOCKET_CONFIG = {
    'HOST': '127.0.0.1',  # 웹소켓 서버 IP
    'PORT': 8082  # 웹소켓 서버 Port
}

DATABASE_CONFIG = {  # DB 환경 설정
    'DB_HOST': 'localhost',
    'DB_PORT': 3386,
    'DB_USER': 'root',
    'DB_PASS': 'root',
    'DB_DATABASE': 'hp2p'
}

HOMS_CONFIG = {
    # (접속 시) 서버에서 제공하는 Peer 기준점, 상위 N% 값 제공
    'INITIAL_ENTRYPOINT_POS': {
        1: 10,
        10: 20,
        20: 30,
        30: 50
    },
    'RECOVERY_ENTRYPOINT_POS': 20,  # (복구 시) 서버에서 제공하는 Peer 기준점, 상위 N% 값 제공
    'PEER_INFO_LIST_COUNT': 3,  # 서버에서 제공하는 목록의 Peer 수
    'OVERLAY_EXPIRES': 0,  # Overlay Expires 값(초)
    'PEER_EXPIRES': 60  # Peer Expires 값(초)
}

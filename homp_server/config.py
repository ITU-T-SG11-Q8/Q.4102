SERVER_CONFIG = {
    'HOST': '127.0.0.1',  # 서버 IP
    'PORT': 8081,  # 서버 Port
    'DEBUG': False,
    'WEB_ROOT': 'static'
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
    'DB_DATABASE': 'hp2p',
}

HOMS_CONFIG = {
    'INITIAL_ENTRYPOINT_POS': 20,  # (접속 시) 서버에서 제공하는 Peer 기준점, 상위 N% 값 제공
    'RECOVERY_ENTRYPOINT_POS': 20,  # (복구 시) 서버에서 제공하는 Peer 기준점, 상위 N% 값 제공
    # 'APPLY_PEER_CAPA': False, 사용 안함
    'PEER_INFO_LIST_COUNT': 3,  # 서버에서 제공하는 목록의 Peer 수
    'DEFAULT_OVERLAY_EXPIRES': 0
}

# # Server
# HOST = 'localhost'
# PORT = 8081
#
# # DB
# DB_HOST = 'localhost'
# DB_PORT = 3386
# DB_USER = 'root'
# DB_PASS = 'root'
# DB_DATABASE = 'test'
#
# # Web
# WEB_ROOT = 'static'
#
# # Debug
# DEBUG = True

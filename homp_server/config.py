SERVER_CONFIG = {
    'HOST': '127.0.0.1',  # 0.0.0.0 or 127.0.0.1
    'PORT': 8081,
    'DEBUG': True,
    'WEB_ROOT': 'static'
}

WEB_SOCKET_CONFIG = {
    'HOST': '127.0.0.1',  # 0.0.0.0 or 127.0.0.1
    'PORT': 8082
}

DATABASE_CONFIG = {
    'DB_HOST': 'localhost',
    'DB_PORT': 3386,
    'DB_USER': 'root',
    'DB_PASS': 'root',
    'DB_DATABASE': 'hp2p',
}

HOMS_CONFIG = {
    'INITIAL_ENTRYPOINT_POS': 80,
    'RECOVERY_ENTRYPOINT_POS': 20,
    'APPLY_PEER_CAPA': False,
    'PEER_INFO_LIST_COUNT': 3,
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

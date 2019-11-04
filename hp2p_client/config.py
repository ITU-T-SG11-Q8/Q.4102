CLIENT_CONFIG = {
    'TCP_SERVER_IP': '127.0.0.1',  # (TCP 사용시) TCP 서버 IP
    'HOMS_URL': 'http://localhost:8081',  # HOMS 서버 URL
    'WEB_SOCKET_SERVER_IP': '127.0.0.1',  # (WebRTC 사용시) 릴레이 웹소켓 서버 IP
    'WEB_SOCKET_SERVER_PORT': 8082  # (WebRTC 사용시) 릴레이 웹소켓 서버 Port
}

PEER_CONFIG = {
    'MAX_PRIMARY_CONNECTION': 10,  # Primary 최대 연결수
    'MAX_INCOMING_CANDIDATE': 10,  # Incoming 최대 연결수
    'MAX_OUTGOING_CANDIDATE': 10,  # Outgoing 최대 연결수
    'PEER_TTL': 3,  # Hello 메시지 TTL
    'ESTAB_PEER_TIMEOUT': 5,  # ESTAB_PEER 메시지 수신 시간(초)
    'ESTAB_PEER_MAX_COUNT': 10,  # ESTAB 최대 연결수
    'PROBE_PEER_TIMEOUT': 5,  # PROBE_PEER 메시지 수신 시간(초)
    'BROADCAST_OPERATION_ACK': False,  # Broadcast 메시지 ACK
    'RELEASE_OPERATION_ACK': False,  # Release 메시지 ACK
    'PRINT_HEARTBEAT_LOG': False  # Heartbeat 메시지 출력 여부
}

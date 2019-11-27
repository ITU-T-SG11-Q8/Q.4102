GUI_CONFIG = {
    'HOST': '127.0.0.1',  # 서버 IP
    'WEB_SOCKET_HOST': '127.0.0.1',  # 웹소켓 서버 IP
    'WEB_ROOT': 'static'
}

CLIENT_CONFIG = {
    'TCP_SERVER_IP': '127.0.0.1',  # (TCP 사용시) TCP 서버 IP
    'HOMS_URL': 'http://localhost:8081',  # HOMS 서버 URL
    'WEB_SOCKET_SERVER_IP': '127.0.0.1',  # (WebRTC 사용시) 릴레이 웹소켓 서버 IP
    'WEB_SOCKET_SERVER_PORT': 8082  # (WebRTC 사용시) 릴레이 웹소켓 서버 Port
}

PEER_CONFIG = {
    'MAX_PRIMARY_CONNECTION': 5,  # Primary 최대 연결수
    'MAX_INCOMING_CANDIDATE': 5,  # Incoming 최대 연결수
    'MAX_OUTGOING_CANDIDATE': 5,  # Outgoing 최대 연결수
    'PEER_TTL': 3,  # Hello 메시지 TTL
    'ESTAB_PEER_TIMEOUT': 5,  # ESTAB_PEER 메시지 수신 시간(초)
    'ESTAB_PEER_MAX_COUNT': 5,  # ESTAB 최대 연결수
    'PROBE_PEER_TIMEOUT': 0,  # PROBE_PEER 메시지 수신 시간(초), 0초면 PROBE_PEER 를 스킵한다.

    'SEND_CANDIDATE': False,  # CANDIDATE 메시지 전송 여부
    'BROADCAST_OPERATION_ACK': False,  # Broadcast 메시지 ACK
    'RELEASE_OPERATION_ACK': False,  # Release 메시지 ACK

    'CHECKED_PRIMARY_INTERVAL': 30,  # PRIMARY 연결 상태 확인 시간((ESTAB_PEER_TIMEOUT + PROBE_PEER_TIMEOUT) * 1.2 이상)
    'PRINT_REPORT_LOG': False,  # Report Log 메시지 출력 여부
    'PRINT_HEARTBEAT_LOG': False,  # Heartbeat Log 메시지 출력 여부
    'PRINT_REFRESH_LOG': False,  # Refresh Log 메시지 출력 여부
    'PRINT_CHECKED_PRIMARY_LOG': False,  # Primary 확인 및 복구 Log 메시지 출력 여부
    'PRINT_SCAN_TREE_LOG': False,  # ScanTree 확인 및 복구 Log 메시지 출력 여부
    'PRINT_UPREP_LOG': False  # uPREP Log 메시지 출력 여부

    # 'USING_RETRY_OVERLAY_JOIN': True,  # 네트워크 참가 재시도
    # 'RETRY_OVERLAY_JOIN_INTERVAL': 30,  # 네트워크 참가 재시도 interval
}

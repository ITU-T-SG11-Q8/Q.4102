# UI 웹서버 환경 설정
GUI_CONFIG = {
    'HOST': '0.0.0.0',  # 서버 IP
    'WEB_SOCKET_HOST': '0.0.0.0',  # 웹소켓 서버 IP
    'WEB_ROOT': 'static'
}
# PEER 통신 환경 설정
CLIENT_CONFIG = {
    'TCP_SERVER_IP': '127.0.0.1',  # (TCP 사용시) TCP 서버 IP
    #'HOMS_URL': 'http://localhost:8081',  # HOMS 서버 URL
    'HOMS_URL': 'http://192.168.100.166:9081',  # HOMS 서버 URL
    'WEB_SOCKET_SERVER_IP': '127.0.0.1',  # (WebRTC 사용시) 릴레이 웹소켓 서버 IP
    'WEB_SOCKET_SERVER_PORT': 8082  # (WebRTC 사용시) 릴레이 웹소켓 서버 Port
}
# PEER 프로토콜 환경 설정
PEER_CONFIG = {
    'MAX_PRIMARY_CONNECTION': 5,  # Primary 최대 연결수(Incoming 와 Outgoing 보다 큰수, (Incoming + Outgoing) * 0.8 이상)
    'MAX_INCOMING_CANDIDATE': 3,  # Incoming 최대 연결수
    'MAX_OUTGOING_CANDIDATE': 3,  # Outgoing 최대 연결수
    'PEER_TTL': 5,  # Hello 메시지 TTL
    'ESTAB_PEER_TIMEOUT': 3,  # ESTAB_PEER 메시지 수신 시간(초) - RTC 인 경우 Connection 을 위한 시간을 고려하여 결정
    'ESTAB_PEER_MAX_COUNT': 3,  # ESTAB 최대 연결수
    'PROBE_PEER_TIMEOUT': 3,  # PROBE_PEER 메시지 수신 시간(초), 0초면 PROBE_PEER 를 스킵한다.

    'SEND_CANDIDATE': False,  # CANDIDATE 메시지 전송 여부
    'BROADCAST_OPERATION_ACK': False,  # Broadcast 메시지 ACK
    'RELEASE_OPERATION_ACK': False,  # Release 메시지 ACK

    'CHECKED_PRIMARY_INTERVAL': 30,  # PRIMARY 연결 상태 확인 시간((ESTAB_PEER_TIMEOUT + PROBE_PEER_TIMEOUT) * 1.5 이상)
    'RETRY_OVERLAY_JOIN': True,  # 네트워크 참가(Hello) 재시도 여부
    'RETRY_OVERLAY_JOIN_COUNT': 3,  # 네트워크 참가(Hello) 재시도 수
    'RETRY_OVERLAY_JOIN_INTERVAL': 5,  # 네트워크 참가(Hello) 재시도 Interval
    'RETRY_OVERLAY_RECOVERY_INTERVAL': 10,  # 네트워크 복구(Hello-Recovery) 재시도 Interval

    'PRINT_REPORT_LOG': False,  # Report Log 메시지 출력 여부
    'PRINT_HEARTBEAT_LOG': False,  # Heartbeat Log 메시지 출력 여부
    'PRINT_REFRESH_LOG': False,  # Refresh Log 메시지 출력 여부
    'PRINT_CHECKED_PRIMARY_LOG': False,  # Primary 확인 및 복구 Log 메시지 출력 여부
    'PRINT_SCAN_TREE_LOG': False,  # ScanTree 확인 및 복구 Log 메시지 출력 여부
    'PRINT_UPREP_LOG': False  # uPREP Log 메시지 출력 여부
}

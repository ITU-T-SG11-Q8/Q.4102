class Peer:
    def __init__(self):
        self.isJoinOverlay = False
        self.isOwner = False

        self.peer_id = None
        self.overlay_id = None
        self.ticket_id = -1

        self.title = None
        self.description = None
        self.overlay_expires = 0
        self.type = 'core'
        self.sub_type = 'tree'
        self.auth_type = 'open'
        self.admin_key = None
        self.auth_keyword = None
        self.auth_access_key = None
        self.auth_peerlist = []
        self.heartbeat_interval = 30
        self.heartbeat_timeout = 60
        self.auth_password = None
        self.peer_expires = 3600

        self.mode = None
        self.use_tcp_server = None

        self.tcp_server_ip = None
        self.tcp_server_port = None

        self.web_socket_server_ip = None
        self.web_socket_server_port = None

    def get_address(self):
        if self.use_tcp_server is None:
            return None
        elif self.use_tcp_server:
            return 'tcp://{0}:{1}'.format(self.tcp_server_ip, self.tcp_server_port)
        else:
            return 'ws://{0}:{1}'.format(self.web_socket_server_ip, self.web_socket_server_port)

    def set_tcp_server_info(self, ip, port):
        self.use_tcp_server = True
        self.tcp_server_ip = ip
        self.tcp_server_port = port

    def set_web_socket_server_info(self, ip, port):
        self.use_tcp_server = False
        self.web_socket_server_ip = ip
        self.web_socket_server_port = port

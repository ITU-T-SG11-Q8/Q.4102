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
        self.peer_expires = 60
        self.scan_tree_sequence = None

        self.is_tcp = None
        self.is_auto = True

        self.tcp_server_ip = None
        self.tcp_server_port = None

        self.web_socket_server_ip = None
        self.web_socket_server_port = None
        self.is_top_peer = False

        self.using_web_gui = False
        self.gui_web_socket_port = None
        self.gui_server_port = None
        self.has_udp_connection = False

        self.public_data_port = None

    def get_address(self):
        if self.is_tcp is None:
            return None
        elif self.is_tcp:
            return 'tcp://{0}:{1}'.format(self.tcp_server_ip, self.tcp_server_port)
        else:
            return 'ws://{0}:{1}'.format(self.web_socket_server_ip, self.web_socket_server_port)

    def set_tcp_server_info(self, ip, port):
        self.is_tcp = True
        self.tcp_server_ip = ip
        self.tcp_server_port = port

    def set_web_socket_server_info(self, ip, port):
        self.is_tcp = False
        self.web_socket_server_ip = ip
        self.web_socket_server_port = port

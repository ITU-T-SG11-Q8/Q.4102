from classes.peer import Peer
from classes.singleton_instance import SingletonInstance
from config import PEER_CONFIG


class Factory(SingletonInstance):
    def __init__(self):
        self._peer = Peer()
        self._homp_handler = None
        self._tcp_server = None
        self._peer_manager = None
        # self._tcp_message_handler = None
        self._client_scheduler = None
        self._rtc_hp2p_client = None
        self._mode = None
        self._web_socket_message_handler = None
        self._udp_socket_client = None
        self._uprep_address = None
        self._public_data_listener = None
        # self._client = None

    # def get_client(self):
    #     return self._client
    #
    # def set_client(self, client):
    #     self._client = client

    def get_public_data_listener(self):
        return self._public_data_listener

    def set_public_data_listener(self, public_data_listener):
        if self._public_data_listener is None:
            self._public_data_listener = public_data_listener

    def get_tcp_server(self):
        return self._tcp_server

    def set_tcp_server(self, tcp_server):
        if self._mode is None and self._tcp_server is None:
            self._tcp_server = tcp_server
            self._mode = 1

    def get_peer_manager(self):
        return self._peer_manager

    def set_peer_manager(self, peer_manager):
        if self._peer_manager is None:
            self._peer_manager = peer_manager

    def get_peer(self):
        return self._peer

    def get_homp_handler(self):
        return self._homp_handler

    def set_homp_handler(self, handle):
        if self._homp_handler is None:
            self._homp_handler = handle

    # def get_tcp_message_handler(self):
    #     return self._tcp_message_handler
    #
    # def set_tcp_message_handler(self, tcp_message_handler):
    #     if self._tcp_message_handler is None:
    #         self._tcp_message_handler = tcp_message_handler

    def get_client_scheduler(self):
        return self._client_scheduler

    def set_client_scheduler(self, scheduler):
        if self._client_scheduler is None:
            self._client_scheduler = scheduler

    def get_rtc_hp2p_client(self):
        return self._rtc_hp2p_client

    def set_rtc_hp2p_client(self, rtc_hp2p_client):
        self._rtc_hp2p_client = rtc_hp2p_client
        self._mode = 2

    def is_used_tcp(self):
        return self._mode == 1

    def is_used_rtc(self):
        return self._mode == 2

    # def set_mode(self, mode):
    #     self._mode = mode

    def get_web_socket_handler(self):
        return self._web_socket_message_handler

    def set_web_socket_handler(self, handler):
        self._web_socket_message_handler = handler

    def set_udp_socket_client(self, udp_socket_client, uprep_ip, uprep_port):
        self._udp_socket_client = udp_socket_client
        self._uprep_address = (uprep_ip, uprep_port)

    def sendto_udp_socket(self, message):
        try:
            if self._udp_socket_client is not None and self._uprep_address is not None:
                self._udp_socket_client.sendto(message.encode(), self._uprep_address)
                if PEER_CONFIG['PRINT_UPREP_LOG']:
                    print('[uPREP] Send Data.', message)
        except:
            if PEER_CONFIG['PRINT_UPREP_LOG']:
                print('[uPREP] Failed Send Data')

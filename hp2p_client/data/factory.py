from classes.peer import Peer
from classes.singleton_instance import SingletonInstance
from homp.homp_message_handler import HompMessageHandler


class Factory(SingletonInstance):
    def __init__(self):
        self._peer = Peer()
        self._homp_handler = HompMessageHandler()
        self._tcp_server = None
        self._peer_manager = None
        self._tcp_message_handler = None
        self._heartbeat_scheduler = None
        self._rtc_hp2p_client = None
        self._mode = None

    def get_tcp_server(self):
        return self._tcp_server

    def set_tcp_server(self, tcp_server):
        self._tcp_server = tcp_server
        self._mode = 1

    def get_peer_manager(self):
        return self._peer_manager

    def set_peer_manager(self, peer_manager):
        self._peer_manager = peer_manager

    def get_peer(self):
        return self._peer

    def get_homp_handler(self):
        return self._homp_handler

    def get_tcp_message_handler(self):
        return self._tcp_message_handler

    def set_tcp_message_handler(self, tcp_message_handler):
        self._tcp_message_handler = tcp_message_handler

    def get_heartbeat_scheduler(self):
        return self._heartbeat_scheduler

    def set_heartbeat_scheduler(self, scheduler):
        self._heartbeat_scheduler = scheduler

    def get_rtc_hp2p_client(self):
        return self._rtc_hp2p_client

    def set_rtc_hp2p_client(self, rtc_hp2p_client):
        self._rtc_hp2p_client = rtc_hp2p_client
        self._mode = 2

    def is_used_tcp(self):
        return self._mode == 1

    def set_mode(self, mode):
        self._mode = mode

from classes.peer import Peer
from classes.singleton_instance import SingletonInstance
from handler.homp_handler import HompMessageHandler


class Factory(SingletonInstance):
    def __init__(self):
        self._peer = Peer()
        self._homp_handler = HompMessageHandler()
        self._tcp_server = None
        self._peer_manager = None
        self._tcp_message_handler = None
        self._heartbeat_scheduler = None
        self._rtc_connection = None
        self._mode = None

    def get_tcp_server(self):
        return self._tcp_server

    def set_tcp_server(self, tcp_server):
        self._tcp_server = tcp_server

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

    def get_rtc_connection(self):
        return self._rtc_connection

    def set_rtc_connection(self, rtc_connection):
        self._rtc_connection = rtc_connection
        self._mode = 2

    def is_used_tcp(self):
        return self._mode == 1

    def set_mode(self, mode):
        self._mode = mode
